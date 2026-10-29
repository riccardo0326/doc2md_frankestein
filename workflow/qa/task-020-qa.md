# QA report — task-020 — Harden image rendering and deterministic output

## STATUS: PASS-WITH-NOTES
Reviewed: 2026-10-28

## Task criteria
| Criterion | Result | Notes |
|---|---|---|
| Filters are configuration-driven and records explain skips | PASS | Boundary tests cover inclusive minimums, aspect equality, and no backend calls for skips. |
| SHA-256 dedupe is stable across pages/runs | PASS | Existing cross-page test and repeated-output test verify one canonical asset/call. |
| Asset names and paths are deterministic/platform-safe | PASS | Repeated conversion compares PNG bytes, Markdown, and sidecar JSON. |
| Figure content and ordering are deterministic | PASS | Placement matrix covers positioned, unknown-bbox, and page-local drafts. |
| Render failures are explicit and isolated | PASS | Failed records now receive a stable `render failed` placeholder with no vision call. |
| AnyDoc failure uses only configured pdfplumber fallback | PASS | Existing fallback integration remains green. |

## Technical quality
| Check | Result |
|---|---|
| Build/tests | PASS: 74 passed, 2 skipped |
| Type check | PASS-WITH-NOTES |
| Lint | PASS |
| No debug statements | PASS |
| Edge cases handled | PASS |

The exact `python -m mypy src` invocation is blocked by installed NumPy stubs
that use Python 3.12 syntax while the project configuration targets Python 3.11.
The source passes `python -m mypy --python-version 3.12 src`; this matches the
existing task-015 workstation note.

## Strategy alignment
Replace-the-edge strategy: consistent. The hardening remains in the existing
Python image adapter and does not add OCR, hosted fallback, or corpus-specific rules.

User goal served: yes — image output is deterministic and render failures remain
visible without sacrificing unrelated page conversion.

## Blockers
-

## Suggestions (non-blocking)
- Keep task-021 limited to optional Kelpie and authorized corpus evidence.

## Approved for git
[ ] Human approved — proceed to commit
