# QA report — task-019 — Wire image cache, telemetry, and sidecars

## STATUS: PASS-WITH-NOTES
Reviewed: 2026-10-28

## Task criteria
| Criterion | Result | Notes |
|---|---|---|
| Image keys include SHA, prompt, model, backend, and config | PASS | `vision_cache_key()` and cache assertions cover each dimension. |
| Hits create no call/backend/tokens; misses create one canonical call | PASS | Two-run duplicate integration test verifies calls and totals. |
| `run.json` reports image usage/latency and derived totals | PASS | Existing call envelope receives `describe_image` records; no duplicate image list is added. |
| Document sidecar owns all image records | PASS | Sidecar assertions retain canonical and duplicate records under `images`. |
| `no_cache=True` is cold | PASS | Test verifies one fresh image call and no cache directory. |
| Corruption is isolated and warned | PASS | Invalid image entry is removed and recomputed with a warning. |

## Technical quality
| Check | Result |
|---|---|
| Build/tests | PASS: 70 passed, 2 skipped |
| Type check | PASS-WITH-NOTES |
| Lint | PASS |
| No debug statements | PASS |
| Edge cases handled | PASS |

The exact `python -m mypy src` invocation is blocked by installed NumPy stubs
that use Python 3.12 syntax while the project configuration targets Python 3.11.
The source passes `python -m mypy --python-version 3.12 src`; this matches the
existing task-015 workstation note.

## Strategy alignment
Replace-the-edge strategy: consistent. Telemetry is derived from existing
vision results and cache-aware call records without changing the Kelpie seam.

User goal served: yes — image processing is now auditable and repeatable across
cold and warm conversions.

## Blockers
-

## Suggestions (non-blocking)
- Continue with general robustness and deterministic placement checks in task-020.

## Approved for git
[ ] Human approved — proceed to commit
