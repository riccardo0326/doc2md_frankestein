# task-003 - Establish the output contract

## What to build

Implement the immutable common models and pure output functions needed by every future adapter: provenance, blocks, page results, converted documents, Markdown rendering, sidecar JSON, and isolated conversion errors. Add the `anydoc` provenance value without claiming that the adapter exists yet.

## Why

The Rust parser and Kelpie must produce the same auditable output. A small stable contract prevents parser-specific details from leaking into the orchestrator.

## Relevant files

Read before starting:

- `C:\Users\rp99480\dev\doc2md\ARCHITECTURE.md` sections 4, 5, 10, and 11
- `MIGRATION-PLAN.md` sections Contract Changes and Page Granularity
- `src/doc2md` in the old repository for reference only

Create:

- `src/doc2md/models.py`
- `src/doc2md/errors.py`
- `src/doc2md/render/markdown.py`
- `src/doc2md/render/sidecar.py`
- `tests/test_models.py`
- `tests/test_render.py`

Modify:

- `src/doc2md/__init__.py`
- `docs/decisions.md` with the schema/source decision from Phase 0

## Steps

1. Write failing model-validation and provenance tests.
2. Implement frozen Pydantic models matching the approved contract.
3. Add `anydoc` to the method union only if Phase 0 approved it.
4. Write golden Markdown and JSON rendering tests.
5. Implement deterministic rendering with optional page markers and block anchors.
6. Validate UTF-8, newline, ordering, and no-NaN rules.

## Acceptance criteria

- [x] Every block has page, block ID, source, Markdown, and plain text.
- [x] AnyDoc provenance is truthful and serialisable.
- [x] Failed pages render a placeholder and do not abort document rendering.
- [x] Sidecar JSON is deterministic and validates through Pydantic.
- [x] Page markers are configurable.
- [x] Golden tests pass byte-for-byte.

## Edge cases to handle

- When a page has no blocks: render a valid empty page result.
- When a block contains Markdown tables or image syntax: preserve it verbatim.
- When a consumer rejects `anydoc` in schema 1.0: use the schema version decision from Phase 0; do not silently mislabel it.

## Definition of done

- [x] `pytest -q` passes.
- [x] `ruff check src tests` passes.
- [x] `mypy src` passes.
- [x] `docs/decisions.md` records contract changes.

## Status

completed

### Dev notes
Files created:
- `src/doc2md/models.py`
- `src/doc2md/errors.py`
- `src/doc2md/render/__init__.py`
- `src/doc2md/render/markdown.py`
- `src/doc2md/render/sidecar.py`
- `tests/test_models.py`
- `tests/test_render.py`

Files modified:
- `pyproject.toml`
- `src/doc2md/__init__.py`
- `docs/decisions.md`
- `MIGRATION-PLAN.md`
- `workflow/ROADMAP.md`
- `workflow/tasks/task-002-bootstrap-package.md`
- `workflow/tasks/task-003-output-contract.md`

Deviations from spec (if any):
- Pydantic v2 was added as the minimum runtime dependency required by the
  contract models; the dependency and MIT license are recorded in D009.
- Schema version remains `1.0` because `anydoc` is an approved additive source
  value; consumers with a closed enum require an explicit future schema decision.

Suggestions for follow-up (do not act on these):
- Keep adapter-specific imports out of the public model and rendering modules.
- Add contract tests for adapter output before implementing the AnyDoc adapter.
