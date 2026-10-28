import sys

import pytest

from doc2md.converters.pdf.anydoc import AnyDocFastExtractor
from doc2md.errors import HardPathHandoffError, OptionalDependencyError, PageExtractionError


class FakeNeedsOcrError(Exception):
    __name__ = "NeedsOcrError"


class FakeBinding:
    NeedsOcrError = FakeNeedsOcrError

    def __init__(self, markdown: str = "# Heading\n") -> None:
        self.markdown = markdown
        self.calls: list[dict[str, object]] = []

    def to_markdown_bytes(
        self,
        data: bytes,
        format: str,
        *,
        ocr: str,
    ) -> str:
        self.calls.append({"data": data, "format": format, "ocr": ocr})
        return self.markdown


def test_fake_binding_returns_one_block_with_original_page() -> None:
    binding = FakeBinding("# Heading\n\n| A | B |\n")
    extractor = AnyDocFastExtractor(binding=binding)

    block = extractor.extract(b"%PDF-test", page=7)

    assert block.block_id == "p0007-b001"
    assert block.type == "other"
    assert block.markdown == "# Heading\n\n| A | B |\n"
    assert block.text == block.markdown
    assert block.provenance.page == 7
    assert block.provenance.source == "anydoc"
    assert binding.calls == [{"data": b"%PDF-test", "format": "pdf", "ocr": "reject"}]


def test_empty_markdown_is_a_typed_page_error() -> None:
    extractor = AnyDocFastExtractor(binding=FakeBinding(" \n"))

    with pytest.raises(PageExtractionError, match="empty Markdown"):
        extractor.extract(b"%PDF-test", page=1)


def test_ocr_response_is_a_hard_path_handoff() -> None:
    class OcrBinding(FakeBinding):
        def to_markdown_bytes(self, data: bytes, format: str, *, ocr: str) -> str:
            raise self.NeedsOcrError("page needs OCR")

    extractor = AnyDocFastExtractor(binding=OcrBinding())

    with pytest.raises(HardPathHandoffError, match="hard path"):
        extractor.extract(b"%PDF-test", page=2)


def test_invalid_page_pdf_is_rejected_before_binding() -> None:
    binding = FakeBinding()
    extractor = AnyDocFastExtractor(binding=binding)

    with pytest.raises(PageExtractionError, match="one-page PDF"):
        extractor.extract(b"not a PDF", page=1)
    assert binding.calls == []


def test_missing_anydoc_is_a_clear_optional_dependency_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "anydoc", None)
    extractor = AnyDocFastExtractor()

    with pytest.raises(OptionalDependencyError, match="firecrawl-anydoc"):
        extractor.extract(b"%PDF-test", page=1)
