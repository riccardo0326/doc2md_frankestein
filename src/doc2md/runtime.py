from __future__ import annotations

from pathlib import Path

from .config import Config
from .converters.pdf import AnyDocFastExtractor, KelpieHardExtractor, PdfConverter
from .converters.pdf.images import ImageStage
from .models import Block, RouteDecision
from .vision.base import VisionBackend, VisionResult
from .vision.fake import FakeVisionBackend
from .vision.kelpie import KelpieVisionBackend


class PerPageKelpieHardExtractor:
    """Adapt the batch Kelpie hard extractor to the converter page seam."""

    def __init__(self, source: Path, extractor: KelpieHardExtractor) -> None:
        self.source = source
        self.extractor = extractor

    def __call__(self, page: int, _pdf_page: object, _decision: RouteDecision) -> list[Block]:
        return self.extractor.extract(self.source, [page]).get(page, [])

    def drain_calls(self) -> list[tuple[str, VisionResult]]:
        return self.extractor.drain_calls()


def _vision_backend(config: Config) -> VisionBackend:
    if config.vision.backend == "fake":
        return FakeVisionBackend()
    return KelpieVisionBackend(config.vision)


def build_runtime(source: str | Path, config: Config | None = None) -> PdfConverter:
    """Build the configured public adapters for one source document."""
    effective_config = config or Config()
    source_path = Path(source)
    vision = _vision_backend(effective_config)
    hard = KelpieHardExtractor(
        vision,
        page_dpi=effective_config.hard.page_dpi,
        prompt_id=effective_config.vision.transcribe_prompt,
    )
    images = ImageStage(
        effective_config.images,
        backend=vision,
        cache_config=effective_config.cache,
    )
    return PdfConverter(
        fast_extractor=AnyDocFastExtractor(),
        hard_extractor=PerPageKelpieHardExtractor(source_path, hard),
        image_stage=images,
    )
