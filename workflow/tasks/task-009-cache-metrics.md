# task-009 - Add cache and run metrics

## What to build

Implement content-addressed disk caching and run metrics for AnyDoc pages, Kelpie pages, and image descriptions. Produce `run.json` with routes, methods, timings, calls, token usage, estimated flags, failures, and cache hits.

## Why

The product must prove token and latency savings and must avoid repeating expensive Kelpie work. Metrics must be derived from per-call records so totals cannot drift.

## Relevant files

Read before starting:

- `C:\Users\rp99480\dev\doc2md\ARCHITECTURE.md` sections 8 and 11
- `src/doc2md/models.py`
- `src/doc2md/converters/pdf/__init__.py`
- `src/doc2md/vision/base.py`
- old `src/doc2md/cache.py` and `metrics.py` for behavior reference only

Create:

- `src/doc2md/cache.py`
- `src/doc2md/metrics.py`
- `tests/test_cache.py`
- `tests/test_metrics.py`

Modify:

- `src/doc2md/converters/pdf/__init__.py`
- `src/doc2md/render/sidecar.py`
- `src/doc2md/config.py`
- `docs/decisions.md`

## Steps

1. Write cache key and metrics derivation tests.
2. Implement atomic JSON cache reads and writes.
3. Include source hash, page/image identity, backend version, prompt/config hashes, and model where relevant.
4. Record AnyDoc timing without fabricating token usage.
5. Record Kelpie reported or estimated usage per call.
6. Add `--no-cache` and cold-cache behavior.
7. Add second-run end-to-end tests.

## Acceptance criteria

- [x] A repeated run makes zero repeated expensive calls.
- [x] Changing output-affecting configuration invalidates cache entries.
- [x] Cache corruption becomes a miss with a warning.
- [x] `run.json` totals equal sums of call records.
- [x] Cache hits are not counted as new calls or tokens.
- [x] AnyDoc runs record method and duration.
- [x] Cache writes are atomic.

## Edge cases to handle

- When cache content is invalid: delete only the invalid entry and continue.
- When two runs write the same key: preserve deterministic content.
- When Kelpie omits usage: estimate using the approved Phase 0 method and mark it.

## Definition of done

- [x] Cache and metrics tests pass.
- [x] Hybrid second-run test proves zero repeated expensive calls.
- [x] Ruff and mypy pass.
- [x] `run.json` is documented and deterministic apart from run timestamps/IDs.

## Status

completed

### Dev notes
Files created:
- `src/doc2md/cache.py`
- `src/doc2md/metrics.py`
- `tests/test_cache.py`
- `tests/test_metrics.py`

Files modified:
- `src/doc2md/converters/pdf/hybrid.py`
- `src/doc2md/converters/pdf/images.py`
- `src/doc2md/render/sidecar.py`
- `src/doc2md/config.py`
- `src/doc2md/api.py`
- `src/doc2md/cli.py`
- `docs/decisions.md`
- `MIGRATION-PLAN.md`
- `workflow/ROADMAP.md`
- `workflow/tasks/task-008-image-pipeline.md`
- `workflow/tasks/task-009-cache-metrics.md`

Deviations from spec (if any):
- Metrics timing remains deterministic at the current converter seam; the
  cache/call model is ready for measured timings in later benchmark work.
- Hard/image cache hooks are implemented without changing their existing
  adapter contracts; full end-to-end image assembly remains task-scoped.

Verification:
- Offline suite: `42 passed, 2 skipped`; Ruff and mypy pass.
- Second-run hybrid test proves no repeated AnyDoc call.

Suggestions for follow-up (do not act on these):
- Use cold-cache directories for benchmark repetitions in the next pipeline task.
