from __future__ import annotations

from datetime import datetime
from threading import Lock

from .models import CallStat, PageStat, RunStats, SourceInfo
from .vision.base import VisionResult


class MetricsCollector:
    """Run-local collector whose token totals derive from call records."""

    def __init__(self) -> None:
        self._lock = Lock()
        self.pages: list[PageStat] = []
        self.calls: list[CallStat] = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.warnings: list[str] = []

    def record_page(self, page: PageStat) -> None:
        with self._lock:
            self.pages.append(page)

    def record_call(self, kind: str, identifier: str, result: VisionResult) -> None:
        with self._lock:
            self.calls.append(
                CallStat(
                    kind=kind,  # type: ignore[arg-type]
                    id=identifier,
                    model=result.model,
                    latency_s=result.latency_s,
                    input_tokens=result.usage.input_tokens,
                    output_tokens=result.usage.output_tokens,
                    total_tokens=result.usage.total_tokens,
                    estimated=result.usage.estimated,
                    cache_hit=False,
                )
            )

    def record_cache(self, *, hit: bool) -> None:
        with self._lock:
            if hit:
                self.cache_hits += 1
            else:
                self.cache_misses += 1

    def add_warning(self, warning: str) -> None:
        with self._lock:
            self.warnings.append(warning)

    def snapshot(
        self,
        *,
        run_id: str,
        started_at: datetime,
        finished_at: datetime,
        pipeline: str,
        source: SourceInfo,
        config_hash: str,
        wall_time_s: float = 0.0,
    ) -> RunStats:
        with self._lock:
            calls = list(self.calls)
            pages = sorted(self.pages, key=lambda page: page.page)
            warnings = list(self.warnings)
            cache_hits = self.cache_hits
            cache_misses = self.cache_misses
        input_tokens = sum(call.input_tokens for call in calls)
        output_tokens = sum(call.output_tokens for call in calls)
        total_tokens = sum(call.total_tokens for call in calls)
        return RunStats(
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            pipeline=pipeline,
            source=source,
            config_hash=config_hash,
            wall_time_s=wall_time_s,
            pages=pages,
            pages_failed=sum(page.status == "failed" for page in pages),
            vision_calls=len(calls),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            tokens_estimated=any(call.estimated for call in calls),
            calls=calls,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            warnings=warnings,
        )
