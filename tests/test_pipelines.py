from pathlib import Path

import pytest

from doc2md.config import CacheConfig, Config
from doc2md.converters.pdf import PdfConverter
from doc2md.errors import ConfigError
from doc2md.models import Block, Provenance


def synthetic_pdf() -> bytes:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 6 0 R >>"
        ),
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << >> /Contents 7 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        (
            b"<< /Length 78 >>\nstream\nBT /F1 12 Tf 72 720 Td "
            b"(Digital text page with enough text) Tj ET\nendstream"
        ),
        b"<< /Length 0 >>\nstream\n\nendstream",
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


def block(page: int, source: str, text: str) -> Block:
    return Block(
        block_id=f"p{page:04d}-b001",
        type="paragraph",
        markdown=text,
        text=text,
        provenance=Provenance(page=page, source=source),
    )


def test_full_vision_routes_every_selected_page_without_fast_or_images(tmp_path: Path) -> None:
    source = tmp_path / "sample.pdf"
    source.write_bytes(synthetic_pdf())
    vision_calls: list[int] = []
    fast_calls: list[int] = []

    converter = PdfConverter(
        fast_extractor=lambda data, page: fast_calls.append(page) or block(page, "anydoc", "fast"),
        vision_extractor=lambda page, pdf_page: vision_calls.append(page) or [
            block(page, "vision", f"vision-{page}")
        ],
        page_pdf_factory=lambda path, page: b"%PDF-page",
    )

    result = converter.convert(
        source,
        pipeline="full-vision",
        config=Config(cache=CacheConfig(enabled=False)),
    )

    assert vision_calls == [1, 2]
    assert fast_calls == []
    assert result.document.pipeline == "full-vision"
    assert [page.method for page in result.document.pages] == ["vision", "vision"]


def test_docling_only_routes_every_page_to_the_development_hard_seam(tmp_path: Path) -> None:
    source = tmp_path / "sample.pdf"
    source.write_bytes(synthetic_pdf())
    hard_calls: list[int] = []

    converter = PdfConverter(
        hard_extractor=lambda page, pdf_page, decision: hard_calls.append(page)
        or [block(page, "docling", f"hard-{page}")],
        vision_extractor=lambda page, pdf_page: pytest.fail("vision was called"),
        fast_extractor=lambda data, page: pytest.fail("fast was called"),
        page_pdf_factory=lambda path, page: b"%PDF-page",
    )

    result = converter.convert(
        source,
        pipeline="docling-only",
        config=Config(cache=CacheConfig(enabled=False)),
    )

    assert hard_calls == [1, 2]
    assert result.document.pipeline == "docling-only"
    assert [page.method for page in result.document.pages] == ["docling", "docling"]


def test_invalid_pipeline_name_is_a_configuration_error(tmp_path: Path) -> None:
    source = tmp_path / "sample.pdf"
    source.write_bytes(synthetic_pdf())

    with pytest.raises(ConfigError, match="unknown pipeline"):
        PdfConverter().convert(source, pipeline="not-a-pipeline")
