from __future__ import annotations

from typing import Protocol

from pydantic import ConfigDict

from ..models import ContractModel, Usage


class VisionResult(ContractModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    text: str
    usage: Usage
    model: str
    latency_s: float
    request_id: str | None = None


class VisionBackend(Protocol):
    name: str
    model: str

    def describe_image(
        self, image_png: bytes, *, prompt_id: str, lang: str = "auto"
    ) -> VisionResult: ...

    def transcribe_page(
        self, image_png: bytes, *, prompt_id: str, lang: str = "auto"
    ) -> VisionResult: ...
