from __future__ import annotations

import hashlib

from ..errors import VisionError
from ..models import Usage
from .base import VisionResult


class FakeVisionBackend:
    name = "fake"

    def __init__(
        self,
        *,
        model: str = "fake-vision",
        transcription: str = "Synthetic transcription.",
        fail: bool = False,
    ) -> None:
        self.model = model
        self.transcription = transcription
        self.fail = fail

    def _result(self, text: str, image_png: bytes) -> VisionResult:
        if self.fail:
            digest = hashlib.sha256(image_png).hexdigest()[:8]
            raise VisionError(f"fake vision failure for {digest}")
        output_tokens = max(1, len(text) // 4)
        return VisionResult(
            text=text,
            usage=Usage(
                input_tokens=12,
                output_tokens=output_tokens,
                total_tokens=12 + output_tokens,
                estimated=True,
            ),
            model=self.model,
            latency_s=0.0,
        )

    def describe_image(
        self, image_png: bytes, *, prompt_id: str, lang: str = "auto"
    ) -> VisionResult:
        del prompt_id, lang
        digest = hashlib.sha256(image_png).hexdigest()[:8]
        return self._result(f"[fake description of {digest}]", image_png)

    def transcribe_page(
        self, image_png: bytes, *, prompt_id: str, lang: str = "auto"
    ) -> VisionResult:
        del prompt_id, lang
        return self._result(self.transcription, image_png)
