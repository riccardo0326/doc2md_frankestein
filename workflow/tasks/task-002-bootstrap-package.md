# task-002 - Bootstrap the migration package

## What to build

Create the independent Python package and development tooling for the migration workspace. The package must install in editable mode, expose a placeholder `doc2md` module, and run offline tests, lint, and type checking. Do not implement PDF conversion, AnyDoc, Kelpie, images, caching, or benchmark behavior.

## Why

The migration needs an independent build and test surface before code is moved behind adapters. This task proves that the new workspace is not coupled to the old repository.

## Relevant files

Read before starting:

- `MIGRATION-PLAN.md`
- `workflow/PROJECT.md`
- `docs/discovery.md`
- `C:\Users\rp99480\dev\doc2md\pyproject.toml`

Create:

- `pyproject.toml`
- `src/doc2md/__init__.py`
- `tests/conftest.py`
- `tests/test_bootstrap.py`

Modify:

- `workflow/PROJECT.md` with exact install, test, lint, type-check, and build commands.

## Steps

1. Add the minimum permitted runtime and development dependencies.
2. Configure Python version, pytest, Ruff, and mypy.
3. Add the package import smoke test.
4. Add the editable-install smoke test instructions.
5. Record any dependency or command deviation in `docs/decisions.md`.

## Acceptance criteria

- [x] Editable installation succeeds in an isolated environment.
- [x] `pytest -q` passes.
- [x] `ruff check src tests` passes.
- [x] `mypy src` passes.
- [x] `import doc2md` does not import AnyDoc, Docling, or Kelpie.
- [x] No source files from the old repository were copied blindly.

## Edge cases to handle

- When an optional native package is unavailable: the base package still installs and tests pass.
- When a dependency license is not known: record it and stop before adding it.

## Definition of done

- [x] Commands are documented in `workflow/PROJECT.md`.
- [x] Tests, lint, and type checking pass.
- [x] `docs/decisions.md` is updated if needed.

## Status

completed

### Dev notes
Files created:
- `pyproject.toml`
- `src/doc2md/__init__.py`
- `tests/conftest.py`
- `tests/test_bootstrap.py`

Files modified:
- `workflow/PROJECT.md`
- `docs/decisions.md`
- `workflow/tasks/task-001-phase0-discovery.md`
- `workflow/tasks/task-002-bootstrap-package.md`

Deviations from spec (if any):
- The base runtime dependency list is intentionally empty; development tools
  are available through the optional `dev` extra. This is recorded as D008.
- The wheel build uses `python -m pip wheel` rather than adding a separate
  `build` dependency.

Suggestions for follow-up (do not act on these):
- Implement only the next approved task's contract; keep this package import
  boundary free of AnyDoc, Docling, and Kelpie.
