from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from doc2md.config import ImageConfig
from doc2md.converters.pdf import images
from doc2md.converters.pdf.images import ImageProcessingResult, ImageStage
from doc2md.errors import OptionalDependencyError
from doc2md.vision.fake import FakeVisionBackend


def test_image_stage_passes_page_context_and_renderer_to_collection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page = SimpleNamespace(images=[])

    def renderer(_page: Any, _number: int, _image: dict[str, Any], _dpi: int) -> bytes:
        return b"png"

    observed: dict[str, Any] = {}

    def collect(
        received_page: Any,
        pdfium_document: Any,
        page_number: int,
        config: ImageConfig,
        seen: dict[str, str],
        *,
        renderer: Any,
        page_class: str | None,
    ) -> list[Any]:
        observed.update(
            page=received_page,
            pdfium_document=pdfium_document,
            page_number=page_number,
            config=config,
            seen=seen,
            renderer=renderer,
            page_class=page_class,
        )
        return []

    monkeypatch.setattr(images, "collect_images", collect)
    stage = ImageStage(ImageConfig(), renderer=renderer)

    result = stage.process_page(
        page,
        7,
        "COMPLEX",
        source_path=Path("input.pdf"),
        output_dir=None,
        seen={},
    )

    assert isinstance(result, ImageProcessingResult)
    assert observed["page"] is page
    assert observed["page_number"] == 7
    assert observed["page_class"] == "COMPLEX"
    assert observed["renderer"] is renderer


def test_image_stage_passes_backend_and_cache_to_processing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = FakeVisionBackend()
    cache = object()
    observed: dict[str, Any] = {}
    expected = ImageProcessingResult(records=[], blocks=[])

    monkeypatch.setattr(images, "collect_images", lambda *args, **kwargs: [])

    def process(
        candidates: list[Any],
        received_backend: Any,
        *,
        prompt_id: str,
        output_dir: Path | None,
        describe: bool,
        cache: Any,
        cache_config: Any,
    ) -> ImageProcessingResult:
        observed.update(
            candidates=candidates,
            backend=received_backend,
            prompt_id=prompt_id,
            output_dir=output_dir,
            describe=describe,
            cache=cache,
            cache_config=cache_config,
        )
        return expected

    monkeypatch.setattr(images, "process_images", process)
    stage = ImageStage(
        ImageConfig(),
        backend=backend,
        renderer=lambda _page, _number, _image, _dpi: b"png",
        cache_config={"render_dpi": 150},
    )

    result = stage.process_page(
        SimpleNamespace(images=[]),
        3,
        "TEXT",
        source_path=None,
        output_dir=Path("out"),
        seen={},
        cache=cache,
        prompt_id="describe_image.v1",
    )

    assert result is expected
    assert observed["backend"] is backend
    assert observed["cache"] is cache
    assert observed["prompt_id"] == "describe_image.v1"
    assert observed["output_dir"] == Path("out")
    assert observed["describe"] is True
    assert observed["cache_config"] == {"render_dpi": 150}


def test_default_renderer_document_is_closed_after_processing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Document:
        closed = False

        def close(self) -> None:
            self.closed = True

    document = Document()

    def factory(source_path: Path) -> Document:
        assert source_path == Path("input.pdf")
        return document

    monkeypatch.setattr(images, "collect_images", lambda *args, **kwargs: [])
    stage = ImageStage(ImageConfig(), renderer_document_factory=factory)

    stage.process_page(
        SimpleNamespace(images=[]),
        1,
        "TEXT",
        source_path=Path("input.pdf"),
        output_dir=None,
        seen={},
    )

    assert document.closed is True


def test_missing_default_renderer_dependency_is_typed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = __import__

    def missing_renderer(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "pypdfium2":
            raise ModuleNotFoundError("pypdfium2")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", missing_renderer)
    stage = ImageStage(ImageConfig())

    with pytest.raises(OptionalDependencyError, match="pypdfium2"):
        stage.process_page(
            SimpleNamespace(images=[]),
            1,
            "TEXT",
            source_path=Path("input.pdf"),
            output_dir=None,
            seen={},
        )
