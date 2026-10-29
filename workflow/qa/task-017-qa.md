# QA report — task-017 — Integrate embedded images in TEXT pages

## STATUS: PASS-WITH-NOTES
Reviewed: 2026-10-28

## Task criteria
| Criterion | Result | Notes |
|---|---|---|
| Eligible TEXT images reach filtering/dedupe/description once per canonical SHA-256 | PASS | Synthetic one- and two-page tests verify one fake vision call for a cross-page duplicate. |
| Figure blocks preserve page, vision provenance, stable IDs, and placement | PASS | Integration assertions verify page 1/2 provenance, bbox, and placement after text. |
| Document and sidecar contain image records | PASS | Described records are serialized in `ConvertedDocument.images` and JSON. |
| Assets use stable relative paths | PASS | Assets are written under `images/pNNNN-iNN.png`; Markdown contains no absolute path. |
| Rendering/description failures remain isolated | PASS | Crop failure leaves the TEXT page usable and records the failed image. |
| Later-page duplicates reuse canonical path/description with occurrence provenance | PASS | Cross-page synthetic test verifies both records and one backend call. |
| pdfplumber fallback remains opt-in and image processing continues | PASS | Fallback test verifies method, warning, image record, and vision call. |
| `images.enabled=False` records disabled vision without backend calls | PASS | Synthetic test verifies `vision_disabled` and zero calls. |

## Technical quality
| Check | Result |
|---|---|
| Build/tests | PASS: 64 passed, 2 skipped |
| Type check | PASS-WITH-NOTES |
| Lint | PASS |
| No debug statements | PASS |
| Edge cases handled | PASS |

The exact `python -m mypy src` command is blocked by installed NumPy stubs
that use Python 3.12 syntax while the project configuration targets Python 3.11.
The source passes `python -m mypy --python-version 3.12 src`; this matches the
existing task-015 workstation note.

## Strategy alignment
Replace-the-edge strategy: consistent. Python coordinates the injected image
stage while AnyDoc and the explicit fallback retain ownership of text extraction.

User goal served: yes — informative embedded figures now survive TEXT-page
conversion in Markdown, the document sidecar, and deterministic asset output.

## Blockers
-

## Suggestions (non-blocking)
- Keep run-level image call, usage, latency, and cache totals in task-019.

## Approved for git
[ ] Human approved — proceed to commit
