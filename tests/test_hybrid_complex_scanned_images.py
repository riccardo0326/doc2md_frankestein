from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from doc2md.config import CacheConfig, Config, ImageConfig
from doc2md.converters.pdf import PdfConverter, hybrid
from doc2md.converters.pdf.images import ImageStage
from doc2md.models import Block, Provenance, RouteDecision
from doc2md.vision.base import VisionResult
from doc2md.vision.fake import FakeVisionBackend


def png(size: tuple[int, int]) -> bytes:
    image = Image.new("RGB", size, "blue")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def image_pdf(page_count: int = 1) -> bytes:
    raw_image = bytes([30, 30, 220]) * (80 * 80)
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
    for content_number, _page in zip(
        range(content_start, content_start + page_count), page_numbers
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
        text = f"Page {index + 1} has text and a distinct embedded figure."
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


def decision_for(page_class: str):
    def decide(signals: object, _router: object, page: int) -> RouteDecision:
        return RouteDecision(page=page, page_class=page_class, signals=signals)  # type: ignore[arg-type]

    return decide


class CountingVision(FakeVisionBackend):
    def __init__(self) -> None:
        super().__init__(model="fake-image")
        self.describe_calls = 0
        self.transcribe_calls = 0

    def describe_image(
        self, image_png: bytes, *, prompt_id: str, lang: str = "auto"
    ) -> VisionResult:
        self.describe_calls += 1
        return super().describe_image(image_png, prompt_id=prompt_id, lang=lang)

    def transcribe_page(
        self, image_png: bytes, *, prompt_id: str, lang: str = "auto"
    ) -> VisionResult:
        self.transcribe_calls += 1
        return super().transcribe_page(image_png, prompt_id=prompt_id, lang=lang)


def stage(vision: CountingVision, renderer: object) -> ImageStage:
    return ImageStage(
        ImageConfig(min_width_px=64, min_height_px=64, min_area_px=100),
        backend=vision,
        renderer=renderer,  # type: ignore[arg-type]
    )


def hard_block(page: int) -> Block:
    return Block(
        block_id=f"p{page:04d}-b001",
        type="paragraph",
        markdown=f"Hard page {page}",
        text=f"Hard page {page}",
        provenance=Provenance(page=page, source="vision"),
    )


def config() -> Config:
    return Config(
        images=ImageConfig(min_width_px=64, min_height_px=64, min_area_px=100),
        cache=CacheConfig(enabled=False),
    )


def test_complex_page_keeps_hard_blocks_and_adds_embedded_figure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "complex.pdf"
    source.write_bytes(image_pdf())
    monkeypatch.setattr(hybrid, "classify", decision_for("COMPLEX"))
    vision = CountingVision()
    hard_calls: list[int] = []

    def hard(page: int, _pdf_page: object, _decision: RouteDecision) -> list[Block]:
        hard_calls.append(page)
        vision.transcribe_page(b"hard-page", prompt_id="transcribe_page.v1")
        return [hard_block(page)]

    result = PdfConverter(
        hard_extractor=hard,
        image_stage=stage(vision, lambda _page, _number, _image, _dpi: png((80, 80))),
        page_pdf_factory=lambda _path, _page: b"%PDF-page",
    ).convert(source, tmp_path / "out", config=config())

    page = result.document.pages[0]
    assert hard_calls == [1]
    assert [block.type for block in page.blocks] == ["paragraph", "figure"]
    assert page.blocks[0].provenance.source == "vision"
    assert page.blocks[1].provenance.source == "vision"
    assert result.document.images[0].status == "described"
    assert vision.describe_calls == 1
    assert vision.transcribe_calls == 1


def test_scanned_full_page_image_uses_hard_path_once_without_image_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "scanned.pdf"
    source.write_bytes(image_pdf())
    monkeypatch.setattr(hybrid, "classify", decision_for("SCANNED"))
    vision = CountingVision()

    def fail_if_rendered(
        _page: object, _number: int, _image: dict[str, object], _dpi: int
    ) -> bytes:
        raise AssertionError("scanned page entered embedded image stage")

    result = PdfConverter(
        hard_extractor=lambda page, _pdf_page, _decision: (
            vision.transcribe_page(b"hard-page", prompt_id="transcribe_page.v1"),
            [hard_block(page)],
        )[1],
        image_stage=stage(vision, fail_if_rendered),
        page_pdf_factory=lambda _path, _page: b"%PDF-page",
    ).convert(source, config=config())

    assert result.document.pages[0].status == "ok"
    assert result.document.pages[0].page_class == "SCANNED"
    assert result.document.images == []
    assert vision.describe_calls == 0
    assert vision.transcribe_calls == 1


def test_hard_and_image_failures_stay_isolated_by_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "isolated.pdf"
    source.write_bytes(image_pdf(page_count=2))
    monkeypatch.setattr(hybrid, "classify", decision_for("COMPLEX"))
    vision = CountingVision()

    def hard(page: int, _pdf_page: object, _decision: RouteDecision) -> list[Block]:
        if page == 1:
            raise RuntimeError("hard page failed")
        vision.transcribe_page(b"hard-page", prompt_id="transcribe_page.v1")
        return [hard_block(page)]

    def broken_second_page(
        _page: object, page: int, _image: dict[str, object], _dpi: int
    ) -> bytes:
        if page == 2:
            raise RuntimeError("image crop failed")
        return png((80, 80))

    result = PdfConverter(
        hard_extractor=hard,
        image_stage=stage(vision, broken_second_page),
        page_pdf_factory=lambda _path, _page: b"%PDF-page",
    ).convert(source, config=config())

    assert result.document.pages[0].status == "failed"
    assert result.document.pages[1].status == "ok"
    assert result.document.images[0].status == "failed"
    assert vision.describe_calls == 0
