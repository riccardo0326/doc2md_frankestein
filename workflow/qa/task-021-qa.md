# QA report — task-021 — Run optional Kelpie and authorized read-only regressions

## STATUS: PASS-WITH-NOTES
Reviewed: 2026-10-28

## Task criteria
| Criterion | Result | Notes |
|---|---|---|
| Offline fake matrix covers TEXT, COMPLEX, SCANNED, disabled/cache/failure/determinism behavior | PASS | Existing image-context matrix plus the new offline matrix run without network. |
| Kelpie probe is safely skipped without approved variables and uses only `describe_image` when enabled | PASS | New marker-guarded module skipped; its enabled path uses the existing method and typed result fields only. |
| Authorized PDFs are read-only from the exact permitted path | PASS-WITH-NOTES | The opt-in test is guarded and skipped because the opt-in variable was not set; no alternate path was used. |
| Aggregate evidence avoids names, excerpts, outputs, credentials, and token values | PASS | Tests retain only counters/categories; documentation records the environment limitation. |
| Full checks pass and optional failures are isolated | PASS-WITH-NOTES | 75 passed, 4 skipped; optional modules are independently guarded. |
| No cutover claim or fallback removal | PASS | D022 explicitly keeps the enterprise cutover pending and preserves pdfplumber fallback. |

## Technical quality
| Check | Result |
|---|---|
| Build/tests | PASS: 75 passed, 4 skipped |
| Type check | PASS-WITH-NOTES |
| Lint | PASS |
| No debug statements | PASS |
| Edge cases handled | PASS |

The exact `python -m mypy src` invocation is blocked by installed NumPy stubs
that use Python 3.12 syntax while the project configuration targets Python 3.11.
The source passes `python -m mypy --python-version 3.12 src`; this matches the
existing task-015 workstation note.

## Strategy alignment
Replace-the-edge strategy: consistent. Optional real integrations remain guarded,
while synthetic tests establish the contract without hosted OCR or local models.

User goal served: yes — the image-context integration is regression-covered and
its real-environment limits are explicit rather than overstated.

## Blockers
-

## Suggestions (non-blocking)
- Execute the two skipped checks only with the approved Kelpie environment or exact authorized corpus opt-in.

## Approved for git
[ ] Human approved — proceed to commit
