from math import nan

import pytest
from pydantic import ValidationError

from doc2md.models import (
    BBox,
    Block,
    ConvertedDocument,
    PageResult,
    Provenance,
    SourceInfo,
    ToolInfo,
)


def make_tool() -> ToolInfo:
    return ToolInfo(
        doc2md="0.1.0",
        pdfplumber="0.11.10",
        anydoc="0.2.4",
        backend="anydoc",
        config_hash="config-hash",
    )


def make_document() -> ConvertedDocument:
    block = Block(
        block_id="p0001-b001",
        type="paragraph",
        markdown="Straße",
        text="Straße",
        provenance=Provenance(page=1, source="anydoc", bbox=BBox(x0=0, y0=0, x1=10, y1=10)),
    )
    return ConvertedDocument(
        source=SourceInfo(name="sample.pdf", sha256="a" * 64, size_bytes=10, page_count=1),
        pipeline="tiered",
        pages=[
            PageResult(
                page=1,
                status="ok",
                page_class="TEXT",
                method="anydoc",
                blocks=[block],
                duration_s=0.1,
            )
        ],
        tool=make_tool(),
    )


def test_anydoc_provenance_is_frozen_and_serialisable() -> None:
    document = make_document()

    assert document.pages[0].blocks[0].provenance.source == "anydoc"
    assert document.model_dump(mode="json")["pages"][0]["method"] == "anydoc"
    with pytest.raises(ValidationError):
        document.pages[0].blocks[0].provenance = Provenance(page=1, source="vision")


def test_page_numbers_and_finite_durations_are_validated() -> None:
    with pytest.raises(ValidationError):
        Provenance(page=0, source="anydoc")
    with pytest.raises(ValidationError):
        PageResult(
            page=1,
            status="failed",
            page_class="TEXT",
            method=None,
            duration_s=nan,
        )
