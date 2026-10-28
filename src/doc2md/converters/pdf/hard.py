from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from io import BytesIO
from pathlib import Path

from ...errors import HardExtractionError
from ...models import Block, BlockType, Provenance
from ...vision.base import VisionBackend, VisionResult

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_LIST_RE = re.compile(r"^\s*(?:[-*+] |\d+[.)]\s+)(.+?)\s*$")


def _table_meta(markdown: str) -> dict[str, str | int | float | bool]:
    rows = [line for line in markdown.splitlines() if line.strip().startswith("|")]
    data_rows = [line for line in rows if not re.match(r"^\s*\|(?:\s*:?-+:?\s*\|)+\s*$", line)]
    columns = max((line.count("|") - 1 for line in rows), default=0)
    meta: dict[str, str | int | float | bool] = {
        "table_rows": len(data_rows),
        "table_cols": columns,
    }
    if len(rows) < 2 or not any("-" in line for line in rows[1:]):
        meta["warning"] = "irregular_table"
    return meta


def blocks_from_transcription(page: int, markdown: str) -> list[Block]:
    """Map Kelpie Markdown into stable, page-provenance-rich blocks."""
    if not isinstance(markdown, str) or not markdown.strip():
        raise HardExtractionError(f"Kelpie returned no transcribed content for page {page}")

    lines = markdown.splitlines()
    blocks: list[Block] = []
    paragraph: list[str] = []

    def append(
        block_type: BlockType,
        value: str,
        level: int | None = None,
        meta: dict[str, str | int | float | bool] | None = None,
    ) -> None:
        text = value.strip()
        if not text:
            return
        if block_type == "heading":
            heading = _HEADING_RE.match(text)
            text = heading.group(2).strip() if heading else text
        blocks.append(
            Block(
                block_id=f"p{page:04d}-b{len(blocks) + 1:03d}",
                type=block_type,
                markdown=value.strip(),
                text=text,
                level=level,
                provenance=Provenance(page=page, source="vision"),
                meta=meta or {},
            )
        )

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            append("paragraph", " ".join(paragraph))
            paragraph = []

    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        index += 1
        if not stripped:
            flush_paragraph()
            continue
        heading = _HEADING_RE.match(stripped)
        if heading:
            flush_paragraph()
            append("heading", stripped, level=len(heading.group(1)))
            continue
        if stripped.startswith("|"):
            flush_paragraph()
            table_lines = [stripped]
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].strip())
                index += 1
            table_markdown = "\n".join(table_lines)
            append("table", table_markdown, meta=_table_meta(table_markdown))
            continue
        list_match = _LIST_RE.match(stripped)
        if list_match:
            flush_paragraph()
            list_lines = [f"- {list_match.group(1)}"]
            while index < len(lines):
                next_match = _LIST_RE.match(lines[index].strip())
                if next_match is None:
                    break
                list_lines.append(f"- {next_match.group(1)}")
                index += 1
            append("list", "\n".join(list_lines))
            continue
        paragraph.append(stripped)
    flush_paragraph()
    if not blocks:
        raise HardExtractionError(f"Kelpie returned no transcribed content for page {page}")
    return blocks


PageRenderer = Callable[[Path, int, int], bytes]


def _render_page(source: Path, page_number: int, dpi: int) -> bytes:
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise HardExtractionError("pypdfium2 is required for Kelpie hard pages") from exc
    document = pdfium.PdfDocument(str(source))
    page = document[page_number - 1]
    try:
        bitmap = page.render(scale=dpi / 72.0)
        image = bitmap.to_pil().convert("RGB")
        output = BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()
    finally:
        page.close()
        document.close()


class KelpieHardExtractor:
    name = "kelpie"

    def __init__(
        self,
        vision: VisionBackend,
        *,
        page_dpi: int,
        prompt_id: str,
        renderer: PageRenderer | None = None,
    ) -> None:
        self.vision = vision
        self.page_dpi = page_dpi
        self.prompt_id = prompt_id
        self.renderer = renderer or _render_page
        self._calls: list[tuple[str, VisionResult]] = []

    def drain_calls(self) -> list[tuple[str, VisionResult]]:
        calls = self._calls
        self._calls = []
        return calls

    def extract(
        self,
        source: Path,
        pages: Sequence[int],
        context: object | None = None,
    ) -> dict[int, list[Block]]:
        del context
        extracted: dict[int, list[Block]] = {}
        for page_number in sorted(set(pages)):
            if page_number < 1:
                raise HardExtractionError("hard-path page numbers must be positive")
            try:
                image_png = self.renderer(source, page_number, self.page_dpi)
                result = self.vision.transcribe_page(image_png, prompt_id=self.prompt_id)
                self._calls.append((f"p{page_number:04d}", result))
                extracted[page_number] = blocks_from_transcription(page_number, result.text)
            except HardExtractionError:
                raise
            except Exception as exc:
                raise HardExtractionError(
                    f"Kelpie hard transcription failed on page {page_number}: {exc}"
                ) from exc
        return extracted
