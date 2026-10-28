from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ...errors import SourceError


class PdfSource:
    """Open a PDF once and expose original 1-based page numbers."""

    def __init__(self, source: str | Path) -> None:
        self.path = Path(source)
        self._pdf: Any | None = None

    def __enter__(self) -> PdfSource:
        try:
            import pdfplumber
        except ModuleNotFoundError as exc:
            raise SourceError("pdfplumber is required for PDF inspection") from exc
        try:
            self._pdf = pdfplumber.open(self.path)
        except Exception as exc:
            raise SourceError(f"Unable to open PDF {self.path}: {exc}") from exc
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        if self._pdf is not None:
            self._pdf.close()
            self._pdf = None

    def iter_pages(self) -> Iterator[tuple[int, Any]]:
        if self._pdf is None:
            raise SourceError("PdfSource must be opened before iterating pages")
        try:
            for page_number, page in enumerate(self._pdf.pages, start=1):
                yield page_number, page
        except Exception as exc:
            raise SourceError(f"Unable to read PDF pages from {self.path}: {exc}") from exc

    @property
    def page_count(self) -> int:
        if self._pdf is None:
            raise SourceError("PdfSource must be opened before reading page_count")
        return len(self._pdf.pages)

    def __iter__(self) -> Iterator[tuple[int, Any]]:
        return self.iter_pages()
