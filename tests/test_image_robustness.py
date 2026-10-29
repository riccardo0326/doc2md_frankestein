from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from test_hybrid_images import CountingVision, FakeFast, image_pdf, png

from doc2md.config import CacheConfig, Config, ImageConfig
from doc2md.converters.pdf import PdfConverter
from doc2md.converters.pdf.images import (
    ImageCandidate,
    collect_images,
    place_image_drafts,
    process_images,
)
from doc2md.models import BBox, Block, ImageBlockDraft, PageResult, Provenance
from doc2md.vision.fake import FakeVisionBackend


def test_filter_boundaries_are_inclusive_and_skips_make_no_backend_calls() -> None:
    images = [
        {"id": "equal", "x0": 0, "x1": 64, "y0": 0, "y1": 64},
        {"id": "width", "x0": 0, "x1": 63, "y0": 0, "y1": 64},
        {"id": "height", "x0": 0, "x1": 64, "y0": 0, "y1": 63},
        {"id": "area", "x0": 0, "x1": 10, "y0": 0, "y1": 10},
        {"id": "aspect", "x0": 0, "x1": 4, "y0": 0, "y1": 1},
    ]
    rendered = {
        "equal": png((64, 64), "red"),
        "width": png((63, 64), "green"),
        "height": png((64, 63), "yellow"),
        "area": png((10, 10), "black"),
        "aspect": png((4, 1), "blue"),
    }
    candidates = collect_images(
        SimpleNamespace(images=images),
        None,
        1,
        ImageConfig(min_width_px=64, min_height_px=64, min_area_px=4096, max_aspect=4),
        {},
        renderer=lambda _page, _number, image, _dpi: rendered[image["id"]],
    )

    by_id = {candidate.image_id: candidate for candidate in candidates}
    assert by_id["p0001-i01"].skip_reason is None
    assert by_id["p0001-i02"].skip_reason == "too_small"
    assert by_id["p0001-i03"].skip_reason == "too_small"
    assert by_id["p0001-i04"].skip_reason == "too_small"
    assert by_id["p0001-i05"].skip_reason == "too_small"
    result = process_images(candidates, FakeVisionBackend(), prompt_id="prompt", output_dir=None)
    assert result.cache_misses == 1
    assert len(result.calls) == 1


def test_repeated_conversion_has_byte_identical_outputs(tmp_path: Path) -> None:
    source = tmp_path / "repeat.pdf"
    source.write_bytes(image_pdf(page_count=2))
    vision = CountingVision()
    from doc2md.converters.pdf.images import ImageStage

    stage = ImageStage(
        ImageConfig(min_width_px=64, min_height_px=64, min_area_px=100),
        backend=vision,
        renderer=lambda _page, _number, _image, _dpi: png((80, 80)),
    )
    converter = PdfConverter(
        fast_extractor=FakeFast(),
        image_stage=stage,
        page_pdf_factory=lambda _path, page: f"%PDF-page-{page}".encode(),
    )
    config = Config(
        images=ImageConfig(min_width_px=64, min_height_px=64, min_area_px=100),
        cache=CacheConfig(enabled=False),
    )

    first = converter.convert(source, tmp_path / "first", config=config)
    second = converter.convert(source, tmp_path / "second", config=config)

    assert first.markdown == second.markdown
    assert first.document.model_dump(mode="json") == second.document.model_dump(mode="json")
    assert first.json_path is not None and second.json_path is not None
    assert first.json_path.read_bytes() == second.json_path.read_bytes()
    first_asset = tmp_path / "first" / "repeat" / "images" / "p0001-i01.png"
    second_asset = tmp_path / "second" / "repeat" / "images" / "p0001-i01.png"
    assert first_asset.read_bytes() == second_asset.read_bytes()


def test_placement_keeps_pages_local_and_handles_unknown_bboxes() -> None:
    page_one = PageResult(
        page=1,
        status="ok",
        page_class="TEXT",
        method="anydoc",
        blocks=[
            Block(
                block_id="p0001-b001",
                type="paragraph",
                markdown="above",
                text="above",
                provenance=Provenance(
                    page=1, source="anydoc", bbox=BBox(x0=0, y0=0, x1=10, y1=10)
                ),
            ),
            Block(
                block_id="p0001-b002",
                type="paragraph",
                markdown="unknown",
                text="unknown",
                provenance=Provenance(page=1, source="anydoc"),
            ),
            Block(
                block_id="p0001-b003",
                type="paragraph",
                markdown="below",
                text="below",
                provenance=Provenance(
                    page=1, source="anydoc", bbox=BBox(x0=0, y0=50, x1=10, y1=60)
                ),
            ),
        ],
        duration_s=0.0,
    )
    page_two = page_one.model_copy(update={"page": 2, "blocks": []})
    drafts = [
        ImageBlockDraft(
            image_id="p0001-i01",
            page=1,
            markdown="figure one",
            text="figure one",
            bbox=BBox(x0=0, y0=20, x1=10, y1=30),
        ),
        ImageBlockDraft(
            image_id="p0002-i01",
            page=2,
            markdown="figure two",
            text="figure two",
            bbox=BBox(x0=0, y0=20, x1=10, y1=30),
        ),
    ]

    placed = place_image_drafts([page_one, page_two], drafts)

    assert [block.text for block in placed[0].blocks] == ["above", "figure one", "unknown", "below"]
    assert [block.text for block in placed[1].blocks] == ["figure two"]


def test_render_failure_has_stable_placeholder_and_no_backend_call() -> None:
    candidate = ImageCandidate(
        image_id="p0001-i01",
        page=1,
        png=None,
        width_px=0,
        height_px=0,
        sha256="",
        bbox=BBox(x0=0, y0=0, x1=10, y1=10),
        error="RuntimeError: crop failed",
    )
    vision = CountingVision()

    result = process_images([candidate], vision, prompt_id="prompt", output_dir=None)

    assert len(result.records) == 1
    assert result.records[0].status == "failed"
    assert result.blocks[0].markdown == "<!-- image p0001-i01: render failed -->"
    assert vision.calls == 0
