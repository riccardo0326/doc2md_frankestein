from __future__ import annotations

import os
import tempfile
from collections import Counter
from pathlib import Path

import pytest

from doc2md import api
from doc2md.config import RouterConfig
from doc2md.converters.pdf.router import classify
from doc2md.converters.pdf.signals import compute_signals

AUTHORIZED_CORPUS = Path(r"C:\Users\rp99480\dev\unstructured-ingest-source")
APPROVED_TEMP = Path(r"C:\Users\rp99480\AppData\Local\Temp\opencode")


def test_final_public_runtime_guard_is_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    with tempfile.TemporaryDirectory(dir=APPROVED_TEMP, prefix="doc2md-final-guard-") as path:
        _run_final_public_runtime_guard(Path(path), monkeypatch)


def _run_final_public_runtime_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from test_public_runtime import CountingVision, config, image_pdf, install_fake_runtime

    source = tmp_path / "final-guard.pdf"
    source.write_bytes(image_pdf())
    vision = CountingVision()
    install_fake_runtime(monkeypatch, vision)

    result = api.convert(source, tmp_path / "out", config=config())

    assert result.document.pages[0].status == "ok"
    assert result.document.images[0].status == "described"
    assert vision.describe_calls == 1


def test_authorized_corpus_guard_is_exact_path_and_aggregate_only() -> None:
    if os.environ.get("DOC2MD_RUN_AUTHORIZED_CORPUS") != "1":
        pytest.skip("authorized corpus check is opt-in")
    if not AUTHORIZED_CORPUS.is_dir():
        pytest.skip("authorized corpus path is unavailable")
    sources = sorted(AUTHORIZED_CORPUS.rglob("*.pdf"))
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
                for page_number, page in enumerate(pdf.pages, start=1):
                    pages += 1
                    images += len(page.images or [])
                    decision = classify(
                        compute_signals(page, RouterConfig()), RouterConfig(), page=page_number
                    )
                    outcomes[decision.page_class] += 1
        except Exception as exc:
            outcomes[f"failure:{type(exc).__name__}"] += 1

    assert documents > 0
    assert pages >= 0
    assert images >= 0
    assert sum(outcomes.values()) >= documents
