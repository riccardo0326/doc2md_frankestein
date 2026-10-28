from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from doc2md.config import ImageConfig
from doc2md.converters.pdf.images import collect_images, place_image_drafts, process_images
from doc2md.models import BBox, Block, ImageBlockDraft, PageResult, Provenance
from doc2md.vision.base import VisionResult
from doc2md.vision.fake import FakeVisionBackend


def png(size: tuple[int, int], color: str = "red") -> bytes:
    image = Image.new("RGB", size, color)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


class CountingVision(FakeVisionBackend):
    def __init__(self) -> None:
        super().__init__(model="fake-image")
        self.calls = 0

    def describe_image(
        self, image_png: bytes, *, prompt_id: str, lang: str = "auto"
    ) -> VisionResult:
        self.calls += 1
        return super().describe_image(image_png, prompt_id=prompt_id, lang=lang)


def test_image_filter_records_tiny_aspect_duplicate_and_render_failures() -> None:
    images = [
        {"id": "tiny", "x0": 0, "x1": 10, "y0": 0, "y1": 10},
        {"id": "wide", "x0": 0, "x1": 200, "y0": 0, "y1": 10},
        {"id": "valid", "x0": 0, "x1": 80, "y0": 0, "y1": 80},
        {"id": "duplicate", "x0": 0, "x1": 80, "y0": 0, "y1": 80},
        {"id": "broken", "x0": 0, "x1": 80, "y0": 0, "y1": 80},
    ]
    page = SimpleNamespace(images=images, width=100, height=100)
    rendered = {
        "tiny": png((10, 10)),
        "wide": png((200, 10)),
        "valid": png((80, 80)),
        "duplicate": png((80, 80)),
    }

    candidates = collect_images(
        page,
        None,
        2,
        ImageConfig(min_width_px=64, min_height_px=1, min_area_px=100, max_aspect=8),
        {},
        renderer=lambda _page, _number, image, _dpi: rendered[image["id"]],
    )

    by_id = {candidate.image_id: candidate for candidate in candidates}
    assert by_id["p0002-i01"].skip_reason == "too_small"
    assert by_id["p0002-i02"].skip_reason == "bad_aspect"
    assert by_id["p0002-i04"].skip_reason == "duplicate"
    assert by_id["p0002-i05"].error is not None


def test_duplicate_images_are_described_once_and_saved_deterministically(tmp_path: Path) -> None:
    image = {"id": "valid", "x0": 0, "x1": 80, "y0": 0, "y1": 80}
    page = SimpleNamespace(images=[image, image], width=100, height=100)
    data = png((80, 80))
    candidates = collect_images(
        page,
        None,
        1,
        ImageConfig(min_width_px=64, min_height_px=64, min_area_px=100),
        {},
        renderer=lambda _page, _number, _image, _dpi: data,
    )
    vision = CountingVision()

    result = process_images(
        candidates,
        vision,
        prompt_id="describe_image.v1",
        output_dir=tmp_path,
    )

    assert vision.calls == 1
    assert (tmp_path / "images" / "p0001-i01.png").is_file()
    assert result.records[1].skip_reason == "duplicate"
    assert result.records[0].usage is not None
    assert result.records[0].description


def test_scanned_pages_are_not_treated_as_embedded_figures() -> None:
    page = SimpleNamespace(images=[{"x0": 0, "x1": 80, "y0": 0, "y1": 80}], width=100, height=100)

    assert collect_images(page, None, 1, ImageConfig(), {}, page_class="SCANNED") == []


def test_image_draft_is_inserted_after_preceding_block() -> None:
    page = PageResult(
        page=1,
        status="ok",
        page_class="TEXT",
        method="anydoc",
        blocks=[
            Block(
                block_id="p0001-b001",
                type="paragraph",
                markdown="before",
                text="before",
                provenance=Provenance(page=1, source="anydoc", bbox=BBox(x0=0, y0=0, x1=10, y1=20)),
            ),
            Block(
                block_id="p0001-b002",
                type="paragraph",
                markdown="after",
                text="after",
                provenance=Provenance(
                    page=1,
                    source="anydoc",
                    bbox=BBox(x0=0, y0=50, x1=10, y1=70),
                ),
            ),
        ],
        duration_s=0.0,
    )
    draft = ImageBlockDraft(
        image_id="p0001-i01",
        page=1,
        markdown="![Figure p0001-i01](images/p0001-i01.png)",
        text="description",
        source_path="images/p0001-i01.png",
        bbox=BBox(x0=0, y0=25, x1=10, y1=40),
    )

    placed = place_image_drafts([page], [draft])[0]

    assert [block.type for block in placed.blocks] == ["paragraph", "figure", "paragraph"]
