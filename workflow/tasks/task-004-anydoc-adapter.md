# task-004 - Implement the AnyDoc page adapter

## What to build

Implement a lazy, optional `AnyDocFastExtractor` that accepts an in-memory one-page PDF, calls the local AnyDoc Python binding, and returns one canonical Markdown block with original page provenance. It must use the page-slicing method verified in Phase 0 and never invoke hosted Firecrawl OCR.

## Why

This is the Rust replacement for the fragile Python fast parser. It must be independently testable before it is connected to routing or production conversion.

## Relevant files

Read before starting:

- `docs/discovery.md` for the verified AnyDoc import and page-slicing API
- `MIGRATION-PLAN.md` sections Ownership rules and Page Granularity
- `src/doc2md/models.py`
- `src/doc2md/errors.py`

Create:

- `src/doc2md/converters/pdf/anydoc.py`
- `tests/test_anydoc_adapter.py`
- `tests/test_anydoc_integration.py`

Modify:

- `pyproject.toml` with an optional AnyDoc dependency
- `src/doc2md/converters/pdf/__init__.py`
- `docs/decisions.md`

## Steps

1. Write fake-binding tests for valid, empty, and failing AnyDoc responses.
2. Implement the adapter protocol and lazy import.
3. Implement the validated one-page PDF input bridge.
4. Wrap non-empty Markdown in one `anydoc` block per original page.
5. Add optional integration tests guarded by the AnyDoc marker.
6. Add a network-free assertion for the local path.

## Acceptance criteria

- [x] A digital page produces non-empty Markdown.
- [x] Original page number and stable block ID are preserved.
- [x] AnyDoc is not imported at package import time.
- [x] Missing AnyDoc raises a clear optional-dependency error.
- [x] Empty or malformed output raises a typed conversion error.
- [x] Local conversion performs no hosted API call.
- [x] Offline tests pass without AnyDoc installed.

## Edge cases to handle

- When page slicing changes page resources: record the limitation and fail the adapter rather than returning misleading output.
- When AnyDoc reports OCR is needed: return a hard-path handoff error; do not enable hosted OCR.
- When Markdown contains multiple structures: preserve the raw Markdown in the block.

## Definition of done

- [x] Adapter contract tests pass.
- [x] Optional integration tests pass when the dependency is installed.
- [x] Ruff and mypy pass.
- [x] No routing or default-pipeline behavior changed.

## Status

completed

### Dev notes
Files created:
- `src/doc2md/converters/__init__.py`
- `src/doc2md/converters/pdf/__init__.py`
- `src/doc2md/converters/pdf/anydoc.py`
- `tests/test_anydoc_adapter.py`
- `tests/test_anydoc_integration.py`

Files modified:
- `pyproject.toml`
- `src/doc2md/errors.py`
- `docs/decisions.md`
- `MIGRATION-PLAN.md`
- `workflow/ROADMAP.md`
- `workflow/tasks/task-003-output-contract.md`
- `workflow/tasks/task-004-anydoc-adapter.md`

Deviations from spec (if any):
- The adapter accepts an already sliced one-page PDF and validates it with lazy
  pypdf in the optional path; page selection remains Python-owned by the caller.
- The canonical block's `text` equals raw AnyDoc Markdown because the adapter
  must not reinterpret the parser's Markdown or invent semantic structure.

Verification:
- Base `.[dev]`: 12 passed, 1 skipped; Ruff and mypy pass.
- Optional `.[dev,anydoc]`: 13 passed; real AnyDoc conversion and no-network
  integration assertion pass.

Suggestions for follow-up (do not act on these):
- Connect this standalone extractor to routing only in the next task.
- Keep the hard-path handoff and optional import boundary unchanged.
