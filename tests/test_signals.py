from types import SimpleNamespace

import pytest

from doc2md.config import RouterConfig
from doc2md.converters.pdf.signals import compute_signals


def fake_page(
    *,
    text: str = "ordinary text",
    char_count: int | None = None,
    images: list[dict[str, float]] | None = None,
    tables: list[object] | None = None,
) -> SimpleNamespace:
    chars = [{}] * (len(text) if char_count is None else char_count)
    return SimpleNamespace(
        chars=chars,
        width=100,
        height=100,
        images=images or [],
        extract_text=lambda: text,
        extract_words=lambda: text.split(),
        find_tables=lambda: tables or [],
    )


def test_signals_capture_text_images_tables_garbling_and_layer() -> None:
    table = SimpleNamespace(extract=lambda: [["header", "value"], ["a", "b"]])
    page = fake_page(
        text="A (cid:12) Straße",
        images=[{"x0": 0, "x1": 50, "top": 0, "bottom": 50}],
        tables=[table],
    )

    signals = compute_signals(page, RouterConfig())

    assert signals.chars == len(page.extract_text())
    assert signals.words == 3
    assert signals.image_count == 1
    assert signals.image_area_ratio == pytest.approx(0.25)
    assert signals.table_count == 1
    assert signals.table_irregular is False
    assert signals.garbled_ratio > 0
    assert signals.has_text_layer is True


def test_unreliable_table_extraction_is_conservative() -> None:
    def fail_extract() -> list[list[str]]:
        raise RuntimeError("bad")

    page = fake_page(tables=[SimpleNamespace(extract=fail_extract)])

    signals = compute_signals(page, RouterConfig())

    assert signals.table_count == 1
    assert signals.table_irregular is True
