from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path

RUBRIC_CRITERIA = (
    "text_fidelity",
    "special_characters",
    "table_fidelity",
    "figure_usefulness",
    "reading_order",
)


@dataclass(frozen=True)
class ReviewPage:
    doc_id: str
    page: int
    page_class: str
    page_image_path: str
    outputs: dict[str, str]


def load_review_pages(run_dir: str | Path) -> list[ReviewPage]:
    outputs_dir = Path(run_dir) / "outputs"
    pages: dict[tuple[str, int], ReviewPage] = {}
    for sidecar in outputs_dir.glob("*/*/rep*/*.json"):
        if sidecar.name == "run.json":
            continue
        pipeline = sidecar.parents[1].name
        doc_id = sidecar.parents[2].name
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        for page in payload.get("pages", []):
            key = (doc_id, int(page["page"]))
            blocks = "\n\n".join(block.get("markdown", "") for block in page.get("blocks", []))
            existing = pages.get(key)
            if existing is None:
                existing = ReviewPage(doc_id, key[1], page["page_class"], "", {})
            pages[key] = ReviewPage(
                existing.doc_id,
                existing.page,
                existing.page_class,
                existing.page_image_path,
                {**existing.outputs, pipeline: blocks},
            )
    return sorted(pages.values(), key=lambda page: (page.doc_id, page.page))


def select_pages(pages: list[ReviewPage], n: int, seed: int) -> list[ReviewPage]:
    if n <= 0:
        return []
    rng = random.Random(seed)
    groups: dict[str, list[ReviewPage]] = {}
    for page in pages:
        groups.setdefault(page.page_class, []).append(page)
    for group in groups.values():
        rng.shuffle(group)
    selected: list[ReviewPage] = []
    group_names = sorted(groups)
    while len(selected) < min(n, len(pages)):
        added = False
        for name in group_names:
            if groups[name] and len(selected) < n:
                selected.append(groups[name].pop())
                added = True
        if not added:
            break
    return selected


def build_blind_rows(
    pages: list[ReviewPage], pipelines: list[str], seed: int
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    rows: list[dict[str, str]] = []
    mapping: dict[str, dict[str, str]] = {}
    labels = [chr(ord("A") + index) for index in range(len(pipelines))]
    for index, page in enumerate(pages, start=1):
        shuffled = list(pipelines)
        random.Random(seed + index).shuffle(shuffled)
        label_map = dict(zip(labels, shuffled, strict=True))
        sample_id = f"s{index:04d}"
        mapping[sample_id] = label_map
        row: dict[str, str] = {
            "sample_id": sample_id,
            "doc_id": page.doc_id,
            "page": str(page.page),
            "page_class": page.page_class,
            "page_image_path": page.page_image_path,
        }
        for label, pipeline in label_map.items():
            row[f"output_{label}"] = page.outputs.get(pipeline, "")
            for criterion in RUBRIC_CRITERIA:
                row[f"{criterion}_{label}_score"] = ""
        rows.append(row)
    return rows, mapping


def write_review_sheet(
    directory: str | Path,
    rows: list[dict[str, str]],
    mapping: dict[str, dict[str, str]],
) -> tuple[Path, Path]:
    directory_path = Path(directory)
    directory_path.mkdir(parents=True, exist_ok=True)
    sheet = directory_path / "review_sheet.csv"
    mapping_path = directory_path / "unblind_map.json"
    fieldnames = list(rows[0]) if rows else ["sample_id"]
    with sheet.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    mapping_path.write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return sheet, mapping_path


def build_review_sheet(run_dir: str | Path, n: int = 30, seed: int = 42) -> tuple[Path, Path]:
    pages = load_review_pages(run_dir)
    pipelines = sorted({pipeline for page in pages for pipeline in page.outputs})
    selected = select_pages(pages, n, seed)
    rows, mapping = build_blind_rows(selected, pipelines, seed)
    return write_review_sheet(Path(run_dir) / "review", rows, mapping)


def render_report(run_dir: str | Path) -> Path:
    directory = Path(run_dir)
    results_exists = (directory / "results.csv").is_file()
    judge_exists = (directory / "judge.json").is_file()
    baseline_present = False
    if results_exists:
        with (directory / "results.csv").open(encoding="utf-8") as handle:
            baseline_present = any(
                row.get("pipeline") == "baseline_current" for row in csv.DictReader(handle)
            )
    lines = [
        "# Quality Review Report",
        "",
        "- manual review: pending",
        f"- baseline_current data: {'available' if baseline_present else 'missing'}",
        "",
        "## Judge limitations",
        "",
        "The optional judge uses an approved remote model and may introduce model/style bias.",
        "Judge scores are not a substitute for human review and may be unavailable.",
        f"Judge result file present: {'yes' if judge_exists else 'no'}.",
        "",
    ]
    report = directory / "report.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    return report
