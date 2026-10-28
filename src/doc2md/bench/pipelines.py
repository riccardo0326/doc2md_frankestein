from __future__ import annotations

from typing import Literal

PipelineName = Literal["tiered", "full-vision", "docling-only", "baseline_current"]


def validate_pipeline(name: str) -> PipelineName:
    if name not in {"tiered", "full-vision", "docling-only", "baseline_current"}:
        raise ValueError(f"unknown benchmark pipeline: {name}")
    return name  # type: ignore[return-value]
