from datetime import datetime, timezone

from doc2md.metrics import MetricsCollector
from doc2md.models import SourceInfo, Usage
from doc2md.vision.base import VisionResult


def test_metrics_totals_are_derived_from_non_cached_call_records() -> None:
    collector = MetricsCollector()
    collector.record_call(
        "describe_image",
        "p0001-i01",
        VisionResult(
            text="one",
            usage=Usage(input_tokens=10, output_tokens=3, total_tokens=13, estimated=False),
            model="fake",
            latency_s=0.2,
        ),
    )
    collector.record_cache(hit=True)
    collector.record_cache(hit=False)

    stats = collector.snapshot(
        run_id="run",
        started_at=datetime(1970, 1, 1, tzinfo=timezone.utc),
        finished_at=datetime(1970, 1, 1, tzinfo=timezone.utc),
        pipeline="tiered",
        source=SourceInfo(name="x.pdf", sha256="a" * 64, size_bytes=1, page_count=1),
        config_hash="config",
    )

    assert stats.vision_calls == 1
    assert stats.input_tokens == 10
    assert stats.output_tokens == 3
    assert stats.total_tokens == 13
    assert stats.cache_hits == 1
    assert stats.cache_misses == 1
    assert stats.calls[0].cache_hit is False
