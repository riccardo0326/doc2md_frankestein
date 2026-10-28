from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PipelineName = Literal["tiered", "full-vision", "docling-only", "baseline_current"]


class SuiteDocument(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    path: str
    tags: list[str] = Field(default_factory=list)


class SuitePipeline(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: PipelineName


class BenchmarkSuite(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    repetitions: int = Field(default=1, ge=1)
    cold_cache: bool = True
    documents: list[SuiteDocument]
    pipelines: list[SuitePipeline]
    source_path: Path


def load_suite(path: str | Path) -> BenchmarkSuite:
    suite_path = Path(path)
    try:
        with suite_path.open("rb") as handle:
            raw = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"unable to read benchmark suite {suite_path}: {exc}") from exc
    suite = raw.get("suite", {})
    documents = raw.get("documents", [])
    pipelines = raw.get("pipelines", [])
    if (
        not isinstance(suite, dict)
        or not isinstance(documents, list)
        or not isinstance(pipelines, list)
    ):
        raise ValueError("benchmark suite requires suite, documents, and pipelines tables")
    return BenchmarkSuite(
        name=suite.get("name", suite_path.stem),
        repetitions=suite.get("repetitions", 1),
        cold_cache=suite.get("cold_cache", True),
        documents=documents,
        pipelines=pipelines,
        source_path=suite_path,
    )
