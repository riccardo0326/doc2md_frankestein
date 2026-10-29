# QA report — image-context corrective loop

## STATUS: PASS

Reviewed: 2026-10-29

## Scope

Tasks 022-026 and the installed public-tool trial were reviewed together. Existing
task QA reports were retained because they contain useful migration evidence.

## Verification

| Check | Result | Notes |
|---|---|---|
| Offline suite | PASS | 90 passed, 5 skipped. |
| Ruff | PASS | `python -m ruff check src tests`. |
| Mypy | PASS-WITH-NOTE | Python 3.12 target passes; default target is blocked only by installed NumPy stub syntax. |
| Installed package | PASS | Isolated package path and packaged prompts resolved correctly. |
| Public TEXT/COMPLEX/SCANNED trial | PASS | Image records, hard calls, provenance, and scanned exclusion matched the contract. |
| Warm-cache trial | PASS | Markdown and document sidecars were byte-identical; warm calls were zero. |
| Authorized corpus | PASS-WITH-NOTE | Exact path was read-only; only aggregate outcomes were retained. |
| Secret/data safety | PASS | No PDFs, outputs, responses, credentials, or token values are tracked. |

## Blockers

- None for this corrective loop.

## Non-blocking notes

- The global `doc2md` command can resolve another checkout; isolated installation
  is required and documented.
- Large image-heavy documents can exceed a short user timeout when descriptions
  are enabled; `--no-images` is the explicit operational control.
- Enterprise cutover remains unclaimed until broader performance and quality
  review is approved.

## Approved for git

[x] Human approval received with the commit and PR request.
