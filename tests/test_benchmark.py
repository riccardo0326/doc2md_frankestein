import csv
from datetime import datetime, timezone
from pathlib import Path

from doc2md.bench.runner import RESULTS_COLUMNS, BenchmarkRunner
from doc2md.bench.suite import load_suite
from doc2md.config import Config
from doc2md.models import (
    ConversionResult,
    ConvertedDocument,
    PageResult,
    PageStat,
    RunStats,
    SourceInfo,
    ToolInfo,
)


def suite_text() -> str:
    return """
[suite]
name = "fixture"
repetitions = 2
cold_cache = true

[[documents]]
id = "doc-a"
path = "a.pdf"
tags = ["digital", "en"]

[[documents]]
id = "doc-b"
path = "b.pdf"
tags = ["scanned"]

[[pipelines]]
name = "tiered"
[[pipelines]]
name = "full-vision"
[[pipelines]]
name = "baseline_current"
"""


def fake_result(source: Path, out_dir: Path, pipeline: str, config: Config) -> ConversionResult:
    out_dir.mkdir(parents=True, exist_ok=True)
    source_info = SourceInfo(name=source.name, sha256="a" * 64, size_bytes=1, page_count=1)
    page = PageResult(
        page=1,
        status="ok",
        page_class="TEXT",
        method="anydoc" if pipeline == "tiered" else "vision",
        duration_s=0.1,
    )
    stats = RunStats(
        run_id=f"{pipeline}-run",
        started_at=datetime(1970, 1, 1, tzinfo=timezone.utc),
        finished_at=datetime(1970, 1, 1, tzinfo=timezone.utc),
        pipeline=pipeline,
        source=source_info,
        config_hash="config",
        wall_time_s=0.1,
        pages=[
            PageStat(
                page=1,
                status="ok",
                page_class="TEXT",
                method=page.method,
                duration_s=0.1,
            )
        ],
    )
    document = ConvertedDocument(
        source=source_info,
        pipeline=pipeline,
        pages=[page],
        tool=ToolInfo(doc2md="0.1.0", pdfplumber="0.11", config_hash="config"),
    )
    return ConversionResult(
        document=document,
        markdown=f"{pipeline}\n",
        markdown_path=None,
        json_path=None,
        run_path=None,
        stats=stats,
    )


def test_suite_loader_and_exact_results_columns(tmp_path: Path) -> None:
    suite_path = tmp_path / "suite.toml"
    suite_path.write_text(suite_text(), encoding="utf-8")

    suite = load_suite(suite_path)

    assert suite.name == "fixture"
    assert suite.repetitions == 2
    assert [document.id for document in suite.documents] == ["doc-a", "doc-b"]
    assert RESULTS_COLUMNS == [
        "run_id", "doc_id", "pipeline", "rep", "pages_total", "pages_text",
        "pages_complex", "pages_scanned", "pages_failed", "images_found",
        "images_described", "images_skipped", "vision_calls", "input_tokens",
        "output_tokens", "total_tokens", "tokens_estimated", "docling_pages",
        "wall_time_s", "time_easy_pages_s", "time_hard_pages_s", "output_chars",
        "cache_hits", "error",
    ]


def test_runner_executes_matrix_and_skips_optional_baseline(tmp_path: Path) -> None:
    suite_path = tmp_path / "suite.toml"
    suite_path.write_text(suite_text(), encoding="utf-8")
    (tmp_path / "a.pdf").write_bytes(b"a")
    (tmp_path / "b.pdf").write_bytes(b"b")
    cache_dirs: list[Path] = []

    def conversion(
        source: Path,
        out_dir: Path,
        *,
        pipeline: str,
        config: Config,
        **kwargs: object,
    ) -> ConversionResult:
        cache_dirs.append(Path(config.cache.dir))
        return fake_result(source, out_dir, pipeline, config)

    run_dir = BenchmarkRunner(convert_fn=conversion).run(suite_path, tmp_path / "runs")
    with (run_dir / "results.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 12
    assert list(rows[0]) == RESULTS_COLUMNS
    assert sum(row["error"] == "baseline unavailable" for row in rows) == 4
    assert len(set(cache_dirs)) == 8
    assert (run_dir / "env.json").is_file()
    assert (run_dir / "outputs" / "doc-a" / "tiered" / "rep1").is_dir()
