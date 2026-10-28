import pytest

from doc2md.config import RouterConfig
from doc2md.converters.pdf.router import classify
from doc2md.models import PageSignals


def make_signals(**overrides: object) -> PageSignals:
    values: dict[str, object] = {
        "chars": 500,
        "words": 80,
        "image_area_ratio": 0.0,
        "image_count": 0,
        "table_count": 0,
        "table_irregular": False,
        "garbled_ratio": 0.0,
        "has_text_layer": True,
    }
    values.update(overrides)
    return PageSignals.model_validate(values)


@pytest.mark.parametrize(
    ("signals", "expected_class", "reason"),
    [
        (make_signals(chars=0, has_text_layer=False), "SCANNED", "no_text_layer"),
        (make_signals(chars=10, image_area_ratio=0.8), "SCANNED", "low_text"),
        (make_signals(garbled_ratio=0.5), "COMPLEX", "garbled_text"),
        (make_signals(table_irregular=True), "COMPLEX", "irregular_table"),
        (make_signals(chars=100, image_area_ratio=0.8), "COMPLEX", "image_dominant"),
        (make_signals(), "TEXT", ""),
    ],
)
def test_router_first_match_returns_explainable_reason(
    signals: PageSignals,
    expected_class: str,
    reason: str,
) -> None:
    decision = classify(signals, RouterConfig(), page=4)

    assert decision.page == 4
    assert decision.page_class == expected_class
    if reason:
        assert any(reason in item for item in decision.reasons)
    else:
        assert decision.reasons == []


def test_router_thresholds_are_configurable() -> None:
    signals = make_signals(chars=80, image_area_ratio=0.8)

    default_decision = classify(signals, RouterConfig(), page=1)
    overridden_decision = classify(signals, RouterConfig(min_chars=100), page=1)

    assert default_decision.page_class == "COMPLEX"
    assert overridden_decision.page_class == "SCANNED"


def test_router_rejects_invalid_page_number() -> None:
    with pytest.raises(ValueError):
        classify(make_signals(), RouterConfig(), page=0)
