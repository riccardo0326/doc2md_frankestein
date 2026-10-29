# task-024 - Preserve source order for overlapping image figures

## What to build

Make `place_image_drafts()` deterministic and source-order preserving when
multiple image drafts share or overlap the same vertical band, while retaining
the existing bbox-relative placement for distinct figures and page-local
provenance.

## Why

The real Kelpie trial described three same-band figures correctly but emitted
them in reverse order around the AnyDoc text block. The current output loses the
source image sequence even though IDs, assets, and descriptions are present.

## Relevant files

Read before starting:
- `src/doc2md/converters/pdf/images.py` - current draft placement algorithm.
- `src/doc2md/models.py` - block, bbox, and image draft contracts.
- `src/doc2md/render/markdown.py` - block rendering order.
- `tests/test_images.py` - existing placement expectations.
- `tests/test_hybrid_images.py` and `tests/test_image_robustness.py` - integration and boundary fixtures.

Create:
- `tests/test_image_placement_order.py` - same-band, overlapping, distinct-band, unknown-bbox, and multi-page ordering tests.

Modify:
- `src/doc2md/converters/pdf/images.py` - only the general placement algorithm.
- `tests/test_images.py` - strengthen existing placement assertions if needed.

## Test-First Steps

1. Add a failing integration assertion for three same-band images expecting `i01`, `i02`, `i03` order.
2. Add failing tests for overlapping bboxes, unknown text bboxes, distinct vertical bands, and two pages.
3. Implement stable insertion using existing page order, bbox data, and draft order; do not branch on filenames or page numbers.
4. Re-run the real synthetic image integration and compare block IDs, Markdown, and sidecar order.

## Acceptance criteria

- [x] Same-band image drafts preserve candidate order.
- [x] Distinct vertical bands remain relative to the correct preceding block.
- [x] Unknown-bbox text does not cause later image drafts to reverse or cross pages.
- [x] Figure block IDs, image IDs, bbox provenance, Markdown, and sidecar order are deterministic.
- [x] Existing placement and failure-placeholder tests remain green.

## Edge cases to handle

- When bboxes overlap: preserve stable draft order rather than infer a false ordering.
- When an existing block has no bbox: retain it page-locally without treating it as a positioned block.
- When several drafts share a page: never use equality or object identity in a way that can replace the wrong page.

## Do not touch

- Image filtering, cache keys, Kelpie calls, AnyDoc normalization, or router policy.

## Definition of done

- [x] Failing-first placement tests pass.
- [x] `python -m pytest -q` passes.
- [x] `python -m ruff check src tests` passes.
- [x] `python -m mypy src` passes, or the known environment limitation is recorded.
- [x] No corpus-specific ordering rule is added.

## Status

completed

### Verification notes

- `python -m pytest -q tests/test_image_placement_order.py`: 4 passed.
- `python -m pytest -q tests/test_images.py tests/test_hybrid_images.py tests/test_image_robustness.py tests/test_image_placement_order.py`: 17 passed.
- `python -m pytest -q`: 88 passed, 4 skipped.
- `python -m ruff check src tests`: passed.
- `python -m mypy src`: blocked only by the installed NumPy stub Python 3.12 `type` syntax; `python -m mypy --python-version 3.12 src`: passed.
