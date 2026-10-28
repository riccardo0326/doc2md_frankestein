from __future__ import annotations

import importlib
from collections.abc import Callable
from io import BytesIO
from typing import Protocol

from ...errors import (
    HardPathHandoffError,
    OptionalDependencyError,
    PageExtractionError,
)
from ...models import Block, Provenance


class AnyDocBinding(Protocol):
    def to_markdown_bytes(self, data: bytes, format: str, *, ocr: str) -> str: ...


PageValidator = Callable[[bytes], None]


def _load_binding() -> AnyDocBinding:
    try:
        return importlib.import_module("anydoc")
    except ModuleNotFoundError as exc:
        raise OptionalDependencyError(
            "firecrawl-anydoc is optional; install the 'anydoc' extra "
            "with `python -m pip install -e \".[anydoc]\"`"
        ) from exc


def _validate_one_page_pdf(data: bytes) -> None:
    if not data.startswith(b"%PDF-"):
        raise PageExtractionError("Expected a one-page PDF starting with %PDF-")

    try:
        pypdf = importlib.import_module("pypdf")
    except ModuleNotFoundError as exc:
        raise OptionalDependencyError(
            "The AnyDoc page bridge requires pypdf; install the 'anydoc' extra"
        ) from exc

    try:
        reader = pypdf.PdfReader(BytesIO(data), strict=False)
        page_count = len(reader.pages)
    except Exception as exc:
        raise PageExtractionError(f"Invalid one-page PDF: {exc}") from exc
    if page_count != 1:
        raise PageExtractionError(f"Expected a one-page PDF, found {page_count} pages")


def _is_ocr_error(binding: AnyDocBinding, error: Exception) -> bool:
    error_type = getattr(binding, "NeedsOcrError", None)
    return (
        (error_type is not None and isinstance(error, error_type))
        or type(error).__name__ == "NeedsOcrError"
    )


class AnyDocFastExtractor:
    """Convert one original page represented as an in-memory one-page PDF."""

    def __init__(
        self,
        *,
        binding: AnyDocBinding | None = None,
        validator: PageValidator | None = None,
    ) -> None:
        self._binding = binding
        self._validator = validator

    def extract(self, page_pdf: bytes, *, page: int) -> Block:
        if isinstance(page, bool) or not isinstance(page, int) or page < 1:
            raise PageExtractionError("Original page number must be a positive integer")
        if not isinstance(page_pdf, bytes) or not page_pdf:
            raise PageExtractionError("Expected non-empty one-page PDF bytes")

        binding = self._binding or _load_binding()
        if self._validator is not None:
            self._validator(page_pdf)
        elif self._binding is None:
            _validate_one_page_pdf(page_pdf)
        elif not page_pdf.startswith(b"%PDF-"):
            raise PageExtractionError("Expected a one-page PDF starting with %PDF-")

        try:
            markdown = binding.to_markdown_bytes(page_pdf, format="pdf", ocr="reject")
        except Exception as exc:
            if _is_ocr_error(binding, exc):
                raise HardPathHandoffError(
                    f"Original page {page} requires OCR; hand off to the configured hard path"
                ) from exc
            raise PageExtractionError(f"AnyDoc conversion failed for page {page}: {exc}") from exc

        if not isinstance(markdown, str) or not markdown.strip():
            raise PageExtractionError(f"AnyDoc returned empty Markdown for page {page}")

        return Block(
            block_id=f"p{page:04d}-b001",
            type="other",
            markdown=markdown,
            text=markdown,
            provenance=Provenance(page=page, source="anydoc"),
        )
