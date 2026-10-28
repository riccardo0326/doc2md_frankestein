# task-007 - Implement the Kelpie hard path

## What to build

Implement the enterprise hard-page adapter that renders selected original pages and calls Kelpie through the discovered `VisionBackend` contract. Parse returned Markdown into common blocks, record usage, and isolate failures. Do not install local OCR or layout models.

## Why

Scanned and visually complex pages need OCR or vision. Kelpie is the approved enterprise inference seam and must remain replaceable and observable.

## Relevant files

Read before starting:

- `docs/discovery.md` and `docs/kelpie-example.md`
- `C:\Users\rp99480\dev\doc2md\ARCHITECTURE.md` sections 6.3, 6.5, 8, and 10
- `src/doc2md/models.py`
- `src/doc2md/converters/pdf/__init__.py`
- `src/doc2md/vision` in the old repository for contract reference only

Create:

- `src/doc2md/vision/base.py`
- `src/doc2md/vision/fake.py`
- `src/doc2md/vision/kelpie.py`
- `tests/test_kelpie_hard.py`
- `tests/test_kelpie_integration.py`
- `prompts/transcribe_page.v1.txt`

Modify:

- `src/doc2md/converters/pdf/hard.py`
- `src/doc2md/converters/pdf/__init__.py`
- `src/doc2md/config.py`
- `docs/decisions.md`

## Steps

1. Write fake-backend tests for headings, paragraphs, lists, tables, empty output, and failure.
2. Implement the protocol and deterministic fake backend.
3. Implement the thin Kelpie client using only discovered request/response evidence.
4. Render only selected pages at configured DPI.
5. Parse Markdown into common blocks with original page numbers.
6. Add retry, timeout, and typed availability behavior from the discovered contract.
7. Add the real integration test guarded by `kelpie` and environment variables.

## Acceptance criteria

- [x] `COMPLEX` and `SCANNED` pages can use Kelpie.
- [x] Kelpie usage and latency are returned in the common result.
- [x] Empty or malformed Markdown fails only the affected page.
- [x] No local OCR/model artifacts are required.
- [x] TLS verification remains enabled.
- [x] Fake tests pass without network access.
- [x] Real integration tests skip safely without approved environment variables.

## Edge cases to handle

- When Kelpie is unreachable: mark the page failed and preserve the document result.
- When a transient error occurs: retry only according to discovered rules.
- When a response has an irregular table: preserve text and record a warning.

## Definition of done

- [x] Hard-page fake end-to-end tests pass.
- [x] Kelpie contract is documented and not invented.
- [x] Ruff and mypy pass.
- [x] `docs/decisions.md` is updated.

## Status

completed

### Dev notes
Files created:
- `src/doc2md/vision/__init__.py`
- `src/doc2md/vision/base.py`
- `src/doc2md/vision/fake.py`
- `src/doc2md/vision/kelpie.py`
- `tests/test_kelpie_hard.py`
- `tests/test_kelpie_integration.py`
- `prompts/transcribe_page.v1.txt`

Files modified:
- `src/doc2md/converters/pdf/hard.py`
- `src/doc2md/converters/pdf/__init__.py`
- `src/doc2md/config.py`
- `pyproject.toml`
- `docs/decisions.md`
- `MIGRATION-PLAN.md`
- `workflow/ROADMAP.md`
- `workflow/tasks/task-006-hybrid-converter.md`
- `workflow/tasks/task-007-kelpie-hard-path.md`

Deviations from spec (if any):
- The thin client supports the verified proxy convention and does not add a
  speculative service-account payload or response field.
- Usage is carried by `VisionResult` and drained by the hard extractor; the
  hybrid loop will consume those call records in the later metrics task.

Verification:
- Fake/offline suite: `33 passed, 2 skipped`; Ruff and mypy pass.
- Kelpie integration skipped safely without approved environment variables.
- Real local proxy verification: `1 passed` with `DARE-NoCloud-Helios` on
  2026-10-28; response content was handled without storing model output.

Suggestions for follow-up (do not act on these):
- Connect `drain_calls()` to the metrics collector only in the metrics task.
- Wire the hard extractor into the hybrid converter after review.
