# task-019 - Wire image cache, telemetry, and sidecars

## Objective

Feed integrated image results into the existing `DiskCache`,
`MetricsCollector`, document sidecar, and `run.json` contracts. Record one
`describe_image` call with model, latency, usage, and estimated flag for each
canonical cache miss; record cache hits/misses without fabricating calls or
tokens; and make the second conversion deterministic and free of repeated
expensive image descriptions.

## Why

Running the image stage without audit data would hide cost, latency, and cache
behavior. The output contract must show which image was processed, how it was
provenanced, and whether the result came from a cache without changing the
discovered Kelpie interface.

## Dependencies And Initial State

- Depends on `task-017` and `task-018`.
- Initial status: `planned`; it becomes `ready` only after both dependencies
  pass QA.

## Files To Read

- `docs/decisions.md` - D015 and the cache/metrics contract.
- `src/doc2md/cache.py` - content-addressed keys and atomic JSON writes.
- `src/doc2md/metrics.py` - call-derived totals and cache counters.
- `src/doc2md/converters/pdf/images.py` - existing image cache behavior.
- `src/doc2md/converters/pdf/hybrid.py` - metrics lifetime and page loop.
- `src/doc2md/models.py` - `VisionResult`, `CallStat`, `RunStats`, and records.
- `src/doc2md/render/sidecar.py` - document and run JSON schemas.
- `tests/test_cache.py`, `tests/test_metrics.py`, `tests/test_render.py`, and
  `tests/test_hybrid_images.py` - current assertions.

## Files To Create

- `tests/test_image_telemetry.py` - cache-aware integration and sidecar tests.

## Files To Modify

- `src/doc2md/converters/pdf/hybrid.py` - drain image call results and merge
  image cache counts into the run collector.
- `src/doc2md/cache.py` - extend `vision_cache_key()` with the injected backend
  name as an output-affecting dimension.
- `src/doc2md/converters/pdf/images.py` - expose only the existing result data
  needed for metrics; retain `vision_cache_key()` and sequential ordering.
- `src/doc2md/render/sidecar.py` - serialize the already-populated image and
  call data without changing unrelated fields.
- `tests/test_cache.py` and `tests/test_metrics.py` - add image-specific key and
  accounting assertions where the existing abstractions are being extended.

## Test-First Steps

1. Add a failing two-run test with one canonical image and one duplicate; assert
   the first run has one miss/call and the second has a hit/no backend call.
2. Assert call totals equal the sum of non-cached `CallStat` records, including
   input/output/total tokens, estimated flags, and `latency_s`; cached results
   must not appear as `CallStat(cache_hit=False)` records.
3. Assert image cache keys change with SHA-256, prompt, model, backend name, or
   output-affecting configuration and remain stable otherwise.
4. Assert `ConvertedDocument.images` retains image IDs and status in the
   document sidecar, while `run.json` retains image call IDs, usage, latency,
   and aggregate cache counts without duplicating the image-record list.
5. Add a corrupted image cache entry test: delete only that entry, report a
   warning, and continue with one fresh description.
6. Implement the smallest wiring and keep cache writes atomic and JSON-only.

## Acceptance Criteria

- [x] Image cache keys include image identity/SHA-256, prompt, model, backend,
  and output-affecting configuration through the existing key seam.
- [x] Cache hits create no new `CallStat`, no new backend call, and no new token
  total; cache misses create exactly one canonical image call.
- [x] `run.json` reports image latency and usage through its existing calls
  envelope and totals remain derived from records.
- [x] The document sidecar contains all image records, including duplicates,
  skipped assets, and failures, with truthful provenance in figure blocks; it is
  the sole owner of the full image-record list.
- [x] `--no-cache`/`no_cache=True` produces a cold run with no read or write.
- [x] Corruption is isolated to one cache entry and visible as a warning.

## Edge Cases

- When Kelpie omits usage, retain the existing `Usage.estimated` behavior; do
  not infer a new token formula in this task.
- When the cache contains a valid result but the output image is absent, the
  image asset is deterministically rewritten without re-describing it.
- When an image description fails, it contributes no successful call or token
  total beyond what the backend actually returned and the record remains failed.
- When a run has both page transcription and image calls, totals and kinds stay
  distinct.

## Definition Of Done

- [x] Offline cache/metrics/sidecar integration tests pass.
- [x] Existing cache, metrics, render, hybrid, and image tests remain green.
- [x] `python -m pytest -q` passes.
- [x] `python -m ruff check src tests` passes.
- [x] `python -m mypy src` passes.
- [x] No usage values, credentials, model responses, or cache payloads from
  real services are committed.

## Status

completed

### Dev notes

Files created:
- `tests/test_image_telemetry.py`

Files modified:
- `src/doc2md/cache.py`
- `src/doc2md/converters/pdf/hybrid.py`
- `src/doc2md/converters/pdf/images.py`
- `tests/test_cache.py`
- `workflow/tasks/task-019-image-cache-metrics-sidecars.md`

Deviations from spec (if any):
- The exact `python -m mypy src` command remains blocked by installed NumPy
  stubs using Python 3.12 syntax under the project Python 3.11 target.
  `python -m mypy --python-version 3.12 src` passes; this is the same
  workstation limitation recorded in task-015 QA.

Suggestions for follow-up (do not act on these):
- Keep crop/filter/placement determinism hardening in task-020.
