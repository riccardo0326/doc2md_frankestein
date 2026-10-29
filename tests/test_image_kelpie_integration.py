import base64
import os

import pytest

from doc2md.config import VisionConfig
from doc2md.vision.kelpie import KelpieVisionBackend

pytestmark = pytest.mark.kelpie

if not os.environ.get("KELPIE_PROXY_BASE_URL") or not os.environ.get("KELPIE_MODEL"):
    pytest.skip(
        "approved Kelpie integration environment is not configured",
        allow_module_level=True,
    )


def test_approved_kelpie_image_probe_contract() -> None:
    backend = KelpieVisionBackend(VisionConfig())
    one_pixel_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    )

    result = backend.describe_image(one_pixel_png, prompt_id="describe_image.v1")

    assert isinstance(result.text, str)
    assert result.model
    assert result.usage.total_tokens >= 0
