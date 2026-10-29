from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from typer.testing import CliRunner

from doc2md import api
from doc2md.cli import app
from doc2md.config import CacheConfig, Config, ImageConfig, VisionConfig
from doc2md.converters.pdf import hybrid
from doc2md.converters.pdf.images import ImageStage
from doc2md.models import Block, Provenance, RouteDecision
from doc2md.vision.base import VisionResult
from doc2md.vision.fake import FakeVisionBackend


def png(size: tuple[int, int]) -> bytes:
    image = Image.new("RGB", size, "purple")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def image_pdf() -> bytes:
    raw_image = bytes([120, 30, 160]) * (80 * 80)
    content = (
        b"BT /F1 12 Tf 72 720 Td "
        b"(Public runtime text has enough content for routing.) Tj ET "
        b"q 80 0 0 80 72 600 cm /Im1 Do Q"
    )
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> /XObject << /Im1 5 0 R >> >> "
            b"/Contents 6 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        (
            f"<< /Type /XObject /Subtype /Image /Width 80 /Height 80 "
            f"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Length {len(raw_image)} >>\n"
            "stream\n"
        ).encode()
        + raw_image
        + b"\nendstream",
        (
            f"<< /Length {len(content)} >>\nstream\n".encode()
            + content
            + b"\nendstream"
        ),
    ]
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


class FakeFast:
    def extract(self, _page_pdf: bytes, *, page: int) -> Block:
        text = f"AnyDoc page {page}"
        return Block(
            block_id=f"p{page:04d}-b001",
            type="paragraph",
            markdown=text,
            text=text,
            provenance=Provenance(page=page, source="anydoc"),
        )


class CountingVision(FakeVisionBackend):
    def __init__(self, *, fail: bool = False) -> None:
        super().__init__(fail=fail)
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


def config() -> Config:
    return Config(
        vision=VisionConfig(backend="fake"),
        images=ImageConfig(min_width_px=64, min_height_px=64, min_area_px=100),
        cache=CacheConfig(enabled=False),
    )


def install_fake_runtime(monkeypatch: pytest.MonkeyPatch, vision: CountingVision) -> None:
    import doc2md.runtime as runtime

    monkeypatch.setattr(hybrid, "_slice_page", lambda _source, page: f"%PDF-page-{page}".encode())
    monkeypatch.setattr(runtime, "AnyDocFastExtractor", lambda: FakeFast())
    monkeypatch.setattr(runtime, "FakeVisionBackend", lambda: vision)
    monkeypatch.setattr(
        runtime,
        "ImageStage",
        lambda image_config, **kwargs: ImageStage(
            image_config,
            backend=kwargs["backend"],
            renderer=lambda _page, _number, _image, _dpi: png((128, 128)),
        ),
    )


def test_api_default_runtime_wires_images_and_figures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "public.pdf"
    source.write_bytes(image_pdf())
    vision = CountingVision()
    install_fake_runtime(monkeypatch, vision)

    result = api.convert(source, tmp_path / "out", config=config())

    assert result.document.images[0].status == "described"
    assert [block.type for block in result.document.pages[0].blocks] == ["paragraph", "figure"]
    assert vision.describe_calls == 1


def test_api_default_runtime_uses_hard_adapter_and_excludes_scanned_images(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "hard.pdf"
    source.write_bytes(image_pdf())
    vision = CountingVision()
    install_fake_runtime(monkeypatch, vision)
    monkeypatch.setattr(
        hybrid,
        "classify",
        lambda signals, router, page: RouteDecision(
            page=page, page_class="SCANNED", signals=signals
        ),
    )

    result = api.convert(source, config=config())

    assert result.document.pages[0].status == "ok"
    assert result.document.pages[0].method == "vision"
    assert result.document.images == []
    assert vision.transcribe_calls == 1
    assert vision.describe_calls == 0


def test_api_default_runtime_isolates_unavailable_vision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "unavailable.pdf"
    source.write_bytes(image_pdf())
    vision = CountingVision(fail=True)
    install_fake_runtime(monkeypatch, vision)

    result = api.convert(source, config=config())

    assert result.document.pages[0].status == "ok"
    assert result.document.images[0].status == "failed"
    assert vision.describe_calls == 1


def test_cli_uses_public_runtime_and_reports_output_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "cli.pdf"
    source.write_bytes(image_pdf())
    output = tmp_path / "out"
    vision = CountingVision()
    install_fake_runtime(monkeypatch, vision)

    result = CliRunner().invoke(
        app,
        ["convert", str(source), "--out", str(output)],
    )

    document_dir = output / "cli"
    assert result.exit_code == 0, result.stdout
    assert result.stdout.strip() == str(document_dir / "cli.md")
    assert (document_dir / "cli.json").is_file()
    assert (document_dir / "images" / "p0001-i01.png").is_file()


def test_comparison_pipelines_do_not_process_embedded_images(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "comparison.pdf"
    source.write_bytes(image_pdf())
    vision = CountingVision()
    install_fake_runtime(monkeypatch, vision)

    full_vision = api.convert(source, pipeline="full-vision", config=config())
    docling_only = api.convert(source, pipeline="docling-only", config=config())

    assert full_vision.document.images == []
    assert docling_only.document.images == []
    assert vision.describe_calls == 0
