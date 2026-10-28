# task-013 - Harden against the permitted corpus

## What to build

Run the complete synthetic matrix and permitted EDAG corpus through the hybrid pipeline and fix only general parser, routing, provenance, and rendering defects. Add regression tests for every discovered class of failure without adding document-specific rules.

## Why

The migration must be robust beyond the synthetic happy path while preserving the rule that confidential samples and filenames never become hidden code inputs.

## Relevant files

Read before starting:

- `MIGRATION-PLAN.md` quality and cutover gates
- `docs/discovery.md` corpus manifest
- `src/doc2md/converters/pdf`
- `tests/`
- existing quality reports in the old repository, as read-only evidence

Create:

- `tests/test_corpus_regressions.py`
- `docs/corpus-results.md`

Modify:

- General parser/router/renderer files only where a failing case proves a reusable rule.
- `docs/decisions.md`

## Steps

1. Run the synthetic matrix with cold cache.
2. Run the permitted corpus without copying confidential PDFs into Git.
3. Group failures by general cause.
4. Write failing regression tests using synthetic or anonymised fixtures.
5. Implement the smallest general fix.
6. Re-run the full matrix and record before/after evidence.

## Acceptance criteria

- [x] Text, columns, tables, figures, ligatures, German text, blank pages, and mixed scans are covered.
- [x] Page provenance remains correct after every fix.
- [x] AnyDoc, pdfplumber fallback, and Kelpie methods remain visible.
- [x] No filename-, page-, or sample-specific branch exists.
- [x] Failed pages remain isolated.
- [x] Corpus results and limitations are documented without confidential content.

## Edge cases to handle

- When a corpus file cannot be opened: record it and continue the suite.
- When a quality defect has no safe general fix: record it as a known limitation.
- When a change affects output: update the relevant golden test and decision record.

## Definition of done

- [x] Full offline test suite passes.
- [x] Corpus regression report is reproducible.
- [x] Ruff and mypy pass.
- [x] No confidential bytes or model responses were committed.

## Status

completed

### Dev notes
Files created:
- `tests/test_corpus_regressions.py`
- `docs/corpus-results.md`

Files modified:
- `docs/decisions.md`
- `MIGRATION-PLAN.md`
- `workflow/ROADMAP.md`
- `workflow/tasks/task-012-quality-review.md`
- `workflow/tasks/task-013-corpus-hardening.md`

Deviations from spec (if any):
- No production parser fix was justified by the permitted corpus run. Complex
  and scanned failures are documented as the existing hard-path wiring limit.
- Corpus PDFs and generated outputs remained outside the repository.

Verification:
- Full offline suite: `53 passed, 2 skipped`; Ruff and mypy pass.
- Six authorized PDFs were inspected read-only with aggregate results recorded
  in `docs/corpus-results.md`.

Suggestions for follow-up (do not act on these):
- Wire the hard extractor into the default hybrid assembly before making quality
  claims for complex/scanned pages.
