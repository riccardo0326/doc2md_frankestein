from pathlib import Path

from doc2md.cache import DiskCache, anydoc_cache_key, vision_cache_key


def test_cache_key_changes_with_output_affecting_inputs() -> None:
    first = anydoc_cache_key("source", 1, "0.2.4", "anydoc", {"min_chars": 50})
    same = anydoc_cache_key("source", 1, "0.2.4", "anydoc", {"min_chars": 50})
    changed = anydoc_cache_key("source", 1, "0.2.4", "anydoc", {"min_chars": 100})
    image = vision_cache_key("image-hash", "describe_image.v1", "helios", {"dpi": 150})

    assert first == same
    assert first != changed
    assert image != vision_cache_key("other-image", "describe_image.v1", "helios", {"dpi": 150})


def test_cache_writes_json_atomically_and_reads_content(tmp_path: Path) -> None:
    cache = DiskCache(tmp_path / "cache", "a" * 64)
    key = anydoc_cache_key("a" * 64, 1, "0.2.4", "anydoc", {})

    cache.put("anydoc", key, {"blocks": [{"text": "cached"}]})

    assert cache.get("anydoc", key) == {"blocks": [{"text": "cached"}]}
    assert not list((tmp_path / "cache").rglob("*.tmp"))


def test_corrupt_entry_is_deleted_and_reported_as_miss(tmp_path: Path) -> None:
    cache = DiskCache(tmp_path / "cache", "b" * 64)
    key = "bad-entry"
    path = cache.path_for("stage", key)
    path.parent.mkdir(parents=True)
    path.write_text("not-json", encoding="utf-8")

    assert cache.get("stage", key) is None
    assert not path.exists()
    assert cache.warnings == [f"cache_corrupt:{path.as_posix()}"]
