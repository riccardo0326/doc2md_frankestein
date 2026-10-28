from __future__ import annotations

import hashlib
import importlib.metadata
import json
from collections.abc import Callable
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Literal

from ...cache import DiskCache, anydoc_cache_key, page_cache_key
from ...config import Config
from ...errors import (
    ConfigError,
    ConversionFailed,
    OptionalDependencyError,
    PageExtractionError,
    SourceError,
)
from ...metrics import MetricsCollector
from ...models import (
    Block,
    ConversionResult,
    ConvertedDocument,
    Method,
    PageResult,
    PageStat,
    Provenance,
    RouteDecision,
    SourceInfo,
    ToolInfo,
)
from ...render.markdown import render_markdown
from ...render.sidecar import write_document, write_run
from .router import classify
from .signals import compute_signals
from .source import PdfSource

FastExtractor = Any
FallbackExtractor = Callable[[int, Any], list[Block]]
HardExtractor = Callable[[int, Any, RouteDecision], list[Block]]
VisionExtractor = Callable[[int, Any], list[Block]]
PagePdfFactory = Callable[[Path, int], bytes]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _version(package: str, fallback: str = "not-installed") -> str:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return fallback


def _config_hash(config: Config) -> str:
    payload = json.dumps(config.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _slice_page(source: Path, page_number: int) -> bytes:
    try:
        from pypdf import PdfReader, PdfWriter
    except ModuleNotFoundError as exc:
        raise OptionalDependencyError(
            "The page bridge requires pypdf; install the 'anydoc' extra"
        ) from exc
    try:
        reader = PdfReader(str(source), strict=False)
        writer = PdfWriter()
        writer.add_page(reader.pages[page_number - 1])
        output = BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception as exc:
        raise PageExtractionError(f"Unable to slice original page {page_number}: {exc}") from exc


def _normalize_block(block: Block, page: int, source: Method) -> Block:
    return block.model_copy(
        update={
            "block_id": f"p{page:04d}-b001",
            "provenance": Provenance(page=page, source=source),
        }
    )


class PdfConverter:
    """Dependency-injected tiered PDF loop; not a default pipeline policy."""

    def __init__(
        self,
        *,
        fast_extractor: FastExtractor | None = None,
        hard_extractor: HardExtractor | None = None,
        vision_extractor: VisionExtractor | None = None,
        fallback_extractor: FallbackExtractor | None = None,
        page_pdf_factory: PagePdfFactory | None = None,
    ) -> None:
        self.fast_extractor = fast_extractor
        self.hard_extractor = hard_extractor
        self.vision_extractor = vision_extractor
        self.fallback_extractor = fallback_extractor
        self.page_pdf_factory = page_pdf_factory or _slice_page

    def _fast(self) -> FastExtractor:
        if self.fast_extractor is None:
            from .anydoc import AnyDocFastExtractor

            self.fast_extractor = AnyDocFastExtractor()
        return self.fast_extractor

    def _blocks_from_fallback(self, page_number: int, page: Any) -> list[Block]:
        if self.fallback_extractor is None:
            raise PageExtractionError("pdfplumber emergency fallback is not configured")
        return self.fallback_extractor(page_number, page)

    def convert(
        self,
        source: str | Path,
        out_dir: str | Path | None = None,
        *,
        config: Config | None = None,
        pages: tuple[int, ...] | None = None,
        strict: bool = False,
        no_cache: bool = False,
        pipeline: Literal["tiered", "full-vision", "docling-only"] = "tiered",
    ) -> ConversionResult:
        if pipeline not in {"tiered", "full-vision", "docling-only"}:
            raise ConfigError(f"unknown pipeline: {pipeline}")
        source_path = Path(source)
        if not source_path.is_file():
            raise SourceError(f"source does not exist: {source_path}")
        effective_config = config or Config()
        source_hash = _sha256(source_path)
        config_digest = _config_hash(effective_config)
        cache = DiskCache(
            effective_config.cache.dir,
            source_hash,
            enabled=effective_config.cache.enabled and not no_cache,
        )
        metrics = MetricsCollector()
        with PdfSource(source_path) as pdf:
            page_count = pdf.page_count
            selected = set(range(1, page_count + 1)) if pages is None else set(pages)
            if not selected or any(page < 1 or page > page_count for page in selected):
                raise ValueError("pages must contain valid 1-based page numbers")
            page_results, page_stats, warnings = self._process_pages(
                pdf,
                source_path,
                selected,
                effective_config,
                source_hash,
                cache,
                metrics,
                pipeline,
            )

        failed_count = sum(result.status == "failed" for result in page_results)
        if strict and failed_count:
            raise ConversionFailed(f"{failed_count} page(s) failed")

        source_info = SourceInfo(
            name=source_path.name,
            sha256=source_hash,
            size_bytes=source_path.stat().st_size,
            page_count=page_count,
        )
        tool = ToolInfo(
            doc2md="0.1.0",
            pdfplumber=_version("pdfplumber"),
            anydoc=_version("firecrawl-anydoc"),
            backend=effective_config.fast.backend,
            config_hash=config_digest,
        )
        document = ConvertedDocument(
            source=source_info,
            pipeline=pipeline,
            pages=page_results,
            tool=tool,
        )
        markdown = render_markdown(
            document,
            page_markers=effective_config.render.page_markers,
            block_anchors=effective_config.render.block_anchors,
        )
        epoch = datetime.fromtimestamp(0, tz=timezone.utc)
        for warning in cache.warnings:
            metrics.add_warning(warning)
        stats = metrics.snapshot(
            run_id=source_hash[:16],
            started_at=epoch,
            finished_at=epoch,
            pipeline="tiered",
            source=source_info,
            config_hash=config_digest,
        )

        markdown_path: Path | None = None
        json_path: Path | None = None
        run_path: Path | None = None
        if out_dir is not None:
            destination = Path(out_dir) / source_path.stem
            destination.mkdir(parents=True, exist_ok=True)
            markdown_path = destination / f"{source_path.stem}.md"
            json_path = destination / f"{source_path.stem}.json"
            run_path = destination / "run.json"
            markdown_path.write_text(markdown, encoding="utf-8", newline="\n")
            write_document(json_path, document)
            write_run(run_path, stats)

        return ConversionResult(
            document=document,
            markdown=markdown,
            markdown_path=markdown_path,
            json_path=json_path,
            run_path=run_path,
            stats=stats,
        )

    def _process_pages(
        self,
        pdf: PdfSource,
        source_path: Path,
        selected: set[int],
        config: Config,
        source_hash: str,
        cache: DiskCache,
        metrics: MetricsCollector,
        pipeline: Literal["tiered", "full-vision", "docling-only"],
    ) -> tuple[list[PageResult], list[PageStat], list[str]]:
        page_results: list[PageResult] = []
        page_stats: list[PageStat] = []
        warnings: list[str] = []
        for page_number, page in pdf:
            decision = classify(
                compute_signals(page, config.router),
                config.router,
                page=page_number,
            )
            if page_number not in selected:
                result = PageResult(
                    page=page_number,
                    status="skipped",
                    page_class=decision.page_class,
                    method=None,
                    warnings=["page_not_selected"],
                    duration_s=0.0,
                )
            elif pipeline == "full-vision":
                vision_key = page_cache_key(
                    source_hash, page_number, "vision", config.vision.model_dump()
                )
                cached = cache.get("vision", vision_key)
                if cached is not None:
                    blocks = [Block.model_validate(item) for item in cached.get("blocks", [])]
                    result = PageResult(
                        page=page_number,
                        status="ok",
                        page_class=decision.page_class,
                        method="vision",
                        blocks=blocks,
                        warnings=["cache_hit:vision"],
                        duration_s=0.0,
                    )
                    metrics.record_cache(hit=True)
                else:
                    metrics.record_cache(hit=False)
                    result = self._convert_vision_page(page_number, page, decision)
                    if result.status == "ok":
                        cache.put(
                            "vision",
                            vision_key,
                            {"blocks": [block.model_dump(mode="json") for block in result.blocks]},
                        )
            elif pipeline == "docling-only" or decision.page_class != "TEXT":
                hard_backend = "docling" if pipeline == "docling-only" else "hard"
                hard_key = page_cache_key(
                    source_hash, page_number, hard_backend, config.hard.model_dump()
                )
                cached = cache.get(hard_backend, hard_key)
                if cached is not None:
                    blocks = [Block.model_validate(item) for item in cached.get("blocks", [])]
                    result = PageResult(
                        page=page_number,
                        status="ok",
                        page_class=decision.page_class,
                        method=blocks[0].provenance.source if blocks else None,
                        blocks=blocks,
                        warnings=[f"cache_hit:{hard_backend}"],
                        duration_s=0.0,
                    )
                    metrics.record_cache(hit=True)
                else:
                    metrics.record_cache(hit=False)
                    result = self._convert_hard_page(page_number, page, decision)
                    if result.status == "ok":
                        cache.put(
                            hard_backend,
                            hard_key,
                            {"blocks": [block.model_dump(mode="json") for block in result.blocks]},
                        )
                    drain_calls = getattr(self.hard_extractor, "drain_calls", None)
                    if callable(drain_calls):
                        for call_id, call_result in drain_calls():
                            metrics.record_call("transcribe_page", call_id, call_result)
            else:
                result = self._convert_text_page(
                    source_path,
                    page_number,
                    page,
                    decision,
                    config,
                    warnings,
                    source_hash,
                    cache,
                    metrics,
                )
            page_results.append(result)
            page_stats.append(
                PageStat(
                    page=page_number,
                    status=result.status,
                    page_class=result.page_class,
                    method=result.method,
                    duration_s=0.0,
                    reasons=decision.reasons,
                )
            )
            metrics.record_page(page_stats[-1])
        return page_results, page_stats, warnings

    def _convert_vision_page(
        self, page_number: int, page: Any, decision: RouteDecision
    ) -> PageResult:
        if self.vision_extractor is None:
            return PageResult(
                page=page_number,
                status="failed",
                page_class=decision.page_class,
                method=None,
                error="full-vision renderer is not configured",
                warnings=["pipeline:full-vision"],
                duration_s=0.0,
            )
        try:
            blocks = self.vision_extractor(page_number, page)
            return PageResult(
                page=page_number,
                status="ok",
                page_class=decision.page_class,
                method="vision",
                blocks=blocks,
                warnings=["pipeline:full-vision", "images:disabled"],
                duration_s=0.0,
            )
        except Exception as exc:
            return PageResult(
                page=page_number,
                status="failed",
                page_class=decision.page_class,
                method=None,
                error=f"{type(exc).__name__}: {exc}",
                warnings=["pipeline:full-vision"],
                duration_s=0.0,
            )

    def _convert_hard_page(
        self, page_number: int, page: Any, decision: RouteDecision
    ) -> PageResult:
        warning = f"routed_to_hard_path:{','.join(decision.reasons) or decision.page_class}"
        if self.hard_extractor is None:
            return PageResult(
                page=page_number,
                status="failed",
                page_class=decision.page_class,
                method=None,
                warnings=[warning],
                error="hard path is not configured",
                duration_s=0.0,
            )
        try:
            blocks = self.hard_extractor(page_number, page, decision)
            return PageResult(
                page=page_number,
                status="ok",
                page_class=decision.page_class,
                method=blocks[0].provenance.source if blocks else None,
                blocks=blocks,
                warnings=[warning],
                duration_s=0.0,
            )
        except Exception as exc:
            return PageResult(
                page=page_number,
                status="failed",
                page_class=decision.page_class,
                method=None,
                warnings=[warning],
                error=f"{type(exc).__name__}: {exc}",
                duration_s=0.0,
            )

    def _convert_text_page(
        self,
        source_path: Path,
        page_number: int,
        page: Any,
        decision: RouteDecision,
        config: Config,
        warnings: list[str],
        source_hash: str,
        cache: DiskCache,
        metrics: MetricsCollector,
    ) -> PageResult:
        if config.fast.backend == "pdfplumber":
            try:
                blocks = self._blocks_from_fallback(page_number, page)
                return PageResult(
                    page=page_number,
                    status="ok",
                    page_class=decision.page_class,
                    method="pdfplumber",
                    blocks=blocks,
                    warnings=["configured_backend:pdfplumber"],
                    duration_s=0.0,
                )
            except Exception as exc:
                return PageResult(
                    page=page_number,
                    status="failed",
                    page_class=decision.page_class,
                    method=None,
                    error=f"{type(exc).__name__}: {exc}",
                    duration_s=0.0,
                )

        cache_key = anydoc_cache_key(
            source_hash,
            page_number,
            _version("firecrawl-anydoc"),
            config.fast.backend,
            config.fast.model_dump(mode="json"),
        )
        cached = cache.get("anydoc", cache_key)
        if cached is not None:
            blocks = [Block.model_validate(item) for item in cached.get("blocks", [])]
            metrics.record_cache(hit=True)
            return PageResult(
                page=page_number,
                status="ok",
                page_class=decision.page_class,
                method="anydoc",
                blocks=blocks,
                warnings=["cache_hit:anydoc"],
                duration_s=0.0,
            )
        metrics.record_cache(hit=False)
        try:
            page_pdf = self.page_pdf_factory(source_path, page_number)
            block = self._fast().extract(page_pdf, page=page_number)
            normalized = _normalize_block(block, page_number, "anydoc")
            cache.put("anydoc", cache_key, {"blocks": [normalized.model_dump(mode="json")]})
            return PageResult(
                page=page_number,
                status="ok",
                page_class=decision.page_class,
                method="anydoc",
                blocks=[normalized],
                duration_s=0.0,
            )
        except Exception as exc:
            if config.fast.fallback == "pdfplumber" and self.fallback_extractor is not None:
                try:
                    blocks = self._blocks_from_fallback(page_number, page)
                    warning = f"anydoc_fallback:{type(exc).__name__}: {exc}"
                    warnings.append(f"page {page_number} used pdfplumber fallback")
                    return PageResult(
                        page=page_number,
                        status="ok",
                        page_class=decision.page_class,
                        method="pdfplumber",
                        blocks=blocks,
                        warnings=[warning],
                        duration_s=0.0,
                    )
                except Exception as fallback_error:
                    exc = fallback_error
            return PageResult(
                page=page_number,
                status="failed",
                page_class=decision.page_class,
                method=None,
                warnings=[f"anydoc_failed:{type(exc).__name__}"],
                error=f"{type(exc).__name__}: {exc}",
                duration_s=0.0,
            )
