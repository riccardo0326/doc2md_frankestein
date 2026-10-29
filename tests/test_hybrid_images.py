from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

from PIL import Image

from doc2md.config import CacheConfig, Config, FastConfig, ImageConfig
from doc2md.converters.pdf import PdfConverter
from doc2md.converters.pdf.images import ImageStage
from doc2md.errors import PageExtractionError
from doc2md.models import Block, Provenance
from doc2md.vision.base import VisionResult
from doc2md.vision.fake import FakeVisionBackend


def png(size: tuple[int, int], color: str = "red") -> bytes:
    image = Image.new("RGB", size, color)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def image_pdf(page_count: int = 1) -> bytes:
    raw_image = bytes([220, 30, 30]) * (80 * 80)
    page_numbers = list(range(3, 3 + page_count))
    font_number = 3 + page_count
    image_number = font_number + 1
    content_start = image_number + 1
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        (
            f"<< /Type /Pages /Kids [{ ' '.join(f'{page} 0 R' for page in page_numbers) }] "
            f"/Count {page_count} >>"
        ).encode(),
    ]
    for index, content_number in enumerate(
        range(content_start, content_start + page_count), start=1
    ):
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {font_number} 0 R >> "
                f"/XObject << /Im1 {image_number} 0 R >> >> /Contents {content_number} 0 R >>"
            ).encode()
        )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(
        (
            f"<< /Type /XObject /Subtype /Image /Width 80 /Height 80 "
            f"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Length {len(raw_image)} >>\n"
            f"stream\n"
        ).encode()
        + raw_image
        + b"\nendstream"
    )
    for index in range(page_count):
        text = (
            f"Digital text page {index + 1} contains enough extractable words for routing. "
            "The embedded figure adds useful visual context."
        )
        stream = (
            f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET "
            "q 80 0 0 80 72 600 cm /Im1 Do Q"
        ).encode()
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode())
        output.extend(body)
        output.extend(b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(output)


def anydoc_block(page: int, text: str = "AnyDoc text") -> Block:
    return Block(
        block_id=f"p{page:04d}-b001",
        type="paragraph",
        markdown=text,
        text=text,
        provenance=Provenance(page=page, source="anydoc"),
    )


class FakeFast:
    def __init__(self, fail: bool = False) -> None:
        self.pages: list[int] = []
        self.fail = fail

    def extract(self, page_pdf: bytes, *, page: int) -> Block:
        self.pages.append(page)
        if self.fail:
            raise PageExtractionError("AnyDoc unavailable")
        return anydoc_block(page, f"AnyDoc page {page}")


class CountingVision(FakeVisionBackend):
    def __init__(self) -> None:
        super().__init__(model="fake-image")
        self.calls = 0

    def describe_image(
        self, image_png: bytes, *, prompt_id: str, lang: str = "auto"
    ) -> VisionResult:
        self.calls += 1
        return super().describe_image(image_png, prompt_id=prompt_id, lang=lang)


def image_stage(vision: CountingVision, renderer: object) -> ImageStage:
    return ImageStage(
        ImageConfig(min_width_px=64, min_height_px=64, min_area_px=100),
        backend=vision,
        renderer=renderer,  # type: ignore[arg-type]
    )


def convert_config() -> Config:
    return Config(
        images=ImageConfig(min_width_px=64, min_height_px=64, min_area_px=100),
        cache=CacheConfig(enabled=False),
    )


def test_text_page_assembles_image_markdown_sidecar_and_asset(tmp_path: Path) -> None:
    source = tmp_path / "text-image.pdf"
    source.write_bytes(image_pdf())
    vision = CountingVision()
    stage = image_stage(vision, lambda _page, _number, _image, _dpi: png((80, 80)))
    converter = PdfConverter(
        fast_extractor=FakeFast(),
        image_stage=stage,
        page_pdf_factory=lambda _path, page: f"%PDF-page-{page}".encode(),
    )

    result = converter.convert(source, tmp_path / "out", config=convert_config())

    page = result.document.pages[0]
    assert page.method == "anydoc"
    assert [block.type for block in page.blocks] == ["paragraph", "figure"]
    assert page.blocks[0].provenance.source == "anydoc"
    assert page.blocks[1].provenance.page == 1
    assert page.blocks[1].provenance.bbox is not None
    assert len(result.document.images) == 1
    record = result.document.images[0]
    assert record.status == "described"
    assert record.path == "images/p0001-i01.png"
    assert record.description
    assert vision.calls == 1
    assert (tmp_path / "out" / "text-image" / "images" / "p0001-i01.png").is_file()
    assert "images/p0001-i01.png" in result.markdown
    assert result.json_path is not None
    sidecar = json.loads(result.json_path.read_text(encoding="utf-8"))
    assert sidecar["images"][0]["image_id"] == "p0001-i01"


def test_pdfplumber_fallback_still_processes_text_images(tmp_path: Path) -> None:
    source = tmp_path / "fallback-image.pdf"
    source.write_bytes(image_pdf())
    vision = CountingVision()
    stage = image_stage(vision, lambda _page, _number, _image, _dpi: png((80, 80)))

    def fallback(page: int, _pdf_page: object) -> list[Block]:
        return [
            Block(
                block_id=f"p{page:04d}-b001",
                type="paragraph",
                markdown="fallback text",
                text="fallback text",
                provenance=Provenance(page=page, source="pdfplumber"),
            )
        ]

    result = PdfConverter(
        fast_extractor=FakeFast(fail=True),
        fallback_extractor=fallback,
        image_stage=stage,
        page_pdf_factory=lambda _path, _page: b"%PDF-page",
    ).convert(
        source,
        tmp_path / "out",
        config=Config(
            fast=FastConfig(fallback="pdfplumber"),
            images=ImageConfig(min_width_px=64, min_height_px=64, min_area_px=100),
            cache=CacheConfig(enabled=False),
        ),
    )

    page = result.document.pages[0]
    assert page.method == "pdfplumber"
    assert any("fallback" in warning for warning in page.warnings)
    assert len(result.document.images) == 1
    assert vision.calls == 1


def test_image_crop_failure_isolated_from_text_page(tmp_path: Path) -> None:
    source = tmp_path / "broken-image.pdf"
    source.write_bytes(image_pdf())
    vision = CountingVision()

    def broken_renderer(_page: object, _number: int, _image: dict[str, object], _dpi: int) -> bytes:
        raise RuntimeError("crop failed")

    result = PdfConverter(
        fast_extractor=FakeFast(),
        image_stage=image_stage(vision, broken_renderer),
        page_pdf_factory=lambda _path, _page: b"%PDF-page",
    ).convert(source, config=convert_config())

    assert result.document.pages[0].status == "ok"
    assert result.document.pages[0].blocks[0].text == "AnyDoc page 1"
    assert result.document.images[0].status == "failed"
    assert vision.calls == 0


def test_cross_page_duplicate_reuses_canonical_image_description(tmp_path: Path) -> None:
    source = tmp_path / "duplicate-images.pdf"
    source.write_bytes(image_pdf(page_count=2))
    vision = CountingVision()
    stage = image_stage(vision, lambda _page, _number, _image, _dpi: png((80, 80)))

    result = PdfConverter(
        fast_extractor=FakeFast(),
        image_stage=stage,
        page_pdf_factory=lambda _path, page: f"%PDF-page-{page}".encode(),
    ).convert(source, tmp_path / "out", config=convert_config())

    assert vision.calls == 1
    assert [record.image_id for record in result.document.images] == [
        "p0001-i01",
        "p0002-i01",
    ]
    duplicate = result.document.images[1]
    assert duplicate.skip_reason == "duplicate"
    assert duplicate.canonical_image_id == "p0001-i01"
    assert duplicate.path == "images/p0001-i01.png"
    assert duplicate.description == result.document.images[0].description
    assert result.document.pages[1].blocks[1].provenance.page == 2


def test_disabling_images_keeps_context_without_backend_call(tmp_path: Path) -> None:
    source = tmp_path / "disabled-images.pdf"
    source.write_bytes(image_pdf())
    vision = CountingVision()
    stage = image_stage(vision, lambda _page, _number, _image, _dpi: png((80, 80)))

    result = PdfConverter(
        fast_extractor=FakeFast(),
        image_stage=stage,
        page_pdf_factory=lambda _path, _page: b"%PDF-page",
    ).convert(
        source,
        config=Config(
            images=ImageConfig(enabled=False, min_width_px=64, min_height_px=64, min_area_px=100),
            cache=CacheConfig(enabled=False),
        ),
    )

    assert result.document.images[0].skip_reason == "vision_disabled"
    assert result.document.pages[0].blocks[1].type == "figure"
    assert vision.calls == 0
