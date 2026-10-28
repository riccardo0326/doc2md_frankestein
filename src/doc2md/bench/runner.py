from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ..api import convert
from ..config import CacheConfig, Config
from ..models import ConversionResult
from .baseline_current import BaselineAdapter
from .pipelines import validate_pipeline
from .suite import BenchmarkSuite, load_suite

RESULTS_COLUMNS = [
    "run_id", "doc_id", "pipeline", "rep", "pages_total", "pages_text",
    "pages_complex", "pages_scanned", "pages_failed", "images_found",
    "images_described", "images_skipped", "vision_calls", "input_tokens",
    "output_tokens", "total_tokens", "tokens_estimated", "docling_pages",
    "wall_time_s", "time_easy_pages_s", "time_hard_pages_s", "output_chars",
    "cache_hits", "error",
]

ConversionFunction = Callable[..., ConversionResult]


class BenchmarkRunner:
    def __init__(
        self,
        *,
        convert_fn: ConversionFunction = convert,
        baseline: BaselineAdapter | None = None,
    ) -> None:
        self.convert_fn = convert_fn
        self.baseline = baseline

    def run(
        self,
        suite_path: str | Path,
        output_root: str | Path = "bench_runs",
        *,
        pipelines: list[str] | None = None,
    ) -> Path:
        suite = load_suite(suite_path)
        selected = pipelines or [item.name for item in suite.pipelines]
        selected = [validate_pipeline(name) for name in selected]
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        run_dir = Path(output_root) / timestamp
        run_dir.mkdir(parents=True, exist_ok=False)
        version_names = ("doc2md", "pydantic", "pdfplumber", "firecrawl-anydoc", "openai")
        versions: dict[str, str] = {}
        for package in version_names:
            try:
                versions[package] = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                versions[package] = "not-installed"
        config_payload = json.dumps(
            {"suite": suite.name, "repetitions": suite.repetitions, "cold_cache": suite.cold_cache},
            sort_keys=True,
            separators=(",", ":"),
        )
        env = {
            "python": sys.version,
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
            "suite": suite.name,
            "cold_cache": suite.cold_cache,
            "versions": versions,
            "config_hash": hashlib.sha256(config_payload.encode("utf-8")).hexdigest(),
        }
        (run_dir / "env.json").write_text(
            json.dumps(env, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        rows: list[dict[str, object]] = []
        for document in suite.documents:
            source = suite.source_path.parent / document.path
            for pipeline in selected:
                for repetition in range(1, suite.repetitions + 1):
                    rows.append(
                        self._run_one(
                            suite,
                            document.id,
                            source,
                            pipeline,
                            repetition,
                            run_dir,
                        )
                    )
        with (run_dir / "results.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=RESULTS_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        return run_dir

    def _run_one(
        self,
        suite: BenchmarkSuite,
        doc_id: str,
        source: Path,
        pipeline: str,
        repetition: int,
        run_dir: Path,
    ) -> dict[str, object]:
        output_dir = run_dir / "outputs" / doc_id / pipeline / f"rep{repetition}"
        output_dir.mkdir(parents=True, exist_ok=True)
        row: dict[str, object] = {column: "" for column in RESULTS_COLUMNS}
        row.update(
            {"run_id": run_dir.name, "doc_id": doc_id, "pipeline": pipeline, "rep": repetition}
        )
        if pipeline == "baseline_current":
            if self.baseline is None:
                row["error"] = "baseline unavailable"
                return row
            try:
                baseline_result = self.baseline.run(source, output_dir)
                row["wall_time_s"] = baseline_result.wall_time_s
                row["output_chars"] = len(
                    baseline_result.markdown_path.read_text(encoding="utf-8")
                )
                if baseline_result.usage is not None:
                    row["input_tokens"] = baseline_result.usage.input_tokens
                    row["output_tokens"] = baseline_result.usage.output_tokens
                    row["total_tokens"] = baseline_result.usage.total_tokens
                    row["tokens_estimated"] = baseline_result.usage.estimated
                return row
            except Exception as exc:
                row["error"] = f"{type(exc).__name__}: {exc}"
                return row

        config = Config(
            cache=CacheConfig(
                enabled=suite.cold_cache,
                dir=str(output_dir / ".doc2md_cache"),
            )
        )
        try:
            result = self.convert_fn(
                source,
                output_dir,
                pipeline=pipeline,
                config=config,
                no_cache=not suite.cold_cache,
            )
            return self._result_row(row, result)
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
            return row

    @staticmethod
    def _result_row(row: dict[str, object], result: ConversionResult) -> dict[str, object]:
        pages = result.document.pages
        stats = result.stats
        row.update(
            {
                "pages_total": len(pages),
                "pages_text": sum(page.page_class == "TEXT" for page in pages),
                "pages_complex": sum(page.page_class == "COMPLEX" for page in pages),
                "pages_scanned": sum(page.page_class == "SCANNED" for page in pages),
                "pages_failed": sum(page.status == "failed" for page in pages),
                "images_found": len(result.document.images),
                "images_described": sum(
                    image.status == "described" for image in result.document.images
                ),
                "images_skipped": sum(
                    image.status == "skipped" for image in result.document.images
                ),
                "vision_calls": stats.vision_calls,
                "input_tokens": stats.input_tokens,
                "output_tokens": stats.output_tokens,
                "total_tokens": stats.total_tokens,
                "tokens_estimated": stats.tokens_estimated,
                "docling_pages": stats.docling_pages,
                "wall_time_s": stats.wall_time_s,
                "time_easy_pages_s": sum(
                    page.duration_s for page in stats.pages if page.page_class == "TEXT"
                ),
                "time_hard_pages_s": sum(
                    page.duration_s for page in stats.pages if page.page_class != "TEXT"
                ),
                "output_chars": len(result.markdown),
                "cache_hits": stats.cache_hits,
            }
        )
        return row
