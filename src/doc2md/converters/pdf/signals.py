from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from ...config import RouterConfig
from ...models import PageSignals

_CID_PATTERN = re.compile(r"\(cid:\d+\)")


def _number(value: object, default: float = 0.0) -> float:
    return float(value) if isinstance(value, (int, float)) else default


def _image_area(page: Any) -> tuple[int, float]:
    width = max(_number(getattr(page, "width", 0)), 0.0)
    height = max(_number(getattr(page, "height", 0)), 0.0)
    page_area = width * height
    total = 0.0
    images = getattr(page, "images", []) or []
    for image in images:
        if not isinstance(image, Mapping):
            continue
        x0 = max(0.0, min(width, _number(image.get("x0"))))
        x1 = max(0.0, min(width, _number(image.get("x1"))))
        top = max(0.0, min(height, _number(image.get("top", image.get("y0")))))
        bottom = max(0.0, min(height, _number(image.get("bottom", image.get("y1")))))
        total += max(0.0, x1 - x0) * max(0.0, bottom - top)
    return len(images), min(1.0, total / page_area) if page_area else 0.0


def _table_signals(page: Any, config: RouterConfig) -> tuple[int, bool]:
    try:
        tables = list(page.find_tables() or [])
    except Exception:
        return 1, True

    irregular = False
    for table in tables:
        try:
            rows = table.extract() or []
            lengths = [len(row) if row is not None else 0 for row in rows]
            if not rows or len(set(lengths)) > 1:
                irregular = True
                continue
            cells = [cell for row in rows for cell in (row or [])]
            missing = sum(cell is None or cell == "" for cell in cells)
            if cells and missing / len(cells) > config.table_none_ratio:
                irregular = True
        except Exception:
            irregular = True
    return len(tables), irregular


def _garbled_ratio(text: str) -> float:
    cid_chars = sum(len(match.group(0)) for match in _CID_PATTERN.finditer(text))
    bad_chars = cid_chars + sum(
        1
        for char in text
        if char == "\ufffd" or 0xE000 <= ord(char) <= 0xF8FF
    )
    return min(1.0, bad_chars / len(text)) if text else 0.0


def compute_signals(page: Any, config: RouterConfig) -> PageSignals:
    """Compute cheap, pdfplumber-compatible signals without selecting an adapter."""
    text = page.extract_text() or ""
    words = page.extract_words() or []
    chars = len(getattr(page, "chars", []))
    image_count, image_area_ratio = _image_area(page)
    table_count, table_irregular = _table_signals(page, config)
    return PageSignals(
        chars=chars,
        words=len(words),
        image_area_ratio=image_area_ratio,
        image_count=image_count,
        table_count=table_count,
        table_irregular=table_irregular,
        garbled_ratio=_garbled_ratio(text),
        has_text_layer=chars >= config.min_chars_text_layer,
    )
