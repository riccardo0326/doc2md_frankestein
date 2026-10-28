# task-006 - Assemble the hybrid tiered converter

## What to build

Implement the document conversion loop that routes `TEXT` pages to AnyDoc, records `COMPLEX` and `SCANNED` pages as explicit hard-path work, preserves page-level failure isolation, and writes Markdown plus the JSON sidecar. Keep the old pdfplumber extractor only as an explicit emergency fallback.

## Why

This is the first end-to-end Frankenstein slice: Rust handles ordinary digital pages while the architecture keeps a seam for Kelpie hard pages.

## Relevant files

Read before starting:

- `MIGRATION-PLAN.md` target architecture and rollback
- `src/doc2md/models.py`
- `src/doc2md/converters/pdf/anydoc.py`
- `src/doc2md/converters/pdf/source.py`
- `src/doc2md/converters/pdf/router.py`
- old `src/doc2md/api.py` for behavior reference only

Create:

- `src/doc2md/converters/pdf/__init__.py`
- `tests/test_hybrid_converter.py`
- `tests/fixtures` synthetic builders as needed

Modify:

- `src/doc2md/api.py`
- `src/doc2md/cli.py`
- `src/doc2md/config.py`
- `docs/decisions.md`

## Steps

1. Write an end-to-end failing test for a mixed synthetic PDF.
2. Add the converter loop and dependency injection points.
3. Route `TEXT` to AnyDoc.
4. Emit explicit hard-path placeholders for other classes until Kelpie is wired.
5. Add configured pdfplumber emergency fallback for AnyDoc failures.
6. Write deterministic Markdown and sidecar outputs.

## Acceptance criteria

- [x] Digital text pages use AnyDoc.
- [x] Hard pages never silently use AnyDoc OCR.
- [x] Original page numbers and methods are preserved.
- [x] One page failure does not abort the document.
- [x] `--strict` fails when any page failed.
- [x] Fallback usage is visible in warnings and sidecar output.
- [x] Mixed synthetic conversion is deterministic.

## Edge cases to handle

- When AnyDoc is unavailable: configured fallback or isolated failure, never an implicit network call.
- When a page is skipped by selection: preserve a skipped result with its original number.
- When the output directory is absent: create it deterministically.

## Definition of done

- [x] End-to-end fake-backed tests pass.
- [x] Offline conversion works for digital synthetic PDFs.
- [x] Ruff and mypy pass.
- [x] Phase 1/2 gate is recorded in `docs/decisions.md`.

## Status

completed

### Dev notes
Files created:
- `src/doc2md/converters/pdf/hybrid.py`
- `tests/test_hybrid_converter.py`

Files modified:
- `src/doc2md/converters/pdf/__init__.py`
- `src/doc2md/api.py`
- `src/doc2md/cli.py`
- `src/doc2md/config.py`
- `docs/decisions.md`
- `MIGRATION-PLAN.md`
- `workflow/ROADMAP.md`
- `workflow/tasks/task-005-inspection-routing.md`
- `workflow/tasks/task-006-hybrid-converter.md`

Deviations from spec (if any):
- The emergency pdfplumber path is an explicit injected callable; no hidden
  legacy extractor was copied into the new workspace.
- Hard extraction remains an explicit injected seam and reports isolated failure
  until the later Kelpie hard-path task.

Verification:
- Base environment: `28 passed, 1 skipped`; Ruff and mypy pass.
- Mixed synthetic PDF preserves original pages, methods, warnings, fallback,
  strict failure behavior, Markdown, and JSON/run sidecars.

Suggestions for follow-up (do not act on these):
- Wire the approved hard extractor contract only in the next task.
- Keep cache, metrics, and image behavior out of this slice until their tasks.
