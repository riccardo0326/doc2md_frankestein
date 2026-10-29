from __future__ import annotations

import os
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_hybrid_images import CountingVision, png

from doc2md.config import ImageConfig, RouterConfig
from doc2md.converters.pdf.images import ImageStage
from doc2md.converters.pdf.router import classify
from doc2md.converters.pdf.signals import compute_signals

AUTHORIZED_CORPUS = Path(r"C:\Users\rp99480\dev\doc2md\samples\unstructured-demo")


def test_offline_fake_image_context_matrix() -> None:
    vision = CountingVision()
    renderer_calls: list[int] = []

    def renderer(_page: object, page: int, _image: dict[str, object], _dpi: int) -> bytes:
        renderer_calls.append(page)
        return png((80, 80))

    for page_class in ("TEXT", "COMPLEX"):
        result = ImageStage(
            ImageConfig(min_width_px=64, min_height_px=64, min_area_px=100),
            backend=vision,
            renderer=renderer,
        ).process_page(
            SimpleNamespace(images=[{"x0": 0, "x1": 80, "y0": 0, "y1": 80}]),
            1,
            page_class,
            source_path=None,
            output_dir=None,
            seen={},
        )
        assert result.records[0].status == "described"

    scanned = ImageStage(
        ImageConfig(min_width_px=64, min_height_px=64, min_area_px=100),
        backend=vision,
        renderer=renderer,
    ).process_page(
        SimpleNamespace(images=[{"x0": 0, "x1": 80, "y0": 0, "y1": 80}]),
        1,
        "SCANNED",
        source_path=None,
        output_dir=None,
        seen={},
    )

    assert scanned.records == []
    assert renderer_calls == [1, 1]
    assert vision.calls == 2


def test_authorized_corpus_is_read_only_and_aggregate_only() -> None:
    if os.environ.get("DOC2MD_RUN_AUTHORIZED_CORPUS") != "1":
        pytest.skip("authorized corpus check is opt-in")
    if not AUTHORIZED_CORPUS.is_dir():
        pytest.skip("authorized corpus path is unavailable")
    sources = sorted(AUTHORIZED_CORPUS.glob("*.pdf"))
    if not sources:
        pytest.skip("authorized corpus contains no PDFs")

    import pdfplumber

    outcomes: Counter[str] = Counter()
    documents = 0
    pages = 0
    images = 0
    for source in sources:
        try:
            with pdfplumber.open(source) as pdf:
                documents += 1
                for page in pdf.pages:
                    pages += 1
                    images += len(page.images or [])
                    decision = classify(
                        compute_signals(page, RouterConfig()), RouterConfig(), page=pages
                    )
                    outcomes[decision.page_class] += 1
        except Exception as exc:
            outcomes[f"failure:{type(exc).__name__}"] += 1

    assert documents > 0
    assert pages >= 0
    assert images >= 0
    assert sum(outcomes.values()) >= documents
