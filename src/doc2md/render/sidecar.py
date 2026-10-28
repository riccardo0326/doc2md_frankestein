from __future__ import annotations

import json
from pathlib import Path

from ..models import ConvertedDocument, RunStats


def document_json(document: ConvertedDocument) -> str:
    """Return the stable, UTF-8 JSON representation of a converted document."""
    return (
        json.dumps(
            document.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    )


def write_document(path: Path, document: ConvertedDocument) -> None:
    """Write a converted document sidecar with UTF-8 and LF line endings."""
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(document_json(document))


def run_json(stats: RunStats) -> str:
    """Return the stable run metrics envelope used by ``run.json``."""
    calls = [call for call in stats.calls if not call.cache_hit]
    page_counts = {
        "total": len(stats.pages),
        "text": sum(page.page_class == "TEXT" for page in stats.pages),
        "complex": sum(page.page_class == "COMPLEX" for page in stats.pages),
        "scanned": sum(page.page_class == "SCANNED" for page in stats.pages),
        "failed": stats.pages_failed,
    }
    payload = {
        "run_id": stats.run_id,
        "started_at": stats.started_at.isoformat(),
        "finished_at": stats.finished_at.isoformat(),
        "pipeline": stats.pipeline,
        "source": {
            "name": stats.source.name,
            "sha256": stats.source.sha256,
            "pages": stats.source.page_count,
        },
        "config_hash": stats.config_hash,
        "totals": {
            "wall_time_s": stats.wall_time_s,
            "pages": page_counts,
            "vision": {
                "calls": len(calls),
                "input_tokens": sum(call.input_tokens for call in calls),
                "output_tokens": sum(call.output_tokens for call in calls),
                "total_tokens": sum(call.total_tokens for call in calls),
                "estimated": any(call.estimated for call in calls),
            },
            "docling": {
                "pages": stats.docling_pages,
                "time_s": stats.docling_time_s,
            },
            "cache": {"hits": stats.cache_hits, "misses": stats.cache_misses},
        },
        "pages": [
            {
                "page": page.page,
                "class": page.page_class,
                "method": page.method,
                "duration_s": page.duration_s,
                "reasons": page.reasons,
            }
            for page in stats.pages
        ],
        "calls": [call.model_dump(mode="json") for call in calls],
        "warnings": stats.warnings,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def write_run(path: Path, stats: RunStats) -> None:
    """Write the deterministic run metrics sidecar with UTF-8 LF output."""
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(run_json(stats))
