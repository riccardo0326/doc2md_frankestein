# task-015 - Package and release the approved hybrid product

## What to build

Package the approved hybrid converter for development and enterprise use, publish complete dependency notices, document installation and operation, and remove only code explicitly approved for removal after the cutover decision. Preserve the configured pdfplumber fallback unless its deletion is separately approved.

## Why

The final product must be installable, auditable, reproducible, and safe on the enterprise machine without hosted Firecrawl OCR or local model artifacts.

## Relevant files

Read before starting:

- `docs/FINDINGS.md`
- `docs/cutover-decision.md`
- `docs/discovery.md`
- `MIGRATION-PLAN.md`
- `pyproject.toml`
- `workflow/PROJECT.md`

Create:

- `README.md`
- `THIRD_PARTY_NOTICES.md`
- `docs/licenses.md`
- `CHANGELOG.md`
- `tests/test_licenses.py`

Modify:

- `pyproject.toml`
- `.gitignore`
- `workflow/PROJECT.md`
- `workflow/ROADMAP.md`
- `docs/decisions.md`

## Steps

1. Add optional dependency groups for AnyDoc and development tooling.
2. Verify native AnyDoc installation on supported Windows/Python environments.
3. Generate Python and native/transitive dependency license reports.
4. Add license enforcement for forbidden licenses.
5. Document local AnyDoc, Kelpie hard path, configuration, outputs, fallback, and security boundary.
6. Build a clean package in an isolated environment.
7. Run tests, lint, type checking, and the documented smoke conversion.
8. Remove only explicitly approved dead code.

## Acceptance criteria

- [x] Clean installation succeeds with the approved extras.
- [x] A digital PDF uses local AnyDoc without external API traffic.
- [x] Scanned/visual pages use Kelpie only through the approved contract.
- [x] No model artifacts are installed or downloaded on the enterprise PC.
- [x] License checks pass with no forbidden dependency.
- [x] README examples run.
- [x] Output, provenance, metrics, cache, and rollback behavior are documented.
- [x] Version and changelog identify the release.

## Edge cases to handle

- When native wheels are unavailable: document the supported environment and keep the package from silently compiling or downloading artifacts.
- When AnyDoc is omitted: the configured fallback remains explicit and tested.
- When Kelpie is unavailable: digital pages still complete; hard pages fail in isolation according to the contract.

## Definition of done

- [x] Clean build and install pass.
- [x] Tests, Ruff, mypy, and license checks pass.
- [x] Final findings and decisions are present.
- [x] No secrets or confidential artifacts are included.

## Status

dev-complete

### Dev notes
Files created:
- `README.md`
- `THIRD_PARTY_NOTICES.md`
- `docs/licenses.md`
- `CHANGELOG.md`
- `tests/test_licenses.py`

Files modified:
- `pyproject.toml`
- `.gitignore`
- `workflow/PROJECT.md`
- `workflow/ROADMAP.md`
- `docs/decisions.md`
- `workflow/tasks/task-014-findings-cutover.md`
- `workflow/tasks/task-015-package-release.md`

Deviations from spec (if any):
- EDAG baseline is explicitly out of scope because its PDFs and invocation/
  telemetry contract are not supplied.
- No dead production code was removed without an explicit approval.

Verification:
- Clean editable install with `.[dev,anydoc,kelpie]`: pass.
- Wheel build: pass.
- License audit with `pip-licenses --fail-on "GPL;AGPL;LGPL;SSPL"`: pass.
- Release smoke conversion on a temporary synthetic digital PDF: pass without
  external API traffic.
- Full suite: `56 passed, 1 skipped`; Ruff and mypy pass.

Suggestions for follow-up (do not act on these):
- Publish only after human review of the provisional cutover decision.
