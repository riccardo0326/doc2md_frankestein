from __future__ import annotations

import base64
import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any, Literal

from ...cache import DiskCache, vision_cache_key
from ...config import ImageConfig
from ...errors import VisionError
from ...models import BBox, Block, ImageBlockDraft, ImageRecord, PageResult, Provenance
from ...vision.base import VisionBackend, VisionResult


@dataclass(frozen=True)
class ImageCandidate:
    image_id: str
    page: int
    png: bytes | None
    width_px: int
    height_px: int
    sha256: str
    bbox: BBox | None
    skip_reason: Literal["too_small", "bad_aspect", "duplicate"] | None = None
    canonical_image_id: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class ImageProcessingResult:
    records: list[ImageRecord]
    blocks: list[ImageBlockDraft]
    calls: list[tuple[str, VisionResult]] = field(default_factory=list)
    cache_hits: int = 0
    cache_misses: int = 0


ImageRenderer = Callable[[Any, int, dict[str, Any], int], bytes]


def _render_crop(pdfium_document: Any, page_number: int, image: dict[str, Any], dpi: int) -> bytes:
    page = pdfium_document[page_number - 1]
    try:
        scale = dpi / 72.0
        rendered = page.render(scale=scale).to_pil().convert("RGB")
        page_height = float(page.get_size()[1])
        x0 = float(image["x0"]) * scale
        x1 = float(image["x1"]) * scale
        top = float(image.get("top", page_height - float(image["y1"]))) * scale
        bottom = float(image.get("bottom", page_height - float(image["y0"]))) * scale
        crop = rendered.crop(
            (
                max(0, min(rendered.width, round(x0))),
                max(0, min(rendered.height, round(top))),
                max(0, min(rendered.width, round(x1))),
                max(0, min(rendered.height, round(bottom))),
            )
        )
        output = BytesIO()
        crop.save(output, format="PNG")
        return output.getvalue()
    finally:
        page.close()


def _bbox(image: dict[str, Any]) -> BBox | None:
    keys = ("x0", "y0", "x1", "y1")
    if not all(key in image for key in keys):
        return None
    return BBox(**{key: float(image[key]) for key in keys})


def collect_images(
    page: Any,
    pdfium_document: Any,
    page_number: int,
    config: ImageConfig,
    seen: dict[str, str],
    *,
    renderer: ImageRenderer | None = None,
    page_class: str | None = None,
) -> list[ImageCandidate]:
    if page_class == "SCANNED":
        return []
    candidates: list[ImageCandidate] = []
    for index, image in enumerate(page.images or [], start=1):
        image_id = f"p{page_number:04d}-i{index:02d}"
        try:
            png = (
                renderer(page, page_number, image, config.render_dpi)
                if renderer is not None
                else _render_crop(pdfium_document, page_number, image, config.render_dpi)
            )
            from PIL import Image

            with Image.open(BytesIO(png)) as rendered:
                width_px, height_px = rendered.size
        except Exception as exc:
            candidates.append(
                ImageCandidate(
                    image_id=image_id,
                    page=page_number,
                    png=None,
                    width_px=0,
                    height_px=0,
                    sha256="",
                    bbox=_bbox(image),
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            continue

        digest = hashlib.sha256(png).hexdigest()
        if (
            width_px < config.min_width_px
            or height_px < config.min_height_px
            or width_px * height_px < config.min_area_px
        ):
            candidates.append(
                ImageCandidate(
                    image_id,
                    page_number,
                    png,
                    width_px,
                    height_px,
                    digest,
                    _bbox(image),
                    "too_small",
                )
            )
            continue
        aspect = max(width_px / height_px, height_px / width_px)
        if aspect > config.max_aspect:
            candidates.append(
                ImageCandidate(
                    image_id,
                    page_number,
                    png,
                    width_px,
                    height_px,
                    digest,
                    _bbox(image),
                    "bad_aspect",
                )
            )
            continue
        canonical = seen.get(digest)
        if canonical is not None:
            candidates.append(
                ImageCandidate(
                    image_id,
                    page_number,
                    png,
                    width_px,
                    height_px,
                    digest,
                    _bbox(image),
                    "duplicate",
                    canonical,
                )
            )
            continue
        seen[digest] = image_id
        candidates.append(
            ImageCandidate(image_id, page_number, png, width_px, height_px, digest, _bbox(image))
        )
    return candidates


def _figure_draft(
    record: ImageRecord,
    text: str,
    data_uri: str | None = None,
    bbox: BBox | None = None,
) -> ImageBlockDraft:
    source = record.path or data_uri or ""
    return ImageBlockDraft(
        image_id=record.image_id,
        page=record.page,
        markdown=(
            f"![Figure {record.image_id}]({source})\n"
            f"> **Image description ({record.image_id}):** {text}"
        ),
        text=text,
        source_path=record.path,
        bbox=bbox,
    )


def process_images(
    candidates: list[ImageCandidate],
    backend: VisionBackend | None,
    *,
    prompt_id: str,
    output_dir: Path | None,
    describe: bool = True,
    cache: DiskCache | None = None,
    cache_config: object | None = None,
) -> ImageProcessingResult:
    records_by_id: dict[str, ImageRecord] = {}
    paths: dict[str, str | None] = {}
    data_uris: dict[str, str] = {}
    if output_dir is not None:
        (output_dir / "images").mkdir(parents=True, exist_ok=True)

    for candidate in candidates:
        if candidate.png is None or candidate.skip_reason is not None:
            continue
        data_uris[candidate.image_id] = (
            "data:image/png;base64," + base64.b64encode(candidate.png).decode("ascii")
        )
        if output_dir is not None:
            path = output_dir / "images" / f"{candidate.image_id}.png"
            path.write_bytes(candidate.png)
            paths[candidate.image_id] = str(path.relative_to(output_dir)).replace("\\", "/")
        else:
            paths[candidate.image_id] = None

    records: list[ImageRecord] = []
    drafts: list[ImageBlockDraft] = []
    calls: list[tuple[str, VisionResult]] = []
    cache_hits = 0
    cache_misses = 0
    for candidate in candidates:
        base: dict[str, Any] = {
            "image_id": candidate.image_id,
            "page": candidate.page,
            "width_px": candidate.width_px,
            "height_px": candidate.height_px,
            "sha256": candidate.sha256,
            "bbox": candidate.bbox,
        }
        if candidate.error is not None:
            records.append(ImageRecord(status="failed", **base))
            continue
        if candidate.skip_reason == "duplicate":
            canonical = records_by_id.get(candidate.canonical_image_id or "")
            record = ImageRecord(
                status="skipped",
                skip_reason="duplicate",
                canonical_image_id=candidate.canonical_image_id,
                path=canonical.path if canonical else None,
                description=canonical.description if canonical else None,
                **base,
            )
            records.append(record)
            if canonical and canonical.description:
                drafts.append(_figure_draft(record, canonical.description, bbox=candidate.bbox))
            continue
        if candidate.skip_reason is not None:
            records.append(ImageRecord(status="skipped", skip_reason=candidate.skip_reason, **base))
            continue
        if not describe or backend is None:
            record = ImageRecord(
                status="skipped",
                skip_reason="vision_disabled",
                path=paths.get(candidate.image_id),
                **base,
            )
            records.append(record)
            drafts.append(
                _figure_draft(
                    record,
                    "Vision description disabled for this pipeline.",
                    bbox=candidate.bbox,
                )
            )
            records_by_id[candidate.image_id] = record
            continue
        try:
            cache_key = vision_cache_key(
                candidate.sha256,
                prompt_id,
                getattr(backend, "model", "unknown"),
                cache_config if cache_config is not None else {},
            )
            cached = cache.get("vision-image", cache_key) if cache is not None else None
            if cached is not None:
                result = VisionResult.model_validate(cached)
                cache_hits += 1
            else:
                result = backend.describe_image(candidate.png or b"", prompt_id=prompt_id)
                cache_misses += 1
                if cache is not None:
                    cache.put("vision-image", cache_key, result.model_dump(mode="json"))
            if not result.text.strip():
                raise VisionError(f"vision returned an empty description for {candidate.image_id}")
            record = ImageRecord(
                status="described",
                path=paths.get(candidate.image_id),
                description=result.text,
                usage=result.usage,
                **base,
            )
            records.append(record)
            records_by_id[candidate.image_id] = record
            calls.append((candidate.image_id, result))
            drafts.append(
                _figure_draft(
                    record,
                    result.text,
                    data_uris.get(candidate.image_id),
                    candidate.bbox,
                )
            )
        except Exception:
            record = ImageRecord(status="failed", path=paths.get(candidate.image_id), **base)
            records.append(record)
            records_by_id[candidate.image_id] = record
            drafts.append(
                ImageBlockDraft(
                    image_id=candidate.image_id,
                    page=candidate.page,
                    markdown=f"<!-- image {candidate.image_id}: description failed -->",
                    text="",
                    source_path=record.path,
                    bbox=candidate.bbox,
                )
            )
    return ImageProcessingResult(
        records=records,
        blocks=drafts,
        calls=calls,
        cache_hits=cache_hits,
        cache_misses=cache_misses,
    )


def place_image_drafts(pages: list[PageResult], drafts: list[ImageBlockDraft]) -> list[PageResult]:
    by_page: dict[int, list[ImageBlockDraft]] = {}
    for draft in drafts:
        by_page.setdefault(draft.page, []).append(draft)
    output = list(pages)
    for page_number, page_drafts in by_page.items():
        page = next((item for item in output if item.page == page_number), None)
        if page is None:
            continue
        blocks = list(page.blocks)
        for draft in page_drafts:
            block = Block(
                block_id=f"p{draft.page:04d}-b{len(blocks) + 1:03d}",
                type="figure",
                markdown=draft.markdown,
                text=draft.text,
                provenance=Provenance(page=draft.page, source="vision", bbox=draft.bbox),
                meta={"image_id": draft.image_id},
            )
            insert_at = len(blocks)
            if draft.bbox is not None:
                insert_at = 0
                for index, existing in enumerate(blocks):
                    bbox = existing.provenance.bbox
                    if bbox is None or bbox.y1 <= draft.bbox.y0:
                        insert_at = index + 1
            blocks.insert(insert_at, block)
        output[output.index(page)] = page.model_copy(update={"blocks": blocks})
    return output
