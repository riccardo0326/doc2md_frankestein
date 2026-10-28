import json
from pathlib import Path

from doc2md.bench.judge import parse_judge_response
from doc2md.bench.review import (
    ReviewPage,
    build_blind_rows,
    render_report,
    select_pages,
    write_review_sheet,
)


def pages() -> list[ReviewPage]:
    return [
        ReviewPage("doc-a", 1, "TEXT", "", {"tiered": "a1", "full-vision": "a2"}),
        ReviewPage("doc-a", 2, "TEXT", "", {"tiered": "b1", "full-vision": "b2"}),
        ReviewPage("doc-b", 1, "COMPLEX", "", {"tiered": "c1", "full-vision": "c2"}),
        ReviewPage("doc-b", 2, "SCANNED", "", {"tiered": "d1", "full-vision": "d2"}),
    ]


def test_stratified_sampling_is_reproducible_and_has_no_duplicates() -> None:
    first = select_pages(pages(), n=3, seed=42)
    second = select_pages(pages(), n=3, seed=42)

    assert first == second
    assert len(first) == 3
    assert len({(page.doc_id, page.page) for page in first}) == 3
    assert {page.page_class for page in first} == {"TEXT", "COMPLEX", "SCANNED"}


def test_blind_sheet_hides_pipeline_names_and_unblinds_exactly(tmp_path: Path) -> None:
    rows, mapping = build_blind_rows(pages(), ["tiered", "full-vision"], seed=7)
    sheet, mapping_path = write_review_sheet(tmp_path, rows, mapping)

    content = sheet.read_text(encoding="utf-8")
    assert "tiered" not in content
    assert "full-vision" not in content
    assert mapping_path.is_file()
    loaded = json.loads(mapping_path.read_text(encoding="utf-8"))
    assert loaded == mapping
    assert rows[0]["output_A"] or rows[0]["output_B"]


def test_judge_parser_accepts_fenced_json_and_reports_malformed_output() -> None:
    valid = parse_judge_response("```json\n{\"text_fidelity\": 2}\n```")
    invalid = parse_judge_response("not json")

    assert valid.error is None
    assert valid.scores["text_fidelity"] == 2
    assert invalid.error is not None
    assert invalid.scores == {}


def test_report_has_pending_manual_state_and_judge_limitations(tmp_path: Path) -> None:
    results = tmp_path / "results.csv"
    results.write_text("run_id,doc_id,pipeline,error\nrun,doc-a,tiered,\n", encoding="utf-8")
    (tmp_path / "judge.json").write_text(
        json.dumps({"errors": [{"sample_id": "s1", "error": "unavailable"}]}),
        encoding="utf-8",
    )

    report = render_report(tmp_path)
    text = report.read_text(encoding="utf-8")

    assert "manual review: pending" in text
    assert "Judge limitations" in text
    assert "baseline_current" in text
