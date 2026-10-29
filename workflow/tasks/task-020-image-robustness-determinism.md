# task-020 - Harden image rendering and deterministic output

## Objective

Complete the general image regression matrix for crop rendering, size/area/
aspect-ratio filters, SHA-256 deduplication, stable saving, placement, and
failure placeholders. Verify that a rendering failure is isolated as a failed
image record and does not trigger an implicit OCR, vision, or alternate parser
fallback; retain the explicit `pdfplumber` fallback only for AnyDoc text
extraction failures.

## Why

The standalone tests prove the happy path, but end-to-end integration must not
turn malformed image geometry or renderer failures into lost pages,
nondeterministic assets, or untracked content.

## Dependencies And Initial State

- Depends on `task-017`, `task-018`, and `task-019`.
- Initial status: `planned`; it becomes `ready` only after all dependencies pass
  QA.

## Files To Read

- `docs/limitations.md` - required filtering, crop, placement, and fallback
  behavior.
- `docs/decisions.md` - D012, D014, and D015.
- `src/doc2md/converters/pdf/images.py` - renderer, filters, IDs, and drafts.
- `src/doc2md/converters/pdf/hybrid.py` - page failure and fallback isolation.
- `src/doc2md/models.py` - image and block constraints.
- `src/doc2md/render/markdown.py` - failure marker behavior.
- `tests/test_images.py`, `tests/test_hybrid_images.py`, and
  `tests/test_image_telemetry.py` - existing integration coverage.

## Files To Create

- `tests/test_image_robustness.py` - boundary and repeated-output regression
  matrix using synthetic pages/PDFs only.

## Files To Modify

- `src/doc2md/converters/pdf/images.py` - only general fixes proven by a
  failing test; add the deterministic failure placeholder only if the
  integration test proves the current failed-record path lacks one, and keep
  the existing API and explicit failure records.
- `src/doc2md/converters/pdf/hybrid.py` - only if a general orchestration fix is
  needed for isolation or output ordering.
- `tests/test_images.py` - consolidate or strengthen existing unit assertions
  without duplicating the entire integration matrix.

## Test-First Steps

1. Add failing boundary tests for minimum width, minimum height, minimum area,
   and maximum aspect ratio, including equality at the configured boundary.
2. Add a failing repeated-output test: identical input/configuration produces
   byte-identical PNG assets, Markdown, image IDs, and sidecar JSON.
3. Add a failing placement matrix with blocks above, below, and without
   bounding boxes; assert figures are inserted after the correct preceding
   block and remain page-local.
4. Add a failing crop-render exception test; assert one failed `ImageRecord`, a
   stable failure marker, no vision call, and successful processing of another
   image/page.
5. Run the matrix with a fake renderer and fake backend offline; use the real
   `pypdfium2` renderer only in the optional environment when available.
6. Apply only the smallest reusable fixes and document any unresolved geometry
   limitation rather than adding a sample-specific branch.

## Acceptance Criteria

- [x] Filter decisions are configuration-driven and recorded as
  `too_small`/`bad_aspect` without backend calls.
- [x] SHA-256 deduplication is stable across pages and runs, with one canonical
  saved asset and one description call.
- [x] Saved asset names and relative paths are deterministic and platform-safe.
- [x] Figure Markdown, descriptions, bboxes, and ordering are deterministic.
- [x] Crop/render failures are represented explicitly and do not abort the
  document or invoke an unapproved fallback.
- [x] AnyDoc failure still uses only the configured `pdfplumber` fallback, with
  its existing warning and method provenance.

## Edge Cases

- When crop coordinates are outside page bounds, clamp safely or record a
  failure; never write an invalid crop silently.
- When a crop has zero width or height, record a failed image and continue.
- When a duplicate's canonical description failed, retain the duplicate
  relationship but do not invent a description.
- When output directories are recreated, no stale temporary file or absolute
  path remains in the result.

## Definition Of Done

- [x] Offline robustness and determinism tests pass.
- [x] Full test suite, Ruff, and mypy pass.
- [x] `python -m pytest -q` passes.
- [x] `python -m ruff check src tests` passes.
- [x] `python -m mypy src` passes.
- [x] No PDF-derived bytes, model output, credentials, or tokens are committed.

## Status

completed

### Dev notes

Files created:
- `tests/test_image_robustness.py`

Files modified:
- `src/doc2md/converters/pdf/images.py`
- `workflow/tasks/task-020-image-robustness-determinism.md`

Deviations from spec (if any):
- The exact `python -m mypy src` command remains blocked by installed NumPy
  stubs using Python 3.12 syntax under the project Python 3.11 target.
  `python -m mypy --python-version 3.12 src` passes; this is the same
  workstation limitation recorded in task-015 QA.

Suggestions for follow-up (do not act on these):
- Keep the final Kelpie/corpus regression limited to authorized, redacted evidence in task-021.
