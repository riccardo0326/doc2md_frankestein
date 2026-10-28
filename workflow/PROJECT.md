# PROJECT.md

## Identity

Project name: `doc2md-frankestein`
Short description: Migration workspace for a hybrid AnyDoc Rust + Python + Kelpie PDF converter.

## Stack

Language: Python >= 3.11; AnyDoc native Rust binding
Framework: Typer CLI, Pydantic v2 models
State management: Explicit run context and content-addressed JSON cache
Data fetching: pdfplumber for signals, AnyDoc for digital pages, pypdfium2 for rendering, Kelpie for hard pages and images
Testing: pytest, Ruff, mypy
Package manager: pip for Python dependencies; native AnyDoc package as an optional dependency

## Commands

Run these commands from the migration workspace inside an isolated Python
environment:

```text
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check src tests
python -m mypy src
pip-licenses --fail-on "GPL;AGPL;LGPL;SSPL"
python -m pip wheel --no-deps . --wheel-dir dist
```

Phase 0 discovery commands remain documented in
`workflow/tasks/task-001-phase0-discovery.md`. Build, lint, and test commands
must remain compatible with the source `doc2md` workspace unless a decision
record changes them.

## File structure

- `MIGRATION-PLAN.md` is the migration source of truth.
- `pyproject.toml` defines the independent package and development tooling.
- `src/doc2md/__init__.py` is the current placeholder package module.
- `tests/` contains offline bootstrap and future contract tests.
- `workflow/tasks/` contains executable tasks. Only the task marked `ready` may start.
- `docs/discovery.md` contains Phase 0 evidence.
- `docs/decisions.md` contains migration decisions.
- Future production code will use the source project's `src/doc2md/` layout only after Phase 0 approves the migration boundary.

## Conventions

Component style: Deep adapters behind small interfaces.
Error handling: Isolate page failures and record the method, fallback, and reason.
Provenance: Original 1-based page numbers are authoritative.
Secrets: Environment variables only; never store values in files.

## Do not touch

- `C:\Users\rp99480\dev\doc2md` unless a later task explicitly authorizes a cutover change.
- `C:\Users\rp99480\dev\ai4tc_webapp`, which is a read-only Kelpie reference.
- Confidential PDFs, model responses, credentials, and token values.

## Known constraints

- Phase 0 must be signed off before production migration work.
- Enterprise PCs must not install or provision OCR/layout/LLM model artifacts.
- Only Kelpie may provide enterprise OCR/vision inference.
- AnyDoc must run locally and must not use Firecrawl hosted OCR in the enterprise path.
