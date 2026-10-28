from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PageClass = Literal["TEXT", "COMPLEX", "SCANNED"]
Method = Literal["pdfplumber", "docling", "vision", "anydoc"]
BlockType = Literal["heading", "paragraph", "list", "table", "figure", "code", "other"]
PageStatus = Literal["ok", "failed", "skipped"]


class ContractModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)


class BBox(ContractModel):
    x0: float
    y0: float
    x1: float
    y1: float


class SourceInfo(ContractModel):
    name: str
    sha256: str
    size_bytes: int = Field(ge=0)
    page_count: int = Field(ge=0)


class ToolInfo(ContractModel):
    doc2md: str
    pdfplumber: str
    anydoc: str | None = None
    backend: str | None = None
    docling: str | None = None
    pypdfium2: str | None = None
    config_hash: str


class Provenance(ContractModel):
    page: int = Field(ge=1)
    source: Method
    bbox: BBox | None = None


class Block(ContractModel):
    block_id: str
    type: BlockType
    markdown: str
    text: str
    level: int | None = None
    provenance: Provenance
    meta: dict[str, str | int | float | bool] = Field(default_factory=dict)


class PageSignals(ContractModel):
    chars: int = Field(ge=0)
    words: int = Field(ge=0)
    image_area_ratio: float = Field(ge=0, le=1)
    image_count: int = Field(ge=0)
    table_count: int = Field(ge=0)
    table_irregular: bool
    garbled_ratio: float = Field(ge=0, le=1)
    has_text_layer: bool


class RouteDecision(ContractModel):
    page: int = Field(ge=1)
    page_class: PageClass
    reasons: list[str] = Field(default_factory=list)
    signals: PageSignals


class Usage(ContractModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    estimated: bool


class ImageRecord(ContractModel):
    image_id: str
    page: int = Field(ge=1)
    bbox: BBox | None = None
    width_px: int = Field(ge=0)
    height_px: int = Field(ge=0)
    sha256: str
    status: Literal["described", "skipped", "failed"]
    skip_reason: Literal["too_small", "bad_aspect", "duplicate", "vision_disabled"] | None = None
    canonical_image_id: str | None = None
    path: str | None = None
    description: str | None = None
    usage: Usage | None = None


class PageResult(ContractModel):
    page: int = Field(ge=1)
    status: PageStatus
    page_class: PageClass
    method: Method | None
    blocks: list[Block] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
    duration_s: float = Field(ge=0)


class ImageBlockDraft(ContractModel):
    image_id: str
    page: int = Field(ge=1)
    markdown: str
    text: str
    source_path: str | None = None
    bbox: BBox | None = None


class ConvertedDocument(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    source: SourceInfo
    pipeline: str
    pages: list[PageResult]
    images: list[ImageRecord] = Field(default_factory=list)
    tool: ToolInfo


class PageStat(ContractModel):
    page: int = Field(ge=1)
    status: PageStatus
    page_class: PageClass | None
    method: Method | None
    duration_s: float = Field(ge=0)
    reasons: list[str] = Field(default_factory=list)


class CallStat(ContractModel):
    kind: Literal["describe_image", "transcribe_page"]
    id: str
    model: str
    latency_s: float = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    estimated: bool
    cache_hit: bool = False


class RunStats(ContractModel):
    run_id: str
    started_at: datetime
    finished_at: datetime
    pipeline: str
    source: SourceInfo
    config_hash: str
    wall_time_s: float = Field(ge=0)
    pages: list[PageStat] = Field(default_factory=list)
    pages_failed: int = Field(default=0, ge=0)
    vision_calls: int = Field(default=0, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    tokens_estimated: bool = False
    calls: list[CallStat] = Field(default_factory=list)
    cache_hits: int = Field(default=0, ge=0)
    cache_misses: int = Field(default=0, ge=0)
    docling_pages: int = Field(default=0, ge=0)
    docling_time_s: float = Field(default=0, ge=0)
    warnings: list[str] = Field(default_factory=list)

    @property
    def vision_tokens_total(self) -> int:
        return self.total_tokens


class ConversionResult(ContractModel):
    document: ConvertedDocument
    markdown: str
    markdown_path: Path | None
    json_path: Path | None
    run_path: Path | None
    stats: RunStats
