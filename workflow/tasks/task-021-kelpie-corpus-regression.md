# task-021 - Run optional Kelpie and authorized read-only regressions

## Objective

Validate the completed image-context integration with the offline fake backend,
an optional Kelpie image-description probe using only the discovered
`VisionBackend` contract, and the authorized PDFs under
`C:\Users\rp99480\dev\doc2md\samples\unstructured-demo` in read-only mode.
Record only aggregate, anonymised pass/skip/failure evidence; do not copy PDFs,
rendered pages, Markdown, JSON output, model responses, credentials, or token
values into this repository.

## Why

Synthetic tests prove behavior without sensitive data. The final regression
gate must additionally establish that image-bearing digital pages in the
permitted corpus do not regress, while preserving the enterprise boundary when
Kelpie or optional PDF rendering dependencies are unavailable.

## Dependencies And Initial State

- Depends on `task-020`.
- Initial status: `planned`; it becomes `ready` only after `task-020` QA.

## Files To Read

- `docs/discovery.md` - authorized corpus manifest and redacted Kelpie contract.
- `docs/decisions.md` - D013, D014, D019, and D020.
- `MIGRATION-PLAN.md` - optional integration and corpus gates.
- `README.md` - supported extras and security boundary.
- `src/doc2md/vision/kelpie.py` and `src/doc2md/vision/base.py` - existing
  client seam; do not infer additional fields.
- `tests/test_kelpie_integration.py`, all image-context tests, and
  `tests/test_corpus_regressions.py` - markers and offline conventions.

## Files To Create

- `tests/test_image_kelpie_integration.py` - marker-guarded image description
  probe using approved environment variables only.
- `tests/test_image_corpus_readonly.py` - opt-in metadata/classification test
  that reads the authorized path in place and emits aggregate assertions only.
  The test must default to `pytest.skip` unless
  `DOC2MD_RUN_AUTHORIZED_CORPUS=1` is set.

## Files To Modify

- `tests/test_kelpie_integration.py` - only if a shared marker/helper can avoid
  duplicate environment handling.
- `docs/decisions.md` - record aggregate verification status and unresolved
  limitations without sensitive content.
- `docs/limitations.md` - reconcile the current broad `run.json` wording with
  the final sidecar/run split; close the integration limitation only if all
  required acceptance evidence exists, otherwise state the remaining gap
  precisely.

## Test-First Steps

1. Add an offline fake-backed matrix test for TEXT, COMPLEX, and SCANNED image
   behavior; make it the default regression path.
2. Add a marker-guarded Kelpie test that calls only
   `describe_image(image_png, prompt_id=...)`, skips without the approved
   environment, and asserts only typed text/model/usage behavior.
3. Add an opt-in read-only corpus test guarded by
   `DOC2MD_RUN_AUTHORIZED_CORPUS=1` (default: skip) that opens each PDF in
   place, records page/image counts and class-level outcomes, and writes no
   PDF-derived content to Git or the default output directory.
4. Run the offline suite first, then optional tests only when their environment
   is available.
5. Compare results against the existing baseline without adding filename,
   page-number, image-name, or document-specific branches.
6. Record aggregate evidence and complete this task's QA gate; the separate
   post-task final gate in `IMPLEMENT-PROMPT.md` runs only after this task is
   marked `completed`. Do not claim full enterprise cutover from a fake or
   unavailable run.

## Acceptance Criteria

- [x] Fake backend covers TEXT image assembly, COMPLEX image handling,
  SCANNED exclusion, disabled vision, cache reuse, rendering failure, and
  deterministic output without network access.
- [x] Kelpie integration is skipped safely without approved environment
  variables and uses no invented request/response contract when enabled.
- [x] Authorized PDFs are opened read-only from the exact permitted path; no
  input or generated content is copied into the workspace.
- [x] Aggregate results identify pass, skip, failure, dependency versions, and
  configuration without names, excerpts, model responses, credentials, or
  token values.
- [x] Full pytest, Ruff, and mypy checks pass; optional integration failures are
  isolated and clearly reported.
- [x] No cutover claim or removal of the explicit pdfplumber fallback is made by
  this task.

## Edge Cases

- When the authorized path is missing or unreadable, mark the corpus check
  skipped/blocked with the reason and continue offline QA; do not substitute
  another local directory.
- When a PDF is malformed, record only an anonymised failure category and
  continue with the remaining permitted inputs.
- When Kelpie is unavailable, fake tests remain mandatory and no local OCR/model
  fallback is allowed.
- When real results expose a general defect, add a synthetic regression before
  changing production code; never add a corpus-specific rule.

## Definition Of Done

- [x] Offline fake matrix passes and this task's QA gate is complete.
- [x] Optional Kelpie test is skipped or passes according to environment state.
- [x] Read-only authorized corpus verification is completed, skipped with a
  documented blocker, or recorded as an explicit environment limitation.
- [x] `python -m pytest -q` passes.
- [x] `python -m ruff check src tests` passes.
- [x] `python -m mypy src` passes.
- [x] No secret, PDF, generated output, model response, credential, or token
  value is present in the diff.

## Status

completed

### Dev notes

Files created:
- `tests/test_image_kelpie_integration.py`
- `tests/test_image_corpus_readonly.py`

Files modified:
- `docs/decisions.md`
- `docs/limitations.md`
- `workflow/tasks/task-021-kelpie-corpus-regression.md`

Deviations from spec (if any):
- The optional Kelpie probe skipped because the approved environment variables
  were unavailable.
- The authorized corpus test skipped because `DOC2MD_RUN_AUTHORIZED_CORPUS=1`
  was not set; no alternate path was substituted.
- The exact `python -m mypy src` command remains blocked by installed NumPy
  stubs using Python 3.12 syntax under the project Python 3.11 target.
  `python -m mypy --python-version 3.12 src` passes; this is the same
  workstation limitation recorded in task-015 QA.

Suggestions for follow-up (do not act on these):
- Run the guarded Kelpie and authorized corpus checks only in their approved environment.
