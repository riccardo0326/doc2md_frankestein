# task-016 - Define the image-stage integration seam

## Objective

Create the explicit Python-owned adapter seam that allows `PdfConverter` to
invoke the existing image functions with an original `pdfplumber` page, an
original 1-based page number, an optional renderer, an optional vision backend,
an output directory, and the run cache. Keep the existing
`ImageProcessingResult` and `VisionBackend` contracts; do not connect the seam
to normal conversion yet.

## Why

The standalone image pipeline is already tested, but the converter has no
dependency-injected way to provide page/rendering context or consume its
result. A small explicit seam prevents hidden imports, hidden network calls,
and document-specific branching in later integration tasks.

## Dependencies And Initial State

- Depends on the `task-015` review gate and Phase 0 sign-off.
- Initial status: `planned`; it becomes `ready` only after the `task-015` review
  gate is accepted.
- This task is planned only in this branch and is not started by the planning
  phase.

## Files To Read

- `MIGRATION-PLAN.md` - ownership, fallback, and security boundaries.
- `workflow/PROJECT.md` - commands and adapter conventions.
- `docs/discovery.md` - rendering, page provenance, and Kelpie evidence.
- `docs/decisions.md` - decisions D002, D006, D014, and D015.
- `src/doc2md/converters/pdf/images.py` - existing image-stage functions and
  `ImageProcessingResult`.
- `src/doc2md/converters/pdf/source.py` - original page lifetime.
- `src/doc2md/config.py` - `ImageConfig` and cache configuration.
- `src/doc2md/models.py` - image, block, and provenance models.
- `src/doc2md/vision/base.py` and `src/doc2md/vision/fake.py` - vision seam.
- `tests/test_images.py` and `tests/conftest.py` - existing fake conventions.

## Files To Create

- `tests/test_image_stage.py` - failing-first adapter and lifecycle tests.
- `tests/fixtures/pdf_images.py` - in-memory page/image fixture helpers, if a
  shared helper is needed.

## Files To Modify

- `src/doc2md/converters/pdf/images.py` - add only the minimal explicit adapter
  or callable required to reuse the existing functions; preserve their public
  behavior.
- `tests/test_images.py` - only when an existing assertion must document the
  seam rather than add duplicated coverage.

## Test-First Steps

1. Add a failing test proving a fake page and injected renderer reach
   `collect_images()` with the original page number and page class.
2. Add a failing test proving an injected fake vision backend and cache can be
   passed through to `process_images()` without importing Kelpie or opening a
   PDF path.
3. Add a failing lifecycle test for a default renderer owner: resources are
   closed after processing and an absent optional renderer dependency produces
   an explicit typed failure.
4. Implement the smallest adapter around the existing functions.
5. Re-run the existing standalone image tests and assert no behavior changes in
   filtering, deduplication, failure records, or placement.

## Acceptance Criteria

- [ ] The seam accepts original page number and page class without deriving
  either from a filename or a page-specific rule.
- [ ] Tests can inject a renderer and a fake backend entirely offline.
- [ ] The default renderer remains lazy and does not install or invoke local
  OCR/model artifacts.
- [ ] `ImageProcessingResult` remains the source of records, drafts, calls,
  cache hits, and cache misses.
- [ ] No Kelpie request field, response field, or retry rule is added.
- [ ] Existing `tests/test_images.py` behavior remains green.

## Edge Cases

- When no output directory is supplied, descriptions remain available in the
  result and no absolute asset path is invented.
- When the optional renderer is unavailable, report an explicit error to the
  caller; do not fall back to hosted OCR.
- When the same SHA-256 is seen again, preserve the first canonical ID and do
  not add a second description call.
- When page class is `SCANNED`, the adapter must be able to pass that fact to
  the existing exclusion rule without deciding routing itself.

## Definition Of Done

- [ ] Test-first seam tests pass offline.
- [ ] Existing image unit tests pass unchanged or with justified contract
  assertions only.
- [ ] `python -m pytest -q` passes.
- [ ] `python -m ruff check src tests` passes.
- [ ] `python -m mypy src` passes.
- [ ] No debug output, secrets, PDF bytes, model responses, or generated
  artifacts are committed.

## Status

planned
