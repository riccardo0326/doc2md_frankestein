from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ..models import Usage


class BaselineResult:
    def __init__(
        self,
        markdown_path: Path,
        wall_time_s: float,
        usage: Usage | None,
        pages: int | None,
    ) -> None:
        self.markdown_path = markdown_path
        self.wall_time_s = wall_time_s
        self.usage = usage
        self.pages = pages


class BaselineAdapter(Protocol):
    def run(self, source: Path, out_dir: Path) -> BaselineResult: ...


class FakeBaselineAdapter:
    def run(self, source: Path, out_dir: Path) -> BaselineResult:
        output = out_dir / f"{source.stem}.baseline.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("fake current-system baseline\n", encoding="utf-8")
        return BaselineResult(output, 0.0, None, None)
