# task-005 - Implement PDF inspection and routing

## What to build

Implement pure per-page PDF signals and configurable routing for `TEXT`, `COMPLEX`, and `SCANNED` pages using pdfplumber only. Add the `inspect` library function and CLI output, without invoking AnyDoc or Kelpie during inspection.

## Why

The hybrid pipeline must decide per page before selecting a parser. Keeping inspection pure makes misrouting explainable and testable.

## Relevant files

Read before starting:

- `C:\Users\rp99480\dev\doc2md\ARCHITECTURE.md` sections 6.2 and 9
- `MIGRATION-PLAN.md` routing policy
- `src/doc2md/models.py`
- `src/doc2md/errors.py`

Create:

- `src/doc2md/config.py`
- `src/doc2md/converters/pdf/signals.py`
- `src/doc2md/converters/pdf/router.py`
- `src/doc2md/converters/pdf/source.py`
- `tests/test_signals.py`
- `tests/test_router.py`

Modify:

- `src/doc2md/cli.py`
- `src/doc2md/api.py`
- `docs/decisions.md`

## Steps

1. Add table-driven signal tests with synthetic signal dictionaries.
2. Implement configurable signal extraction from pdfplumber.
3. Implement first-match routing rules and human-readable reasons.
4. Add `inspect_pdf` and machine-readable CLI output.
5. Add synthetic text, table, image-heavy, and scanned fixtures.

## Acceptance criteria

- [x] Signals include text, images, tables, garbling, and text-layer presence.
- [x] Router returns the expected class and reason for every fixture.
- [x] Thresholds can be overridden through configuration.
- [x] Inspection does not import AnyDoc, Docling, or Kelpie.
- [x] Page numbers are 1-based and original.
- [x] `doc2md inspect` produces stable output.

## Edge cases to handle

- When a page is blank: classify it deterministically without vision.
- When table extraction is unreliable: route according to the documented conservative rule.
- When PDF access fails: return a typed source error.

## Definition of done

- [x] Tests, Ruff, and mypy pass.
- [x] CLI help and output are accurate.
- [x] Decisions and thresholds are documented.

## Status

completed

### Dev notes
Files created:
- `src/doc2md/config.py`
- `src/doc2md/converters/pdf/signals.py`
- `src/doc2md/converters/pdf/router.py`
- `src/doc2md/converters/pdf/source.py`
- `tests/test_signals.py`
- `tests/test_router.py`
- `tests/test_inspection.py`

Files modified:
- `pyproject.toml`
- `src/doc2md/__init__.py`
- `src/doc2md/api.py`
- `src/doc2md/cli.py`
- `docs/decisions.md`
- `MIGRATION-PLAN.md`
- `workflow/ROADMAP.md`
- `workflow/tasks/task-004-anydoc-adapter.md`
- `workflow/tasks/task-005-inspection-routing.md`

Deviations from spec (if any):
- The CLI exposes `--min-chars` as the first explicit threshold override; all
  router thresholds remain configurable through `RouterConfig`.
- Table extraction failures are marked irregular and therefore route
  conservatively to `COMPLEX`.

Verification:
- Base environment: `24 passed, 1 skipped`; Ruff and mypy pass.
- No AnyDoc, Docling, or Kelpie import occurs during inspection.

Suggestions for follow-up (do not act on these):
- Connect inspection decisions to the standalone extractors only in the next
  task.
