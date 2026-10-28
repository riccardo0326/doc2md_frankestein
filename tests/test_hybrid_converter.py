import json
from pathlib import Path

import pytest

from doc2md.config import CacheConfig, Config, FastConfig
from doc2md.converters.pdf import PdfConverter
from doc2md.errors import ConversionFailed, PageExtractionError
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


def anydoc_block(page: int, text: str = "AnyDoc text") -> Block:
    return Block(
        block_id=f"p{page:04d}-b001",
        type="other",
        markdown=text,
        text=text,
        provenance=Provenance(page=page, source="anydoc"),
    )


class FakeFast:
    def __init__(self) -> None:
        self.pages: list[int] = []

    def extract(self, page_pdf: bytes, *, page: int) -> Block:
        self.pages.append(page)
        return anydoc_block(page, f"AnyDoc page {page}")


def test_mixed_conversion_routes_text_and_isolates_hard_page(tmp_path: Path) -> None:
    source = tmp_path / "mixed.pdf"
    source.write_bytes(synthetic_pdf())
    fast = FakeFast()
    converter = PdfConverter(
        fast_extractor=fast,
        page_pdf_factory=lambda path, page: f"%PDF-page-{page}".encode(),
    )

    result = converter.convert(
        source,
        out_dir=tmp_path / "out",
        config=Config(cache=CacheConfig(enabled=False)),
    )

    assert fast.pages == [1]
    assert [page.page for page in result.document.pages] == [1, 2]
    assert result.document.pages[0].method == "anydoc"
    assert result.document.pages[1].status == "failed"
    assert "hard path" in (result.document.pages[1].error or "")
    assert "AnyDoc page 1" in result.markdown
    assert "page: 2 failed" in result.markdown
    assert result.json_path is not None and result.json_path.is_file()
    assert result.markdown_path is not None and result.markdown_path.is_file()


def test_anydoc_failure_uses_only_configured_fallback(tmp_path: Path) -> None:
    source = tmp_path / "text.pdf"
    source.write_bytes(synthetic_pdf())

    class FailingFast(FakeFast):
        def extract(self, page_pdf: bytes, *, page: int) -> Block:
            self.pages.append(page)
            raise PageExtractionError("binding unavailable")

    fallback_calls: list[int] = []

    def fallback(page_number: int, page: object) -> list[Block]:
        fallback_calls.append(page_number)
        return [
            Block(
                block_id=f"p{page_number:04d}-b001",
                type="paragraph",
                markdown="fallback",
                text="fallback",
                provenance=Provenance(page=page_number, source="pdfplumber"),
            )
        ]

    converter = PdfConverter(
        fast_extractor=FailingFast(),
        fallback_extractor=fallback,
        page_pdf_factory=lambda path, page: b"%PDF-page",
    )
    result = converter.convert(
        source,
        config=Config(
            fast=FastConfig(fallback="pdfplumber"),
            cache=CacheConfig(enabled=False),
        ),
        out_dir=tmp_path / "out",
    )

    assert fallback_calls == [1]
    page = result.document.pages[0]
    assert page.method == "pdfplumber"
    assert any("fallback" in warning for warning in page.warnings)
    assert "fallback" in result.markdown
    assert result.json_path is not None
    sidecar = json.loads(result.json_path.read_text(encoding="utf-8"))
    assert any("fallback" in warning for warning in sidecar["pages"][0]["warnings"])


def test_strict_mode_raises_after_page_isolation(tmp_path: Path) -> None:
    source = tmp_path / "mixed.pdf"
    source.write_bytes(synthetic_pdf())
    converter = PdfConverter(
        fast_extractor=FakeFast(),
        page_pdf_factory=lambda path, page: b"%PDF-page",
    )

    with pytest.raises(ConversionFailed, match="failed"):
        converter.convert(source, strict=True, config=Config(cache=CacheConfig(enabled=False)))


def test_selected_pages_remain_original_and_outputs_are_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "mixed.pdf"
    source.write_bytes(synthetic_pdf())
    converter = PdfConverter(
        fast_extractor=FakeFast(),
        page_pdf_factory=lambda path, page: b"%PDF-page",
    )

    config = Config(cache=CacheConfig(enabled=False))
    first = converter.convert(source, pages=(2,), config=config)
    second = converter.convert(source, pages=(2,), config=config)

    assert [page.page for page in first.document.pages] == [1, 2]
    assert first.document.pages[0].status == "skipped"
    assert first.document.pages[1].page == 2
    assert first.markdown == second.markdown
    assert first.document.model_dump(mode="json") == second.document.model_dump(mode="json")


def test_second_run_uses_cache_without_repeating_anydoc(tmp_path: Path) -> None:
    source = tmp_path / "text.pdf"
    source.write_bytes(synthetic_pdf())
    fast = FakeFast()
    converter = PdfConverter(
        fast_extractor=fast,
        page_pdf_factory=lambda path, page: b"%PDF-page",
    )
    config = Config(cache=CacheConfig(dir=str(tmp_path / "cache")))

    converter.convert(source, config=config)
    converter.convert(source, config=config)

    assert fast.pages == [1]
