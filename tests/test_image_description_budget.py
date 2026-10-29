from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from doc2md.config import VisionConfig
from doc2md.vision.kelpie import KelpieVisionBackend


def test_image_prompt_is_concise_and_information_focused() -> None:
    prompt = KelpieVisionBackend(VisionConfig())._prompt("describe_image.v1").lower()

    for term in ("charts", "tables", "labels", "numbers", "relationships"):
        assert term in prompt
    assert "decorative" in prompt
    assert "at most three sentences" in prompt
    assert "do not invent" in prompt


def test_image_and_page_output_budgets_are_separate() -> None:
    defaults = VisionConfig()
    assert defaults.max_tokens == 384
    assert defaults.transcribe_max_tokens == 1600

    custom = VisionConfig(max_tokens=128, transcribe_max_tokens=2048)
    assert custom.max_tokens == 128
    assert custom.transcribe_max_tokens == 2048


class RecordingResponses:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return SimpleNamespace(
            output_text="A concise synthetic description.",
            usage=SimpleNamespace(input_tokens=1, output_tokens=5, total_tokens=6),
            id="synthetic-response",
        )


class RecordingClient:
    def __init__(self) -> None:
        self.responses = RecordingResponses()


def test_backend_routes_image_and_page_budgets_to_their_operations() -> None:
    client = RecordingClient()
    backend = KelpieVisionBackend(
        VisionConfig(max_tokens=384, transcribe_max_tokens=1600),
        client=client,
    )

    backend.describe_image(b"image", prompt_id="describe_image.v1")
    assert client.responses.calls[-1]["max_output_tokens"] == 384

    backend.transcribe_page(b"page", prompt_id="transcribe_page.v1")
    assert client.responses.calls[-1]["max_output_tokens"] == 1600
