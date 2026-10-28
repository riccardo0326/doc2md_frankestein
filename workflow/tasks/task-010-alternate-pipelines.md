# task-010 - Add comparison pipelines

## What to build

Add `full-vision` and the disposable development-only `docling-only` comparison policies behind the same conversion API. Reuse the hybrid stages with routing overrides; do not create separate orchestration paths.

## Why

The migration needs controlled baselines to measure whether the hybrid pipeline reduces tokens and preserves quality.

## Relevant files

Read before starting:

- `C:\Users\rp99480\dev\doc2md\ARCHITECTURE.md` sections 6.3 and 6.6
- `MIGRATION-PLAN.md` cutover decision
- `src/doc2md/converters/pdf/__init__.py`
- `src/doc2md/converters/pdf/hard.py`
- `src/doc2md/vision/base.py`

Create:

- `tests/test_pipelines.py`

Modify:

- `src/doc2md/converters/pdf/__init__.py`
- `src/doc2md/config.py`
- `src/doc2md/cli.py`
- `docs/decisions.md`

## Steps

1. Write policy tests for all-pages vision and all-pages hard routing.
2. Implement pipeline selection through one converter loop.
3. Reuse page rendering, block mapping, images, cache, and metrics.
4. Keep Docling lazy and explicitly development-only.
5. Verify `full-vision` disables duplicate image descriptions.

## Acceptance criteria

- [x] `tiered`, `full-vision`, and `docling-only` are selectable.
- [x] `full-vision` calls vision for every selected page.
- [x] `docling-only` never becomes the enterprise default.
- [x] Pipeline names and methods are recorded in outputs.
- [x] Cache and metrics remain correct for every policy.
- [x] Importing or running tiered text-only conversion does not import Docling.

## Edge cases to handle

- When Docling is unavailable: only affected diagnostic pages fail clearly.
- When full vision has no renderer: return the documented source error.
- When a pipeline name is invalid: return a configuration error.

## Definition of done

- [x] Pipeline tests and existing tests pass.
- [x] CLI help lists valid pipeline choices.
- [x] Ruff and mypy pass.
- [x] Development-only limitations are documented.

## Status

completed

### Dev notes
Files created:
- `tests/test_pipelines.py`

Files modified:
- `src/doc2md/converters/pdf/hybrid.py`
- `src/doc2md/converters/pdf/__init__.py`
- `src/doc2md/config.py`
- `src/doc2md/api.py`
- `src/doc2md/cli.py`
- `docs/decisions.md`
- `MIGRATION-PLAN.md`
- `workflow/ROADMAP.md`
- `workflow/tasks/task-009-cache-metrics.md`
- `workflow/tasks/task-010-alternate-pipelines.md`

Deviations from spec (if any):
- `docling-only` remains an injected development hard seam; this task does not
  install or import Docling artifacts.
- `full-vision` disables image descriptions by policy and uses the injected
  vision page renderer seam; concrete service wiring remains separate.

Verification:
- Offline suite: `45 passed, 2 skipped`; Ruff and mypy pass.
- Policy tests confirm all-page vision, all-page hard routing, pipeline names,
  methods, and invalid pipeline configuration handling.

Suggestions for follow-up (do not act on these):
- Add benchmark-specific pipeline repetitions and cold-cache orchestration only
  in the benchmark task.
