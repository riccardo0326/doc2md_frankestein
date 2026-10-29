# task-025 - Make warm-cache document sidecars deterministic

## What to build

Separate operational cache-hit telemetry from document content so cold and warm
conversions produce byte-identical Markdown, document sidecar JSON, image assets,
image records, figure ordering, and provenance. `run.json` may and should differ
in cache totals and call records because it describes execution telemetry.

## Why

The real trial produced identical Markdown on cold and warm runs but different
document sidecars because warm AnyDoc pages gained `cache_hit:anydoc` page
warnings. That violates the intended deterministic document contract.

## Relevant files

Read before starting:
- `src/doc2md/converters/pdf/hybrid.py` - AnyDoc/page cache warnings and metrics.
- `src/doc2md/converters/pdf/images.py` - image cache records and drafts.
- `src/doc2md/cache.py` - cache hit/miss and corruption behavior.
- `src/doc2md/metrics.py` - run-local operational counters.
- `src/doc2md/render/sidecar.py` - document versus run serialization.
- `src/doc2md/models.py` - page warnings, image records, and run stats.
- `tests/test_image_telemetry.py` and `tests/test_hybrid_images.py` - current two-run assertions.

Create:
- `tests/test_warm_cache_determinism.py` - cold/warm output comparison contract.

Modify:
- `src/doc2md/converters/pdf/hybrid.py` - keep cache-hit diagnostics in operational telemetry without changing document content, unless an equally general existing seam is preferable.
- `tests/test_render.py` - assert the documented split if sidecar coverage is needed.

## Test-First Steps

1. Add a failing two-run test with AnyDoc and image cache enabled.
2. Assert Markdown, document JSON bytes, image assets, image records, block order, IDs, and provenance are equal.
3. Assert warm `run.json` differs only in expected cache/call telemetry and contains no duplicated image-record envelope.
4. Implement the smallest separation between document warnings and operational cache telemetry.
5. Re-run corruption, no-cache, duplicate, and failure-isolation tests.

## Acceptance criteria

- [x] Cold and warm document sidecars are byte-identical for identical source/configuration.
- [x] Cold and warm Markdown and generated image bytes are identical.
- [x] Warm runs make no new AnyDoc or image vision calls and add no new tokens.
- [x] `run.json` accurately reports cache hits/misses and calls even when the document sidecar is unchanged.
- [x] Corrupt cache entries remain isolated and visible in run warnings.

## Edge cases to handle

- When `no_cache=True`: output remains deterministic and the run is cold.
- When only AnyDoc is cached: image records and placement remain unchanged.
- When only an image is cached: AnyDoc document content remains unchanged.
- When a cache entry is corrupt: the document contract remains stable while run telemetry records the warning.

## Do not touch

- Kelpie request fields, image descriptions, token formulas, prompt IDs, or cache key dimensions.

## Definition of done

- [x] Failing-first warm-cache tests pass.
- [x] `python -m pytest -q` passes.
- [x] `python -m ruff check src tests` passes.
- [x] `python -m mypy src` passes, or the known environment limitation is recorded.
- [x] No model responses, tokens, PDFs, or cache payloads are committed.

## Status

completed

### Verification notes

- `python -m pytest -q tests/test_warm_cache_determinism.py`: 1 passed.
- `python -m pytest -q tests/test_image_telemetry.py tests/test_hybrid_images.py tests/test_cache.py tests/test_warm_cache_determinism.py`: 12 passed.
- `python -m pytest -q`: 89 passed, 4 skipped.
- `python -m ruff check src tests`: passed.
- `python -m mypy src`: blocked only by the installed NumPy stub Python 3.12 `type` syntax; `python -m mypy --python-version 3.12 src`: passed.
