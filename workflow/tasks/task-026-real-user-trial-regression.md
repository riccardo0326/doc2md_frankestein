# task-026 - Verify the packaged public tool against the authorized trial corpus

## What to build

Run a final user-level regression in a disposable environment after tasks
022-025: verify isolated package resolution and prompt resources, run the public
CLI over representative and aggregate authorized PDFs, exercise the configured
Kelpie service when available, and record only anonymized aggregate outcomes.
Do not add a repository fixture containing a source PDF, rendered page, Markdown,
JSON output, model response, credential, or token value.

## Why

The previous trial found the defects addressed by this loop. A final gate must
prove those defects are fixed in the installed public tool, not only through
injected unit-test seams.

## Relevant files

Read before starting:
- `README.md` - installation, CLI, outputs, and security boundary.
- `pyproject.toml` - supported extras and entry point.
- `docs/discovery.md` - authorized evidence and Kelpie contract.
- `docs/decisions.md` - D013-D015 and current image-context decision.
- `tests/test_public_runtime.py`, `tests/test_package_smoke.py`, `tests/test_warm_cache_determinism.py` - automated contracts from prior tasks.
- `C:\Users\rp99480\dev\unstructured-ingest-source` - authorized read-only trial input.

Create:
- `tests/test_final_trial_guards.py` - opt-in, aggregate-only environment guards if an automated wrapper is needed.

Modify:
- `docs/decisions.md` - record aggregate pass/skip/failure categories and unresolved limitations only.
- `docs/limitations.md` - close only verified gaps; keep environment-dependent gaps explicit.

## Test-First Steps

1. Add an offline final guard proving the public runtime path is callable with fake adapters.
2. Add an opt-in exact-path corpus guard defaulting to skip without `DOC2MD_RUN_AUTHORIZED_CORPUS=1`.
3. Create a disposable environment outside the workspace and install the documented wheel/extras.
4. Verify `doc2md.__file__`, `doc2md --help`, prompt resolution, and optional dependency versions.
5. Run representative embedded-image, complex, scanned, malformed, and multi-page PDFs without storing their outputs in Git.
6. Run the aggregate corpus trial and record only counts, classes, dependency availability, and failure categories.
7. If a general defect appears, add a synthetic failing regression and return to the appropriate earlier task; never add a corpus-specific branch.

## Acceptance criteria

- [x] Installed public CLI resolves this workspace package and packaged prompts.
- [x] Public CLI/API produces image records/assets when the configured runtime and Kelpie are available.
- [x] Public CLI/API uses the hard path for COMPLEX/SCANNED pages and does not double-describe scanned full-page images.
- [x] Cold/warm outputs satisfy task-025 deterministic sidecar rules.
- [x] Aggregate corpus results contain no filenames, excerpts, model responses, credentials, or token values.
- [x] Missing optional dependencies, malformed PDFs, and unavailable Kelpie are isolated and clearly categorized.
- [x] Trial outputs exist only under the approved temporary directory and the repository diff contains no generated artifacts.

## Edge cases to handle

- When the Kelpie process or approved environment is unavailable: skip real calls and retain mandatory offline evidence.
- When the authorized corpus path is missing: skip only that check and do not substitute another path.
- When the installed command resolves another checkout: fail the smoke gate and do not alter unrelated workspaces.
- When a PDF is malformed: continue the aggregate run and record only an anonymized error category.

## Do not touch

- Any input under `C:\Users\rp99480\dev\unstructured-ingest-source`.
- `C:\Users\rp99480\dev\doc2md` and `C:\Users\rp99480\dev\ai4tc_webapp`.
- Credentials, service configuration values, model responses, token values, and generated outputs in Git.

## Definition of done

- [x] Offline final guards pass.
- [x] Optional Kelpie and corpus checks pass or have explicit safe skips.
- [x] `python -m pytest -q` passes.
- [x] `python -m ruff check src tests` passes.
- [x] `python -m mypy src` passes, or the known environment limitation is recorded.
- [x] Repository status contains no trial-generated artifacts.

## Status

completed

### Verification notes

- `python -m pytest -q tests/test_final_trial_guards.py tests/test_package_smoke.py`: 2 passed, 1 skipped without the corpus opt-in.
- `$env:DOC2MD_RUN_AUTHORIZED_CORPUS = '1'; python -m pytest -q tests/test_final_trial_guards.py`: 2 passed; exact authorized corpus was read in place and only aggregate assertions were retained.
- Installed wheel smoke: package path and both prompts resolved from `Temp\opencode\doc2md-final-trial\venv`; `doc2md --help` passed.
- Installed representative CLI aggregate: 4 documents, 0 CLI aborts, 9 isolated page failures, 0 image records while AnyDoc/Kelpie were unavailable.
- `python -m pytest -q`: 90 passed, 5 skipped.
- `python -m pytest -q tests/test_kelpie_integration.py tests/test_image_kelpie_integration.py tests/test_image_corpus_readonly.py`: 1 passed, 3 skipped; real Kelpie was skipped because approved service variables were unavailable.
- `python -m ruff check src tests`: passed.
- `python -m mypy src`: blocked only by the installed NumPy stub Python 3.12 `type` syntax; `python -m mypy --python-version 3.12 src`: passed.
- No commit, amend, push, or PR was performed.
