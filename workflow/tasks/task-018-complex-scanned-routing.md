# task-018 - Handle COMPLEX images and exclude SCANNED full pages

## Objective

Extend the integrated image stage to eligible `COMPLEX` pages without replacing
the Kelpie hard path, and explicitly exclude full-page images from `SCANNED`
pages. A successful complex page may contain hard-path blocks plus separately
proven embedded figure blocks; a scanned page must use one hard-path page
transcription and must not create an embedded `ImageRecord` for its full-page
image.

## Why

Visual content is not limited to TEXT pages. Complex pages need both truthful
hard-path handling and, where the PDF exposes distinct embedded figures,
figure-level provenance. Scanned full-page images are already the hard path's
input and double processing would duplicate descriptions and tokens.

## Dependencies And Initial State

- Depends on `task-017`.
- Initial status: `planned`; it becomes `ready` only after `task-017` QA.

## Files To Read

- `docs/limitations.md` - COMPLEX and SCANNED behavior.
- `docs/decisions.md` - D013, D014, and D015.
- `docs/discovery.md` - hard-path and image-bearing page evidence.
- `src/doc2md/converters/pdf/hybrid.py` - route branches and call draining.
- `src/doc2md/converters/pdf/hard.py` - Kelpie page rendering and blocks.
- `src/doc2md/converters/pdf/images.py` - page-class exclusion and placement.
- `src/doc2md/vision/base.py` and `src/doc2md/vision/fake.py` - method seams.
- `tests/test_kelpie_hard.py`, `tests/test_hybrid_converter.py`, and
  `tests/test_images.py` - hard and image expectations.

## Files To Create

- `tests/test_hybrid_complex_scanned_images.py` - fake hard/vision integration
  tests for complex and scanned pages.

## Files To Modify

- `src/doc2md/converters/pdf/hybrid.py` - run embedded-image processing for
  eligible COMPLEX pages, keep hard extraction authoritative, and preserve
  page-level isolation.
- `src/doc2md/converters/pdf/images.py` - only if a general full-page or class
  exclusion rule is needed; keep `SCANNED` exclusion explicit.
- `tests/test_hybrid_converter.py` - preserve existing route assertions while
  adding complex image expectations if necessary.

## Test-First Steps

1. Add a failing synthetic `COMPLEX` fixture with a hard-path fake returning a
   page block and an embedded figure with a bounding box.
2. Assert the hard block remains present, the figure has `vision` provenance,
   and the two backend methods are observable as separate, intentional calls.
3. Add a failing synthetic `SCANNED` fixture with a full-page image and a fake
   hard backend; assert `transcribe_page()` is called once and
   `describe_image()` is never called for that image.
4. Assert the scanned document has no embedded `ImageRecord` for the full-page
   image and no duplicate image file.
5. Add failure-isolation tests for hard failure and image failure on different
   pages.
6. Implement only the route-aware orchestration; do not alter router thresholds
   or the Kelpie request contract.

## Acceptance Criteria

- [ ] Eligible `COMPLEX` pages preserve hard-path output and can add embedded
  figure records/blocks without changing the route class.
- [ ] `SCANNED` pages never pass their full-page image to
  `VisionBackend.describe_image()` or the embedded-image stage.
- [ ] Hard-page usage remains a `transcribe_page` record and image usage remains
  a `describe_image` record; neither is relabelled.
- [ ] One failing hard or image operation affects only its page/asset and does
  not abort unrelated pages.
- [ ] `full-vision` and `docling-only` comparison policies retain their current
  explicit image-disabled behavior.

## Edge Cases

- When a COMPLEX page has no distinct embedded images, only the hard path runs.
- When a complex hard transcription fails, its page warning/error is retained;
  image failures must not be converted into a successful hard result.
- When a scanned page contains several XObjects representing one full-page
  render, none are described by the embedded-image stage.
- When a page is unselected, it remains skipped and cannot trigger a rendering,
  hard, or image call.

## Definition Of Done

- [ ] Fake-backed complex/scanned tests pass without network access.
- [ ] Existing hard, image, hybrid, and pipeline tests remain green.
- [ ] `python -m pytest -q` passes.
- [ ] `python -m ruff check src tests` passes.
- [ ] `python -m mypy src` passes.
- [ ] No full-page or document-specific heuristic is introduced.

## Status

planned
