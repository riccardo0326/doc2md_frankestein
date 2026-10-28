from pathlib import Path

import pytest

from doc2md.converters.pdf.hard import KelpieHardExtractor
from doc2md.errors import HardExtractionError
from doc2md.vision.fake import FakeVisionBackend


def test_fake_backend_transcribes_markdown_structures_into_blocks() -> None:
    markdown = (
        "# Heading\n\n"
        "A paragraph with German Straße.\n\n"
        "- first\n- second\n\n"
        "| A | B |\n| --- | --- |\n| 1 | 2 |\n"
    )
    backend = FakeVisionBackend(transcription=markdown)
    extractor = KelpieHardExtractor(
        backend,
        page_dpi=120,
        prompt_id="transcribe_page.v1",
        renderer=lambda source, page, dpi: b"synthetic-page",
    )

    blocks = extractor.extract(Path("synthetic.pdf"), [4])[4]
    calls = extractor.drain_calls()

    assert [block.type for block in blocks] == ["heading", "paragraph", "list", "table"]
    assert blocks[0].block_id == "p0004-b001"
    assert blocks[0].provenance.page == 4
    assert blocks[0].provenance.source == "vision"
    assert blocks[3].meta == {"table_rows": 2, "table_cols": 2}
    assert calls[0][0] == "p0004"
    assert calls[0][1].usage.total_tokens > 0
    assert calls[0][1].latency_s == 0.0


def test_hard_extractor_renders_only_selected_original_pages() -> None:
    rendered: list[tuple[Path, int, int]] = []
    backend = FakeVisionBackend(transcription="text")

    def renderer(source: Path, page: int, dpi: int) -> bytes:
        rendered.append((source, page, dpi))
        return f"page-{page}".encode()

    extractor = KelpieHardExtractor(backend, page_dpi=200, prompt_id="prompt", renderer=renderer)

    extracted = extractor.extract(Path("input.pdf"), [5, 2, 5])

    assert sorted(extracted) == [2, 5]
    assert rendered == [(Path("input.pdf"), 2, 200), (Path("input.pdf"), 5, 200)]


@pytest.mark.parametrize("text", ["", "   \n"])
def test_empty_transcription_fails_the_affected_page(text: str) -> None:
    extractor = KelpieHardExtractor(
        FakeVisionBackend(transcription=text),
        page_dpi=120,
        prompt_id="prompt",
        renderer=lambda source, page, dpi: b"page",
    )

    with pytest.raises(HardExtractionError, match="no transcribed content"):
        extractor.extract(Path("input.pdf"), [1])


def test_backend_failure_is_typed_and_isolated_to_call() -> None:
    backend = FakeVisionBackend(fail=True)
    extractor = KelpieHardExtractor(
        backend,
        page_dpi=120,
        prompt_id="prompt",
        renderer=lambda source, page, dpi: b"page",
    )

    with pytest.raises(HardExtractionError, match="Kelpie hard transcription failed"):
        extractor.extract(Path("input.pdf"), [2])
