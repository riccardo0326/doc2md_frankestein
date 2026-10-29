from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HardConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    engine: Literal["kelpie", "docling-dev-only"] = "kelpie"
    languages: list[str] = Field(default_factory=lambda: ["en", "de"])
    page_dpi: int = Field(default=200, ge=72)


class KelpieConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    base_url: str = ""
    model: str = "DARE-NoCloud-Helios"


class VisionConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    backend: Literal["kelpie", "fake"] = "kelpie"
    max_tokens: int = Field(default=384, ge=1)
    transcribe_max_tokens: int = Field(default=1600, ge=1)
    timeout_s: float = Field(default=120.0, gt=0)
    max_retries: int = Field(default=3, ge=0)
    transcribe_prompt: str = "transcribe_page.v1"
    kelpie: KelpieConfig = Field(default_factory=KelpieConfig)


class ImageConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = True
    render_dpi: int = Field(default=150, ge=1)
    min_width_px: int = Field(default=64, ge=1)
    min_height_px: int = Field(default=64, ge=1)
    min_area_px: int = Field(default=10_000, ge=1)
    max_aspect: float = Field(default=8.0, ge=1)


class CacheConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = True
    dir: str = ".doc2md_cache"


class RouterConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    min_chars: int = Field(default=50, ge=0)
    min_chars_text_layer: int = Field(default=10, ge=0)
    scan_image_ratio: float = Field(default=0.6, ge=0, le=1)
    max_garbled: float = Field(default=0.02, ge=0, le=1)
    table_none_ratio: float = Field(default=0.15, ge=0, le=1)
    complex_image_ratio: float = Field(default=0.4, ge=0, le=1)
    image_page_min_chars: int = Field(default=400, ge=0)


class FastConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    backend: Literal["anydoc", "pdfplumber"] = "anydoc"
    fallback: Literal["none", "pdfplumber"] = "none"


class RenderConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    page_markers: bool = False
    block_anchors: bool = False


class Config(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    router: RouterConfig = Field(default_factory=RouterConfig)
    fast: FastConfig = Field(default_factory=FastConfig)
    render: RenderConfig = Field(default_factory=RenderConfig)
    hard: HardConfig = Field(default_factory=HardConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)
    images: ImageConfig = Field(default_factory=ImageConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
