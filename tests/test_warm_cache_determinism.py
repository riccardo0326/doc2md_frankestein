from __future__ import annotations

import json
from pathlib import Path

from test_hybrid_images import CountingVision, FakeFast, image_pdf, png

from doc2md.config import CacheConfig, Config, ImageConfig
from doc2md.converters.pdf import PdfConverter
from doc2md.converters.pdf.images import ImageStage


def image_config() -> ImageConfig:
    return ImageConfig(min_width_px=64, min_height_px=64, min_area_px=100)


def test_cold_and_warm_document_outputs_are_identical(tmp_path: Path) -> None:
    source = tmp_path / "warm-cache.pdf"
    source.write_bytes(image_pdf(page_count=2))
    cache_dir = tmp_path / "cache"
    vision = CountingVision()
    converter = PdfConverter(
        fast_extractor=FakeFast(),
        image_stage=ImageStage(
            image_config(),
            backend=vision,
            renderer=lambda _page, _number, _image, _dpi: png((80, 80)),
        ),
        page_pdf_factory=lambda _path, page: f"%PDF-page-{page}".encode(),
    )
    config = Config(images=image_config(), cache=CacheConfig(dir=str(cache_dir)))

    cold = converter.convert(source, tmp_path / "cold", config=config)
    warm = converter.convert(source, tmp_path / "warm", config=config)

    assert cold.markdown == warm.markdown
    assert cold.document.model_dump(mode="json") == warm.document.model_dump(mode="json")
    assert cold.json_path is not None and warm.json_path is not None
    assert cold.json_path.read_bytes() == warm.json_path.read_bytes()
    for record in cold.document.images:
        if record.path is None:
            continue
        cold_asset = tmp_path / "cold" / "warm-cache" / record.path
        warm_asset = tmp_path / "warm" / "warm-cache" / record.path
        assert cold_asset.read_bytes() == warm_asset.read_bytes()

    assert vision.calls == 1
    assert warm.stats.calls == []
    assert warm.stats.input_tokens == 0
    assert warm.stats.total_tokens == 0
    assert warm.stats.cache_hits == 3

    cold_run = json.loads(cold.run_path.read_text(encoding="utf-8")) if cold.run_path else {}
    warm_run = json.loads(warm.run_path.read_text(encoding="utf-8")) if warm.run_path else {}
    assert "images" not in warm_run
    assert cold_run["totals"]["cache"] == {"hits": 0, "misses": 3}
    assert warm_run["totals"]["cache"] == {"hits": 3, "misses": 0}
