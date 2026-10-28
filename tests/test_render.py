import json
from datetime import datetime, timezone
from pathlib import Path

from doc2md.models import ConvertedDocument, PageResult, PageStat, RunStats, SourceInfo, ToolInfo
from doc2md.render.markdown import render_markdown
from doc2md.render.sidecar import write_document, write_run


def make_document() -> ConvertedDocument:
    from doc2md.models import Block, Provenance

    return ConvertedDocument(
        source=SourceInfo(name="sample.pdf", sha256="b" * 64, size_bytes=12, page_count=3),
        pipeline="tiered",
        pages=[
            PageResult(
                page=1,
                status="ok",
                page_class="TEXT",
                method="anydoc",
                blocks=[
                    Block(
                        block_id="p0001-b001",
                        type="table",
                        markdown=(
                            "| Kopf | Wert |\n| --- | --- |\n"
                            "| Straße | ![Figure](images/p0001-i01.png) |"
                        ),
                        text="Kopf Wert Straße",
                        provenance=Provenance(page=1, source="anydoc"),
                    )
                ],
                duration_s=0.1,
            ),
            PageResult(
                page=2,
                status="failed",
                page_class="COMPLEX",
                method=None,
                error="AnyDoc conversion failed",
                duration_s=0.2,
            ),
            PageResult(
                page=3,
                status="ok",
                page_class="TEXT",
                method="anydoc",
                duration_s=0.0,
            ),
        ],
        tool=ToolInfo(
            doc2md="0.1.0",
            pdfplumber="0.11.10",
            anydoc="0.2.4",
            backend="anydoc",
            config_hash="config-hash",
        ),
    )


def test_markdown_preserves_blocks_and_failed_page_placeholder() -> None:
    rendered = render_markdown(make_document())

    assert "| Straße | ![Figure](images/p0001-i01.png) |" in rendered
    assert "<!-- page: 2 failed: AnyDoc conversion failed -->" in rendered
    assert "<!-- page: 1 -->" not in rendered
    assert rendered.endswith("\n")


def test_markdown_markers_and_anchors_are_configurable() -> None:
    rendered = render_markdown(make_document(), page_markers=True, block_anchors=True)

    assert "<!-- page: 1 -->" in rendered
    assert "<!-- block: p0001-b001 -->" in rendered
    assert "<!-- page: 2 failed: AnyDoc conversion failed -->" in rendered


def test_sidecar_is_utf8_deterministic_and_valid_json(tmp_path: Path) -> None:
    document = make_document()
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    write_document(first, document)
    write_document(second, document)

    first_bytes = first.read_bytes()
    assert first_bytes == second.read_bytes()
    assert first_bytes.endswith(b"\n")
    assert b"Stra\xc3\x9fe" in first_bytes
    payload = json.loads(first_bytes)
    assert payload["pages"][0]["blocks"][0]["provenance"]["source"] == "anydoc"


def test_run_sidecar_contains_derived_page_and_cache_totals(tmp_path: Path) -> None:
    stats = RunStats(
        run_id="run-1",
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        finished_at=datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
        pipeline="tiered",
        source=SourceInfo(name="sample.pdf", sha256="b" * 64, size_bytes=12, page_count=1),
        config_hash="config-hash",
        wall_time_s=1.0,
        pages=[PageStat(page=1, status="ok", page_class="TEXT", method="anydoc", duration_s=1.0)],
        cache_hits=2,
        cache_misses=1,
    )
    path = tmp_path / "run.json"

    write_run(path, stats)
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["totals"]["pages"] == {
        "total": 1,
        "text": 1,
        "complex": 0,
        "scanned": 0,
        "failed": 0,
    }
    assert payload["totals"]["cache"] == {"hits": 2, "misses": 1}
