from __future__ import annotations

from doc2md.converters.pdf.images import place_image_drafts
from doc2md.models import BBox, Block, ImageBlockDraft, PageResult, Provenance


def text_block(page: int, block_id: str, text: str, bbox: BBox | None) -> Block:
    return Block(
        block_id=block_id,
        type="paragraph",
        markdown=text,
        text=text,
        provenance=Provenance(page=page, source="anydoc", bbox=bbox),
    )


def page(page_number: int, blocks: list[Block]) -> PageResult:
    return PageResult(
        page=page_number,
        status="ok",
        page_class="TEXT",
        method="anydoc",
        blocks=blocks,
        duration_s=0.0,
    )


def draft(image_id: str, page_number: int, y0: float, y1: float) -> ImageBlockDraft:
    return ImageBlockDraft(
        image_id=image_id,
        page=page_number,
        markdown=f"figure {image_id}",
        text=image_id,
        bbox=BBox(x0=0, y0=y0, x1=10, y1=y1),
    )


def figure_ids(result: PageResult) -> list[str]:
    return [block.meta["image_id"] for block in result.blocks if block.type == "figure"]


def test_same_band_figures_preserve_draft_order() -> None:
    result = place_image_drafts(
        [page(1, [text_block(1, "p0001-b001", "text", BBox(x0=0, y0=20, x1=10, y1=80))])],
        [
            draft("p0001-i01", 1, 30, 40),
            draft("p0001-i02", 1, 30, 40),
            draft("p0001-i03", 1, 30, 40),
        ],
    )[0]

    assert figure_ids(result) == ["p0001-i01", "p0001-i02", "p0001-i03"]


def test_overlapping_figures_preserve_stable_draft_order() -> None:
    result = place_image_drafts(
        [page(1, [text_block(1, "p0001-b001", "text", BBox(x0=0, y0=20, x1=10, y1=80))])],
        [
            draft("p0001-i01", 1, 20, 50),
            draft("p0001-i02", 1, 40, 70),
            draft("p0001-i03", 1, 45, 65),
        ],
    )[0]

    assert figure_ids(result) == ["p0001-i01", "p0001-i02", "p0001-i03"]


def test_distinct_vertical_bands_remain_relative_to_text() -> None:
    result = place_image_drafts(
        [
            page(
                1,
                [
                    text_block(1, "p0001-b001", "above", BBox(x0=0, y0=0, x1=10, y1=10)),
                    text_block(1, "p0001-b002", "middle", BBox(x0=0, y0=50, x1=10, y1=60)),
                    text_block(1, "p0001-b003", "below", BBox(x0=0, y0=100, x1=10, y1=110)),
                ],
            )
        ],
        [draft("p0001-i01", 1, 20, 30), draft("p0001-i02", 1, 80, 90)],
    )[0]

    assert [block.text for block in result.blocks] == [
        "above",
        "p0001-i01",
        "middle",
        "p0001-i02",
        "below",
    ]


def test_unknown_bbox_text_does_not_reverse_or_cross_page() -> None:
    pages = [
        page(
            1,
            [
                text_block(1, "p0001-b001", "above", BBox(x0=0, y0=0, x1=10, y1=10)),
                text_block(1, "p0001-b002", "unknown", None),
                text_block(1, "p0001-b003", "below", BBox(x0=0, y0=50, x1=10, y1=60)),
            ],
        ),
        page(2, [text_block(2, "p0002-b001", "page two", None)]),
    ]
    drafts = [
        draft("p0001-i01", 1, 20, 30),
        draft("p0001-i02", 1, 25, 35),
        draft("p0002-i01", 2, 20, 30),
    ]

    placed = place_image_drafts(pages, drafts)

    assert [block.text for block in placed[0].blocks] == [
        "above",
        "p0001-i01",
        "p0001-i02",
        "unknown",
        "below",
    ]
    assert figure_ids(placed[1]) == ["p0002-i01"]
