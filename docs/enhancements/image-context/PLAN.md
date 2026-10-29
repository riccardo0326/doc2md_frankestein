# Image Context Integration Enhancement

## Objective

Connect the existing embedded-image stage to the normal `PdfConverter` flow so
informative images on digital PDF pages are preserved in Markdown and in the
sidecar contract. The enhancement must cover `TEXT` and eligible `COMPLEX`
pages, while leaving full-page `SCANNED` images to the Kelpie hard path without
double description.

This is a planning-only change. No application code, PDF, generated output,
model response, credential, or token value is introduced by this enhancement
branch.

## Baseline And Gap

Before branch creation the repository was clean on `main`; this planning branch
is now `enhancement/image-context-integration`. Phase 0 is signed off and
`task-015` is reviewed and the image-context gate is now open. The current gap
is specific and verified:

- `src/doc2md/converters/pdf/images.py` already discovers, renders, filters,
  hashes, deduplicates, saves, describes, caches, and places image drafts.
- `tests/test_images.py` verifies those behaviors with fake renderers and a
  fake vision backend.
- `PdfConverter` in `src/doc2md/converters/pdf/hybrid.py` does not invoke that
  stage, does not aggregate `ImageRecord` values, and does not place image
  blocks into converted pages.
- `run.json` and `MetricsCollector` already expose the call, usage, latency,
  and cache seams, but image results are not fed into them by the converter.
  The document sidecar owns image records; `run.json` owns image call records
  and aggregate cache/usage/latency totals, avoiding a second image-record
  envelope.
- The explicit `pdfplumber` fallback exists for AnyDoc text extraction and must
  remain the only text fallback. A rendering failure is an isolated image
  failure, not permission to invent another OCR or vision path.

## Scope Classification

### Required To Fix The TEXT-Page Bug

Tasks `016` through `020` are required. Together they:

- give `PdfConverter` an explicit, injectable image-stage seam;
- run the stage for eligible `TEXT` pages after text extraction;
- retain page provenance and place figure blocks after the correct preceding
  block;
- record image records, deterministic assets, descriptions, failures, usage,
  latency, cache hits, cache misses, and `run.json` data;
- preserve image processing when the text extractor uses the configured
  `pdfplumber` fallback;
- cover eligible `COMPLEX` pages and exclude full-page `SCANNED` images;
- prove rendering/crop failure isolation, filtering boundaries, SHA-256
  deduplication, and deterministic output.

### Already Implemented And Reused

The following behavior is already implemented and must not be rewritten or
silently changed without a failing regression test:

- `collect_images()` assigns stable page/image IDs and accepts an injected
  renderer.
- Crop rendering uses `pypdfium2` geometry and PNG output when the default
  renderer is used.
- Minimum width, height, area, and maximum aspect-ratio filters are
  configuration-driven.
- SHA-256 deduplication preserves the first canonical image and records later
  duplicates.
- `process_images()` saves `images/pNNNN-iNN.png`, calls only
  `VisionBackend.describe_image()`, records `ImageRecord` and `Usage`, and
  isolates failures. Its integration must extend the existing local record
  map to a run-level canonical registry for cross-page duplicates.
- `place_image_drafts()` creates inline figure blocks and uses bounding boxes to
  place them relative to existing blocks.
- `page_class="SCANNED"` currently excludes embedded-image collection.
- `DiskCache`, `vision_cache_key()`, `MetricsCollector`, `VisionResult`, the
  fake vision backend, sidecar writers, and Kelpie's discovered
  `VisionBackend` seam already exist.

The integration tasks may adapt these seams, but must not invent a second
vision request or cache contract.

The current wording in `docs/limitations.md` broadly describes image
provenance, usage, latency, cache, and failure as `run.json` impact. The
implementation must reconcile that wording in `task-021`: full `ImageRecord`
data remains in the document sidecar, while `run.json` exposes the corresponding
image calls and aggregate metrics. This is an additive clarification, not a
second serialized image-record contract.

### Optional Or Environment-Dependent

- Real Kelpie image-description calls are optional and must remain marker- and
  environment-guarded. Offline tests use `FakeVisionBackend`.
- The default `pypdfium2` renderer is optional at installation time through the
  existing `kelpie` extra; tests may inject a renderer and must not require a
  network or local model artifact.
- Verification against
  `C:\Users\rp99480\dev\doc2md\samples\unstructured-demo` is read-only,
  opt-in when the path and dependencies are available, and records only
  anonymised aggregate outcomes outside this repository.

### Explicitly Out Of Scope

- No change to the Kelpie request/response contract beyond the discovered
  `VisionBackend.describe_image()` method and existing redacted evidence.
- No implicit Firecrawl hosted OCR, local OCR, layout model, or vision model
  installation.
- No filename-, document-, image-name-, or page-number-specific branch.
- No change to the default router thresholds or a silent `TEXT` to `COMPLEX`
  reclassification.
- No removal of the `pdfplumber` fallback or the existing hard-path behavior.
- No semantic reinterpretation of AnyDoc Markdown.
- No copy of authorized or confidential PDFs, Markdown output, sidecars,
  model responses, credentials, or token values into Git.
- No full-vision image behavior change: comparison pipelines retain their
  explicit image-disabled policy unless a separate decision authorizes it.

## Contract Decisions For Implementation

1. The image stage is a Python-owned adapter around the existing
   `collect_images()`, `process_images()`, and `place_image_drafts()` functions.
   Its input is the original `pdfplumber` page, original 1-based page number,
   page class, source path, output directory, `ImageConfig`, shared
   deduplication map, `DiskCache`, and an injected `VisionBackend` or
   renderer. Its result remains `ImageProcessingResult` plus the placed page
   results; no Kelpie-specific fields are added. The converter owns a run-level
   canonical record registry so a duplicate on a later page reuses the first
   canonical path/description while retaining its own occurrence provenance.
2. `TEXT` and `COMPLEX` are eligible for embedded-image processing. The hard
   extractor remains authoritative for full-page transcription on `COMPLEX`;
   embedded figures may be appended as separately proven `figure` blocks.
3. `SCANNED` pages do not enter the embedded-image stage. Their full-page
   image is handled once by `KelpieHardExtractor`, with no `ImageRecord` and no
   `describe_image()` call for that full-page asset.
4. `images.enabled=False` disables vision descriptions explicitly, but retained
   candidates still produce `ImageRecord(status="skipped",
   skip_reason="vision_disabled")` and deterministic inline output when an
   output directory is requested. No backend call is allowed.
5. If crop rendering fails, the image receives a failed `ImageRecord` and a
   failure placeholder; the page's text or hard result remains isolated. The
   configured `pdfplumber` fallback applies only to AnyDoc extraction failures.
6. Cache hits restore the existing `VisionResult` contract for the image record
   but create no new call record and add no new token totals. Cache misses
   create one `describe_image` call record per canonical image only. The image
   cache key must include the backend name in addition to the existing image,
   prompt, model, and configuration dimensions.
7. The document sidecar contains image records. `run.json` contains image
   `describe_image` call IDs, usage, latency, and aggregate cache totals; it
   does not duplicate the full image-record list.

## Task Order And Dependencies

| Task | Outcome | Depends on |
|---|---|---|
| `task-016` | Explicit image-stage seam and offline synthetic fixture contract | `task-015` review gate |
| `task-017` | End-to-end images in `TEXT` pages | `task-016` |
| `task-018` | `COMPLEX` image handling and `SCANNED` exclusion | `task-017` |
| `task-019` | Image cache, usage/latency metrics, sidecar, and `run.json` wiring | `task-017`, `task-018` |
| `task-020` | Crop/filter/dedupe/placement/failure determinism hardening | `task-017`, `task-018`, `task-019` |
| `task-021` | Optional Kelpie probe and authorized read-only regression matrix | `task-020` |

There are no circular dependencies. The `task-015` review gate is accepted and
tasks `016` through `021` have completed their QA gates. The post-trial loop
starts with `task-022` as `ready`; tasks `023` through `026` remain `planned`.
A task becomes `completed` only after its own QA passes, and only the next row
may then become `ready`.

## Test And Verification Policy

- Every task starts with a failing offline test or a failing contract assertion.
- Synthetic PDFs are the default fixtures. They must include at least a text
  page with an embedded figure, a complex page with an embedded figure, and a
  scanned page represented by a full-page image.
- Fakes must expose calls and usage without network access. Tests must assert
  that one broken crop or description cannot abort unrelated pages.
- Optional AnyDoc/Kelpie tests are separately marked and safely skipped when
  dependencies or approved environment variables are absent.
- Every task runs, from the workspace root:

  ```text
  python -m pytest -q
  python -m ruff check src tests
  python -m mypy src
  ```

- The authorized corpus check reads PDFs in place, never copies them, never
  stores rendered pages or Markdown, and writes only aggregate anonymised
  results to the approved temporary location or test report.
- Final output checks must include the Markdown, document JSON sidecar, image
  files, and `run.json`; image records belong to the document sidecar while
  image calls and aggregate cache/usage/latency belong to `run.json`. Only
  generated image files under the requested output directory are allowed to
  contain PDF-derived bytes.

## Review Gate

The plan was reviewed internally for numeric ordering, dependency direction,
test-first execution, contract fidelity, data-safety boundaries, and separation
of required versus optional work. The review result and any corrections are
recorded in the implementation prompt and in the final planning response.

## Post-Trial Corrective Loop

The first user-level trial against the authorized `unstructured-ingest-source`
corpus found five general follow-up gaps: public runtime wiring, prompt resource
packaging, same-band figure ordering, warm-cache sidecar determinism, and the
installed-tool/corpus smoke gate. These are ordered as tasks `022` through
`026`; they must use the same test-first, contract-fidelity, and data-safety
rules as tasks `016` through `021`.

| Task | Outcome | Depends on |
|---|---|---|
| `task-022` | Public CLI/API runtime constructs image and hard adapters | `task-021` trial |
| `task-023` | Installed wheel packages prompts and resolves the correct entry point | `task-022` |
| `task-024` | Same-band and overlapping figures preserve stable source order | `task-023` |
| `task-025` | Warm-cache document sidecars remain deterministic | `task-024` |
| `task-026` | Disposable installed-tool and authorized corpus regression gate | `task-025` |
