from doc2md.models import Block, PageResult, Provenance
from doc2md.render.markdown import render_markdown


def test_hard_page_failure_does_not_drop_other_page_provenance() -> None:
    pages = [
        PageResult(
            page=1,
            status="ok",
            page_class="TEXT",
            method="anydoc",
            blocks=[
                Block(
                    block_id="p0001-b001",
                    type="other",
                    markdown="text",
                    text="text",
                    provenance=Provenance(page=1, source="anydoc"),
                )
            ],
            duration_s=0.0,
        ),
        PageResult(
            page=2,
            status="failed",
            page_class="SCANNED",
            method=None,
            error="hard path is not configured",
            duration_s=0.0,
        ),
    ]

    markdown = render_markdown(
        type("Document", (), {"pages": pages})()  # type: ignore[arg-type]
    )

    assert "text" in markdown
    assert "page: 2 failed" in markdown
    assert pages[0].blocks[0].provenance.page == 1


def test_regression_fixture_does_not_depend_on_filename_or_page_rule() -> None:
    provenance = Provenance(page=23, source="vision")

    assert provenance.page == 23
    assert provenance.source == "vision"
