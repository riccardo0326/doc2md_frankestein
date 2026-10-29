from __future__ import annotations

import hashlib
import json
from pathlib import Path

from test_hybrid_images import CountingVision, FakeFast, image_pdf, png

from doc2md.cache import DiskCache, vision_cache_key
from doc2md.config import CacheConfig, Config, ImageConfig
from doc2md.converters.pdf import PdfConverter
from doc2md.converters.pdf.images import ImageStage


def image_config() -> ImageConfig:
    return ImageConfig(min_width_px=64, min_height_px=64, min_area_px=100)


def test_image_cache_metrics_and_sidecars_are_cache_aware(tmp_path: Path) -> None:
    source = tmp_path / "telemetry.pdf"
    source.write_bytes(image_pdf(page_count=2))
    cache_dir = tmp_path / "cache"
    vision = CountingVision()
    stage = ImageStage(
        image_config(),
        backend=vision,
        renderer=lambda _page, _number, _image, _dpi: png((80, 80)),
    )
    converter = PdfConverter(
        fast_extractor=FakeFast(),
        image_stage=stage,
        page_pdf_factory=lambda _path, page: f"%PDF-page-{page}".encode(),
    )
    config = Config(images=image_config(), cache=CacheConfig(dir=str(cache_dir)))

    first = converter.convert(source, tmp_path / "first", config=config)
    second = converter.convert(source, tmp_path / "second", config=config)

    assert vision.calls == 1
    assert len(first.document.images) == 2
    assert len(second.document.images) == 2
    assert [call.kind for call in first.stats.calls] == ["describe_image"]
    assert first.stats.calls[0].id == "p0001-i01"
    assert first.stats.calls[0].cache_hit is False
    assert first.stats.calls[0].input_tokens == 12
    assert first.stats.calls[0].output_tokens > 0
    assert first.stats.calls[0].total_tokens == 12 + first.stats.calls[0].output_tokens
    assert first.stats.cache_misses == 3
    assert first.stats.cache_hits == 0
    assert second.stats.calls == []
    assert second.stats.input_tokens == 0
    assert second.stats.total_tokens == 0
    assert second.stats.cache_hits == 3
    assert second.stats.cache_misses == 0
    assert (tmp_path / "second" / "telemetry" / "images" / "p0001-i01.png").is_file()

    assert first.run_path is not None
    run_payload = json.loads(first.run_path.read_text(encoding="utf-8"))
    assert run_payload["totals"]["vision"]["calls"] == 1
    assert run_payload["totals"]["vision"]["total_tokens"] == first.stats.total_tokens
    assert run_payload["calls"][0]["kind"] == "describe_image"
    assert "images" not in run_payload

    assert first.json_path is not None
    document_payload = json.loads(first.json_path.read_text(encoding="utf-8"))
    assert len(document_payload["images"]) == 2
    assert document_payload["images"][1]["skip_reason"] == "duplicate"


def test_corrupt_image_cache_entry_isolated_and_recomputed(tmp_path: Path) -> None:
    source = tmp_path / "corrupt-image-cache.pdf"
    source.write_bytes(image_pdf())
    cache_dir = tmp_path / "cache"
    config = Config(images=image_config(), cache=CacheConfig(dir=str(cache_dir)))
    first_vision = CountingVision()
    converter = PdfConverter(
        fast_extractor=FakeFast(),
        image_stage=ImageStage(
            image_config(),
            backend=first_vision,
            renderer=lambda _page, _number, _image, _dpi: png((80, 80)),
        ),
        page_pdf_factory=lambda _path, _page: b"%PDF-page",
    )
    converter.convert(source, config=config)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    key = vision_cache_key(
        hashlib.sha256(png((80, 80))).hexdigest(),
        "describe_image.v1",
        "fake-image",
        image_config().model_dump(mode="json"),
        backend="fake",
    )
    cache = DiskCache(cache_dir, source_hash)
    cache.path_for("vision-image", key).write_text("not-json", encoding="utf-8")

    second_vision = CountingVision()
    second_converter = PdfConverter(
        fast_extractor=FakeFast(),
        image_stage=ImageStage(
            image_config(),
            backend=second_vision,
            renderer=lambda _page, _number, _image, _dpi: png((80, 80)),
        ),
        page_pdf_factory=lambda _path, _page: b"%PDF-page",
    )
    result = second_converter.convert(source, config=config)

    assert second_vision.calls == 1
    assert result.stats.cache_misses == 1
    assert any(warning.startswith("cache_corrupt:") for warning in result.stats.warnings)


def test_no_cache_makes_image_run_cold(tmp_path: Path) -> None:
    source = tmp_path / "no-cache-image.pdf"
    source.write_bytes(image_pdf())
    cache_dir = tmp_path / "cache"
    vision = CountingVision()
    result = PdfConverter(
        fast_extractor=FakeFast(),
        image_stage=ImageStage(
            image_config(),
            backend=vision,
            renderer=lambda _page, _number, _image, _dpi: png((80, 80)),
        ),
        page_pdf_factory=lambda _path, _page: b"%PDF-page",
    ).convert(
        source,
        config=Config(images=image_config(), cache=CacheConfig(dir=str(cache_dir))),
        no_cache=True,
    )

    assert vision.calls == 1
    assert result.stats.cache_hits == 0
    assert result.stats.cache_misses == 2
    assert not cache_dir.exists()
