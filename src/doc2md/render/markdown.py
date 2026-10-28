from __future__ import annotations

from ..models import ConvertedDocument, PageResult


def _failure_marker(page: PageResult) -> str:
    return f"<!-- page: {page.page} failed: {page.error or 'unknown error'} -->"


def render_markdown(
    document: ConvertedDocument,
    *,
    page_markers: bool = False,
    block_anchors: bool = False,
) -> str:
    """Render pages in input order without interpreting block Markdown."""
    chunks: list[str] = []
    for page in document.pages:
        if page_markers:
            marker = (
                _failure_marker(page)
                if page.status == "failed"
                else f"<!-- page: {page.page} -->"
            )
            chunks.append(marker)

        if page.status == "failed":
            if not page_markers:
                chunks.append(_failure_marker(page))
        else:
            for block in page.blocks:
                if block_anchors:
                    chunks.append(f"<!-- block: {block.block_id} -->")
                chunks.append(block.markdown)
        chunks.append("")

    return "\n".join(chunks).rstrip("\n") + "\n"
