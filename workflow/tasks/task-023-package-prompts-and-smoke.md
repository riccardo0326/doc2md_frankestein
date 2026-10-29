# task-023 - Package prompts and verify isolated installation

## What to build

Package the existing non-secret prompt files with the Python distribution and
make `KelpieVisionBackend` resolve them from installed package resources rather
than a source-checkout-relative path. Add an isolated wheel/install smoke test
that proves the installed `doc2md` command resolves this workspace, loads the
image prompt, and preserves the documented optional dependency boundary.

## Why

The real-user trial showed that the wheel installed successfully but every
Kelpie image call failed because `prompts/describe_image.v1.txt` was absent from
the installed distribution.

## Relevant files

Read before starting:
- `pyproject.toml` - setuptools package discovery and wheel configuration.
- `src/doc2md/vision/kelpie.py` - current prompt lookup.
- `prompts/describe_image.v1.txt` - existing image prompt content and location.
- `prompts/transcribe_page.v1.txt` - existing hard-page prompt.
- `tests/test_kelpie_integration.py` - optional integration marker convention.
- `tests/test_licenses.py` - packaging and repository safety assertions.
- `README.md` - supported installation commands.

Create:
- `tests/test_prompt_resources.py` - installed/source resource lookup contract.
- `tests/test_package_smoke.py` - isolated wheel/entry-point smoke contract, using a temporary directory only.

Modify:
- `src/doc2md/vision/kelpie.py` - resolve the existing prompts through package resources.
- `pyproject.toml` - include prompt resources in the wheel without adding model artifacts.
- `README.md` - document the verified isolated installation boundary if the smoke test changes installation guidance.

## Test-First Steps

1. Add a failing resource test that invokes the existing prompt lookup from an installed-package-like location.
2. Add a failing wheel smoke assertion that the installed `doc2md` command imports this package and can resolve `describe_image.v1`.
3. Implement resource packaging without changing prompt contents or the Kelpie request contract.
4. Build and install the wheel into a disposable environment outside the repository.
5. Run the smoke command and verify no workspace `build/`, output, PDF, or model artifact is created.

## Acceptance criteria

- [x] Installed `KelpieVisionBackend` resolves `describe_image.v1` and `transcribe_page.v1`.
- [x] Wheel metadata includes the existing prompt resources and no local OCR/model artifacts.
- [x] `doc2md --help` in an isolated environment resolves the workspace package, not another checkout on `sys.path`.
- [x] Missing optional Kelpie dependencies still produce the existing typed failure.
- [x] Prompt contents and the discovered VisionBackend request/response contract are unchanged.

## Edge cases to handle

- When running from a source checkout: prompt lookup still works.
- When installed as a wheel: prompt lookup does not depend on the current working directory.
- When a prompt is absent or renamed: preserve a typed `VisionError` rather than silently using a different prompt.

## Do not touch

- Prompt text unless a failing resource test proves a packaging-only correction is insufficient.
- Credentials, model files, response captures, or any reference workspace.

## Definition of done

- [x] Resource and isolated-install tests pass.
- [x] Wheel build/install smoke passes in a disposable environment.
- [x] `python -m pytest -q` passes.
- [x] `python -m ruff check src tests` passes.
- [x] `python -m mypy src` passes, or the known environment limitation is recorded.
- [x] No generated build directory remains in the repository.

## Status

completed

### Verification notes

- `python -m pytest -q tests/test_prompt_resources.py tests/test_package_smoke.py`: 4 passed.
- `python -m pytest -q`: 84 passed, 4 skipped.
- `python -m ruff check src tests`: passed.
- `python -m mypy src`: blocked only by the installed NumPy stub Python 3.12 `type` syntax; `python -m mypy --python-version 3.12 src`: passed.
- Wheel and virtual environment smoke artifacts were created only under pytest's temporary directory; no workspace build artifact remains.
