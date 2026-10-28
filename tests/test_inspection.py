from pathlib import Path

from typer.testing import CliRunner

import doc2md.cli as cli
from doc2md.cli import app
from doc2md.models import PageSignals, RouteDecision


def decisions() -> list[RouteDecision]:
    return [
        RouteDecision(
            page=1,
            page_class="TEXT",
            reasons=[],
            signals=PageSignals(
                chars=12,
                words=3,
                image_area_ratio=0.0,
                image_count=0,
                table_count=0,
                table_irregular=False,
                garbled_ratio=0.0,
                has_text_layer=True,
            ),
        )
    ]


def test_inspect_cli_output_is_stable(monkeypatch: object, tmp_path: Path) -> None:
    monkeypatch.setattr(cli, "inspect_pdf", lambda source, config=None: decisions())
    source = tmp_path / "sample.pdf"
    source.write_bytes(b"%PDF-test")

    result = CliRunner().invoke(app, ["inspect", str(source)])

    assert result.exit_code == 0
    assert result.stdout == (
        "page class chars images tables garbled text_layer reasons\n"
        "1 TEXT 12 0 0 0.0000 yes -\n"
    )


def test_inspect_cli_json_output(monkeypatch: object, tmp_path: Path) -> None:
    monkeypatch.setattr(cli, "inspect_pdf", lambda source, config=None: decisions())
    source = tmp_path / "sample.pdf"
    source.write_bytes(b"%PDF-test")

    result = CliRunner().invoke(app, ["inspect", str(source), "--json"])

    assert result.exit_code == 0
    assert '"page": 1' in result.stdout
    assert '"page_class": "TEXT"' in result.stdout
