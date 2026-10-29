# task-022 - Wire the public runtime to image and hard-path adapters

## What to build

Make the normal public conversion path construct the configured AnyDoc, Kelpie
hard-page, and embedded-image adapters instead of requiring callers to inject a
custom `PdfConverter`. The CLI and `api.convert()` must use the same runtime
assembly, preserve fake-adapter injection for offline tests, keep comparison
pipelines explicitly image-disabled, and retain isolated failures when optional
Kelpie access is unavailable.

## Why

The real-user trial showed that direct API injection works, but normal
`doc2md convert` emits no image records and leaves COMPLEX/SCANNED pages without
a hard extractor. The public product path must exercise the implemented image
context contract.

## Relevant files

Read before starting:
- `src/doc2md/cli.py` - public command options and API delegation.
- `src/doc2md/api.py` - public conversion entry point and converter injection.
- `src/doc2md/config.py` - existing vision, image, hard, and cache settings.
- `src/doc2md/converters/pdf/hybrid.py` - converter seams and pipeline policy.
- `src/doc2md/converters/pdf/hard.py` - existing `KelpieHardExtractor` contract.
- `src/doc2md/converters/pdf/images.py` - existing `ImageStage` contract.
- `src/doc2md/vision/kelpie.py` and `src/doc2md/vision/base.py` - discovered backend seam.
- `tests/test_hybrid_images.py` and `tests/test_hybrid_complex_scanned_images.py` - offline integration conventions.

Create:
- `src/doc2md/runtime.py` - one Python-owned runtime factory and the per-page hard adapter, if a separate module keeps public assembly explicit.
- `tests/test_public_runtime.py` - fake-backed CLI/API runtime tests.

Modify:
- `src/doc2md/api.py` - build the configured runtime when no converter is injected.
- `src/doc2md/cli.py` - expose only configuration already supported by `Config`, including an explicit image-disable option if needed by the existing command contract.
- `src/doc2md/converters/pdf/hybrid.py` - only if the runtime adapter requires a minimal public seam adjustment.

## Test-First Steps

1. Add a failing API test proving a normal conversion with fake runtime adapters emits image records and figure blocks.
2. Add a failing public-path test proving a COMPLEX/SCANNED fixture uses the hard adapter and that SCANNED pages create no embedded image record.
3. Add a failing test proving unavailable optional Kelpie access isolates the affected page/image without invoking hosted OCR or a local model.
4. Add a failing comparison-pipeline test proving `full-vision` and `docling-only` do not invoke the embedded-image stage.
5. Implement the smallest runtime factory around the existing contracts.
6. Run the CLI through an isolated test runner or subprocess and assert output paths, sidecar records, and exit behavior.

## Acceptance criteria

- [x] `api.convert()` without an injected converter builds the configured runtime and processes eligible embedded images.
- [x] Normal `doc2md convert` can produce image records/assets when AnyDoc, the configured renderer, and Kelpie are available.
- [x] COMPLEX/SCANNED pages use the existing Kelpie hard contract; SCANNED full-page images are never sent to `describe_image()`.
- [x] Fake backends remain injectable and all new tests run offline.
- [x] Missing optional dependencies or unavailable Kelpie calls remain isolated failures with truthful warnings.
- [x] `full-vision` and `docling-only` retain explicit image-disabled behavior.
- [x] No request/response fields, retry policy, model value, or credential behavior is invented.

## Edge cases to handle

- When the vision service is not configured: TEXT conversion remains usable and image failures are recorded without aborting the page.
- When `images.enabled=False`: no image backend call occurs and retained candidates use the existing `vision_disabled` record contract.
- When a hard page fails: the page remains failed and unrelated TEXT/image pages continue.
- When the caller supplies a custom `PdfConverter`: preserve that injection path unchanged.

## Do not touch

- `C:\Users\rp99480\dev\doc2md` or `C:\Users\rp99480\dev\ai4tc_webapp`.
- Kelpie request/response shapes, router thresholds, AnyDoc Markdown normalization, or the explicit pdfplumber fallback policy.

## Definition of done

- [x] Test-first public runtime tests pass offline.
- [x] `python -m pytest -q` passes.
- [x] `python -m ruff check src tests` passes.
- [x] `python -m mypy src` passes, or the known NumPy-target limitation is recorded without masking source errors.
- [x] No PDFs, model responses, credentials, tokens, or generated output are committed.

## Status

completed

### Verification notes

- `python -m pytest -q tests/test_public_runtime.py`: 5 passed.
- `python -m pytest -q`: 80 passed, 4 skipped.
- `python -m ruff check src tests`: passed.
- `python -m mypy src`: blocked only by the installed NumPy stub Python 3.12 `type` syntax; `python -m mypy --python-version 3.12 src`: passed.
- No optional Kelpie or authorized corpus run was performed for this offline task.
