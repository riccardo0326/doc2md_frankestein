from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def _digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def anydoc_cache_key(
    source_hash: str,
    page: int,
    version: str,
    backend: str,
    config: object,
) -> str:
    return _digest(
        {
            "source": source_hash,
            "page": page,
            "anydoc_version": version,
            "backend": backend,
            "config": config,
        }
    )


def page_cache_key(source_hash: str, page: int, backend: str, config: object) -> str:
    return _digest({"source": source_hash, "page": page, "backend": backend, "config": config})


def vision_cache_key(image_or_page: str, prompt_id: str, model: str, config: object) -> str:
    return _digest(
        {"input": image_or_page, "prompt": prompt_id, "model": model, "config": config}
    )


class DiskCache:
    """JSON-only content-addressed cache with atomic replacement."""

    def __init__(self, directory: str | Path, source_hash: str, *, enabled: bool = True) -> None:
        self.directory = Path(directory)
        self.source_hash = source_hash
        self.enabled = enabled
        self.warnings: list[str] = []

    def path_for(self, stage: str, key: str) -> Path:
        parts = [part for part in (*stage.split("/"), *key.split("/")) if part]
        safe_parts = [part.replace("..", "_").replace("\\", "_") for part in parts]
        return (
            self.directory
            / self.source_hash[:2]
            / self.source_hash
            / Path(*safe_parts).with_suffix(".json")
        )

    def get(self, stage: str, key: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        path = self.path_for(stage, key)
        try:
            with path.open(encoding="utf-8") as handle:
                value = json.load(handle)
            if not isinstance(value, dict):
                raise ValueError("cache value is not an object")
            return value
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            if path.exists():
                path.unlink()
                self.warnings.append(f"cache_corrupt:{path.as_posix()}")
            return None

    def put(self, stage: str, key: str, value: dict[str, Any]) -> None:
        if not self.enabled:
            return
        path = self.path_for(stage, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent, suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
