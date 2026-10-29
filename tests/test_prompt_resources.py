from __future__ import annotations

from importlib import resources

import pytest

from doc2md.config import VisionConfig
from doc2md.errors import VisionError
from doc2md.vision.kelpie import KelpieVisionBackend


@pytest.mark.parametrize("prompt_id", ["describe_image.v1", "transcribe_page.v1"])
def test_prompt_is_resolved_as_a_doc2md_package_resource(prompt_id: str) -> None:
    resource = resources.files("doc2md").joinpath("prompts", f"{prompt_id}.txt")

    assert resource.is_file()
    assert KelpieVisionBackend(VisionConfig())._prompt(prompt_id) == resource.read_text(
        encoding="utf-8"
    ).strip()


def test_missing_prompt_keeps_typed_vision_error() -> None:
    with pytest.raises(VisionError, match="Prompt file not found"):
        KelpieVisionBackend(VisionConfig())._prompt("missing-prompt.v1")
