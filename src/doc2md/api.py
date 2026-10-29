from __future__ import annotations

from pathlib import Path
from typing import Literal

from .config import Config
from .converters.pdf import PdfConverter
from .converters.pdf.router import classify
from .converters.pdf.signals import compute_signals
from .converters.pdf.source import PdfSource
from .models import ConversionResult, RouteDecision
from .runtime import build_runtime


def convert(
    source: str | Path,
    out_dir: str | Path | None = None,
    *,
    config: Config | None = None,
    pages: tuple[int, ...] | None = None,
    strict: bool = False,
    no_cache: bool = False,
    pipeline: Literal["tiered", "full-vision", "docling-only"] = "tiered",
    converter: PdfConverter | None = None,
) -> ConversionResult:
    """Run the standalone tiered converter with optional injected seams."""
    if converter is None:
        effective_config = config or Config()
        converter = build_runtime(source, effective_config)
        config = effective_config
    return converter.convert(
        source,
        out_dir,
        config=config,
        pages=pages,
        strict=strict,
        no_cache=no_cache,
        pipeline=pipeline,
    )


def inspect_pdf(
    source: str | Path,
    *,
    config: Config | None = None,
) -> list[RouteDecision]:
    """Inspect and route every original PDF page without invoking an adapter."""
    effective_config = config or Config()
    decisions: list[RouteDecision] = []
    with PdfSource(source) as pdf:
        for page_number, page in pdf:
            signals = compute_signals(page, effective_config.router)
            decisions.append(classify(signals, effective_config.router, page=page_number))
    return decisions
