# task-008 - Add image extraction and descriptions

## What to build

Implement embedded-image discovery, filtering, hashing, saving, placement, and optional Kelpie descriptions for digital pages. Keep scanned full-page images on the hard-page path rather than treating them as embedded figures.

## Why

Images carry information that text extraction cannot preserve. Filtering and deduplication prevent unnecessary Kelpie calls and token use.

## Relevant files

Read before starting:

- `C:\Users\rp99480\dev\doc2md\ARCHITECTURE.md` section 6.4
- `src/doc2md/models.py`
- `src/doc2md/vision/base.py`
- `src/doc2md/converters/pdf/__init__.py`
- old `src/doc2md/converters/pdf/images.py` for behavior reference only

Create:

- `src/doc2md/converters/pdf/images.py`
- `tests/test_images.py`
- `prompts/describe_image.v1.txt`

Modify:

- `src/doc2md/converters/pdf/__init__.py`
- `src/doc2md/config.py`
- `docs/decisions.md`

## Steps

1. Write tests for large, tiny, extreme-aspect, duplicate, and failed images.
2. Implement image extraction from the validated page source.
3. Implement configuration-driven filtering and SHA-256 deduplication.
4. Save kept images under the output directory with stable IDs.
5. Call the injected vision backend with the versioned prompt.
6. Insert image blocks after the correct preceding page block.

## Acceptance criteria

- [x] Tiny and invalid images are recorded as skipped with reasons.
- [x] Duplicate images produce one description call.
- [x] Kept images are saved with deterministic names.
- [x] Descriptions are inline and linked to the correct page.
- [x] Usage is recorded for every description call.
- [x] Image failures do not abort document conversion.
- [x] Scanned full-page images are not double-described.

## Edge cases to handle

- When image bytes cannot be rendered: record a failed image record.
- When the output directory is in-memory only: retain description data without writing files.
- When the vision backend is disabled: record `vision_disabled` explicitly.

## Definition of done

- [x] Fake vision tests pass offline.
- [x] Image placement and sidecar golden tests pass.
- [x] Ruff and mypy pass.
- [x] Decisions document the scanned-page behavior.

## Status

completed

### Dev notes
Files created:
- `src/doc2md/converters/pdf/images.py`
- `tests/test_images.py`
- `prompts/describe_image.v1.txt`

Files modified:
- `src/doc2md/models.py`
- `src/doc2md/config.py`
- `src/doc2md/converters/pdf/__init__.py`
- `docs/decisions.md`
- `MIGRATION-PLAN.md`
- `workflow/ROADMAP.md`
- `workflow/tasks/task-007-kelpie-hard-path.md`
- `workflow/tasks/task-008-image-pipeline.md`

Deviations from spec (if any):
- Image description concurrency is kept deterministic and sequential in this
  slice; bounded concurrency remains a later metrics/performance concern.
- Image cache integration is intentionally deferred to its dedicated task.

Verification:
- Offline suite: `37 passed, 2 skipped`; Ruff and mypy pass.
- Fake image backend covers filtering, dedupe, saving, usage, placement,
  failures, vision-disabled behavior, and scanned-page exclusion.

Suggestions for follow-up (do not act on these):
- Integrate image drafts into the hybrid assembly only with the metrics/cache
  contract kept explicit.
