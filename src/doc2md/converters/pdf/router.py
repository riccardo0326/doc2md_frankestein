from __future__ import annotations

from collections.abc import Mapping

from ...config import Config, RouterConfig
from ...models import PageClass, PageSignals, RouteDecision


def _router_config(config: RouterConfig | Config) -> RouterConfig:
    return config.router if isinstance(config, Config) else config


def classify(
    signals: PageSignals | Mapping[str, object],
    config: RouterConfig | Config,
    *,
    page: int = 1,
) -> RouteDecision:
    """Apply the documented first-match routing policy to one page."""
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError("page must be a positive integer")
    signals_model = PageSignals.model_validate(signals)
    cfg = _router_config(config)

    if not signals_model.has_text_layer:
        page_class: PageClass = "SCANNED"
        reasons = ["no_text_layer"]
    elif (
        signals_model.chars < cfg.min_chars
        and signals_model.image_area_ratio >= cfg.scan_image_ratio
    ):
        page_class = "SCANNED"
        reasons = ["low_text", "high_image_area"]
    elif signals_model.garbled_ratio >= cfg.max_garbled:
        page_class = "COMPLEX"
        reasons = ["garbled_text"]
    elif signals_model.table_irregular:
        page_class = "COMPLEX"
        reasons = ["irregular_table"]
    elif (
        signals_model.image_area_ratio >= cfg.complex_image_ratio
        and signals_model.chars < cfg.image_page_min_chars
    ):
        page_class = "COMPLEX"
        reasons = ["image_dominant"]
    else:
        page_class = "TEXT"
        reasons = []

    return RouteDecision(
        page=page,
        page_class=page_class,
        reasons=reasons,
        signals=signals_model,
    )
