# QA report — task-018 — Handle COMPLEX images and exclude SCANNED full pages

## STATUS: PASS-WITH-NOTES
Reviewed: 2026-10-28

## Task criteria
| Criterion | Result | Notes |
|---|---|---|
| COMPLEX pages preserve hard output and can add embedded figures | PASS | Synthetic forced-COMPLEX test keeps the hard block and adds a figure. |
| SCANNED full-page images never enter image description/stage | PASS | Synthetic forced-SCANNED test records no image and one hard transcription call. |
| Hard and image methods remain separately observable | PASS | Test fake observes `transcribe_page` and `describe_image` independently. |
| Hard/image failures are isolated | PASS | Two-page test keeps the hard failure on page 1 and image failure on page 2 isolated. |
| Comparison policies retain explicit image-disabled behavior | PASS | Existing pipeline regression suite remains green; new routing is gated to tiered policy. |

## Technical quality
| Check | Result |
|---|---|
| Build/tests | PASS: 67 passed, 2 skipped |
| Type check | PASS-WITH-NOTES |
| Lint | PASS |
| No debug statements | PASS |
| Edge cases handled | PASS |

The exact `python -m mypy src` invocation is blocked by installed NumPy stubs
that use Python 3.12 syntax while the project configuration targets Python 3.11.
The source passes `python -m mypy --python-version 3.12 src`; this matches the
existing task-015 workstation note.

## Strategy alignment
Replace-the-edge strategy: consistent. Hard-path ownership remains unchanged;
the image stage is additive only for successful tiered digital pages.

User goal served: yes — complex visual figures are retained without double
describing scanned full-page images or changing comparison policies.

## Blockers
-

## Suggestions (non-blocking)
- Keep usage, latency, cache, and run-sidecar call aggregation in task-019.

## Approved for git
[ ] Human approved — proceed to commit
