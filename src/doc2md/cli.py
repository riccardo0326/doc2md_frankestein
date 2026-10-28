from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import typer

from .api import convert as convert_pdf
from .api import inspect_pdf
from .bench.review import build_review_sheet, render_report
from .bench.runner import BenchmarkRunner
from .config import Config, RouterConfig
from .models import RouteDecision

app = typer.Typer(add_completion=False, no_args_is_help=True)
bench_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(bench_app, name="bench")


@app.callback()
def _root() -> None:
    """Inspect PDF routing signals."""


def _config_with_min_chars(min_chars: int | None) -> Config | None:
    if min_chars is None:
        return None
    return Config(router=RouterConfig(min_chars=min_chars))


def _format_decisions(decisions: list[RouteDecision]) -> str:
    lines = ["page class chars images tables garbled text_layer reasons"]
    for decision in decisions:
        signals = decision.signals
        reasons = ";".join(decision.reasons) if decision.reasons else "-"
        text_layer = "yes" if signals.has_text_layer else "no"
        lines.append(
            f"{decision.page} {decision.page_class} {signals.chars} "
            f"{signals.image_count} {signals.table_count} {signals.garbled_ratio:.4f} "
            f"{text_layer} {reasons}"
        )
    return "\n".join(lines) + "\n"


@app.command("inspect")
def inspect_command(
    source: Path = typer.Argument(..., exists=True, readable=True),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
    min_chars: int | None = typer.Option(None, min=0, help="Override router.min_chars."),
) -> None:
    decisions = inspect_pdf(source, config=_config_with_min_chars(min_chars))
    if json_output:
        payload = [decision.model_dump(mode="json") for decision in decisions]
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        typer.echo(_format_decisions(decisions), nl=False)


@app.command("convert")
def convert_command(
    source: Path = typer.Argument(..., exists=True, readable=True),
    out_dir: Path = typer.Option(Path("out"), "--out", "-o"),
    strict: bool = typer.Option(False, "--strict", help="Fail if any page fails."),
    no_cache: bool = typer.Option(False, "--no-cache", help="Disable the disk cache."),
    pipeline: Literal["tiered", "full-vision", "docling-only"] = typer.Option(
        "tiered", "--pipeline", help="Conversion comparison pipeline."
    ),
) -> None:
    result = convert_pdf(
        source,
        out_dir,
        strict=strict,
        no_cache=no_cache,
        pipeline=pipeline,
    )
    if result.markdown_path is not None:
        typer.echo(str(result.markdown_path))


@bench_app.command("run")
def benchmark_run_command(
    suite: Path = typer.Option(..., "--suite", exists=True, readable=True),
    out_dir: Path = typer.Option(Path("bench_runs"), "--out"),
    pipelines: str | None = typer.Option(
        None, "--pipelines", help="Comma-separated pipeline names."
    ),
) -> None:
    selected = [item.strip() for item in pipelines.split(",")] if pipelines else None
    run_dir = BenchmarkRunner().run(suite, out_dir, pipelines=selected)
    typer.echo(str(run_dir))


@bench_app.command("review-sheet")
def benchmark_review_sheet_command(
    run_dir: Path = typer.Argument(..., exists=True, file_okay=False),
    sample_size: int = typer.Option(30, "--n", min=1),
    seed: int = typer.Option(42, "--seed"),
) -> None:
    sheet, _mapping = build_review_sheet(run_dir, sample_size, seed)
    typer.echo(str(sheet))


@bench_app.command("judge")
def benchmark_judge_command(
    run_dir: Path = typer.Argument(..., exists=True, file_okay=False),
) -> None:
    judge_path = run_dir / "judge.json"
    judge_path.write_text(
        json.dumps(
            {"errors": [{"error": "judge backend requires approved Kelpie configuration"}]},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    typer.echo(str(judge_path))


@bench_app.command("report")
def benchmark_report_command(
    run_dir: Path = typer.Argument(..., exists=True, file_okay=False),
) -> None:
    typer.echo(str(render_report(run_dir)))


def main() -> None:
    app()
