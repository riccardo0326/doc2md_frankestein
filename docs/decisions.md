# Decisions

## D001 - Keep the original workspace intact

The migration starts in `C:\Users\rp99480\dev\doc2md_frankestein`. The existing `doc2md` workspace is treated as a read-only reference until a separate cutover decision. This protects the current implementation and its benchmark evidence while the hybrid path is proved.

## D002 - Rust is an adapter, not the orchestrator

AnyDoc owns local digital-document parsing. Python retains routing, provenance, cache, metrics, rendering, and failure isolation. Kelpie remains the only enterprise OCR/vision inference path.

## D003 - Phase 0 precedes production code

AnyDoc package behavior, page slicing, native dependency licensing, and the provenance contract must be evidenced before the first production migration task starts.

## D004 - AnyDoc is local-only and optional

The selected package is `firecrawl-anydoc==0.2.4`, imported as `anydoc`. The
adapter may use `to_markdown_bytes(..., ocr="reject")` for routed digital pages.
The hosted Firecrawl fallback is outside the enterprise path and must never be
enabled implicitly. A missing package, local conversion error, or scan result
must remain an explicit configured failure/fallback.

## D005 - First adapter output is one AnyDoc block per page

The public AnyDoc PDF API returns Markdown only and does not expose stable PDF
block metadata, page markers, bounding boxes, usage, or image records. The
first adapter will therefore preserve the complete AnyDoc Markdown as one
Python-owned block for each successfully converted original page, with
`provenance.source="anydoc"` and the original 1-based page number.

## D006 - Use pypdf for the in-memory page seam

The selected page seam is `pypdf==6.21.3`: `PdfReader` reads the source,
`PdfWriter.add_page()` writes the selected page to an in-memory `BytesIO`, and
Python retains the original 1-based page number. It is BSD-3-Clause and
preserved geometry and image XObjects in the synthetic and authorized sample
corpus. The adapter must pre-check/reroute blank and image-only pages and must
not turn `NeedsOcrError` into hosted OCR. A native Rust page-level seam is only
needed if a valid routed TEXT page later fails this boundary.

## D007 - Use the Apache-2.0 option for ryu

The AnyDoc package and `pdf-inspector` are MIT. The bundled Rust SBOM has 118
components and lists `ryu 1.0.23` as `Apache-2.0 OR BSL-1.0`. The human
approved use of the Apache-2.0 option on 2026-10-27; no BSL-1.0 exception is
required.

## D008 - Keep the bootstrap runtime dependency-free

Task 002 keeps the base package's runtime dependency list empty. The task adds
only the development tools `pytest` (MIT), Ruff (MIT), and mypy (MIT) as an
optional `dev` extra.
AnyDoc, Docling, Kelpie, PDF libraries, and conversion dependencies remain out
of the bootstrap package until a task explicitly needs them and records their
license and import boundary. This is a deliberate deviation from the source
workspace's broader runtime dependency list and keeps the import smoke test
offline and lazy.

## D009 - Keep schema 1.0 for the additive AnyDoc source

The approved `anydoc` provenance value is an additive method value in the
common contract and is serialized truthfully as `source="anydoc"`. Schema
version `1.0` remains in force because Phase 0 found no consumer requiring a
closed source enum. A consumer that rejects the new value must use an explicit
compatibility decision and schema bump; the renderer must not relabel AnyDoc
output as `pdfplumber`.

Pydantic v2 is now a runtime dependency because the task-003 contract is built
from frozen Pydantic models. Its MIT license is permitted by the project
allow-list.

## D010 - Keep the AnyDoc adapter optional and local-only

The `anydoc` extra contains `firecrawl-anydoc` (MIT, with the native license
approval in D007), `pypdf` (BSD-3-Clause), and `reportlab` (BSD) for synthetic
optional integration fixtures. The base package remains installable without
these packages. The adapter imports both AnyDoc and pypdf lazily, always passes
`ocr="reject"`, and converts OCR-needed pages into a hard-path handoff instead
of invoking hosted Firecrawl OCR.

## D011 - Keep inspection pdfplumber-only and conservative

Task 005 adds `pdfplumber` (MIT) and Typer (MIT) as runtime dependencies for
inspection and the `doc2md inspect` command. Inspection computes only configured
signals, applies first-match routing, and never imports or invokes AnyDoc,
Docling, or Kelpie. The initial thresholds are the architecture defaults:
`min_chars=50`, `min_chars_text_layer=10`, `scan_image_ratio=0.6`,
`max_garbled=0.02`, `table_none_ratio=0.15`, `complex_image_ratio=0.4`, and
`image_page_min_chars=400`. Table extraction errors route conservatively as
irregular tables.

## D012 - Keep the hybrid loop injectable before hard-path wiring

Task 006 adds `PdfConverter` as a standalone, dependency-injected loop. `TEXT`
pages use AnyDoc, while `COMPLEX` and `SCANNED` pages become explicit hard-path
work and fail in isolation until a hard extractor is supplied. The pdfplumber
fallback is available only when `Config.fast.fallback="pdfplumber"` and an
explicit fallback callable is injected. No default route calls AnyDoc for hard
pages, and strict mode raises `ConversionFailed` only after page isolation.

This records the Phase 1/2 gate: the mixed synthetic slice preserves original
pages, methods, warnings, deterministic Markdown, and sidecar output without
making the hybrid converter depend on Kelpie or changing inspection policy.

## D013 - Keep Kelpie behind the discovered VisionBackend contract

Task 007 adds an optional `kelpie` extra containing `openai` (Apache-2.0),
`httpx` (BSD), and `pypdfium2` (BSD/Apache). The thin client uses the discovered
OpenAI Responses API shape at `/openai/v1/responses`: native `input_text` plus
`input_image` data URLs, `store=False`, and no vision-incompatible temperature
parameters. It uses environment/configuration names only, keeps TLS verification
enabled, and raises `VisionUnavailable` without configured service access.

Kelpie hard extraction renders only selected original pages, parses returned
Markdown into `vision` blocks, and exposes `(call_id, VisionResult)` through
`drain_calls()` so usage and latency remain observable. Empty responses and
backend failures become typed hard extraction failures. The real `kelpie` test
is marker-guarded and skips without the approved environment variables; no local
OCR or model artifacts are installed.

Real proxy verification on 2026-10-28 passed against the active local
`kelpie serve run` proxy at `127.0.0.1:18080` with `DARE-NoCloud-Helios`. The
proxy returned response content in `output[*].content[*]`, so the client also
accepts documented `output_text`/`reasoning_text` content blocks when the SDK
convenience field is empty. No response text, token values, or credentials were
stored.

## D014 - Treat scanned full-page images as hard-path input

Task 008 extracts embedded figures only from digital/eligible pages. A
`SCANNED` page's full-page image is not recorded as an embedded figure and is
not sent to the image-description backend a second time; OCR/visual handling
remains the Kelpie hard path. Image filtering uses the approved size, area,
aspect-ratio, and SHA-256 deduplication rules. Description failures become
failed `ImageRecord`s and never abort the document.

## D015 - Derive run metrics from cache-aware call records

Task 009 uses JSON-only content-addressed cache entries under the configured
cache directory. Keys include source/page or image identity, backend/version,
prompt/model, and output-affecting configuration. Writes use a temporary file,
flush, and atomic `os.replace`; corrupt entries are deleted individually and
reported as warnings. Cache hits do not create call records or add token totals.

`MetricsCollector` derives calls, latency, token totals, estimated flags, page
stats, and cache counts from run-local records. `--no-cache` disables reads and
writes for a cold run. Image descriptions expose the same cache seam without
changing the Kelpie request contract.

## D016 - Keep comparison pipelines as routing policies

Task 010 keeps `tiered`, `full-vision`, and `docling-only` behind the same
`PdfConverter` loop. `full-vision` uses the injected vision seam for every
selected page and disables duplicate image handling; `docling-only` uses the
injected development hard seam and is never the enterprise default. No Docling
import or artifact provisioning occurs in tiered conversion, and unavailable
development hard dependencies fail only the affected diagnostic page.

## D017 - Keep benchmark execution isolated and baseline-optional

Task 011 writes one timestamped run directory with redacted `env.json`, exact
`results.csv` columns, and separate output/cache directories for every
document/pipeline/repetition. The current EDAG baseline is an optional adapter;
unavailability records a row error and never aborts other pipelines. The suite
contains only permitted paths and never copies source PDFs into the repository.

## D018 - Keep quality review blind and judge-optional

Task 012 samples pages stratified by class with a fixed seed, writes pipeline
outputs under blind labels, and stores a round-trippable unblinding map. Manual
scores remain pending until a reviewer fills the sheet. Judge calls use the
existing vision seam only when configured; malformed or unavailable responses
become structured errors. Reports explicitly state approved-model/style-bias
limitations, sample size, and missing baseline data.

## D019 - Record corpus limitations instead of adding sample-specific rules

Task 013 verified the synthetic suite and six authorized external PDFs without
copying inputs or outputs. Five text pages converted through local AnyDoc; three
complex and three scanned pages remained isolated failures because the default
hybrid slice has not yet wired a hard extractor. This is documented as a
capability limitation in `docs/corpus-results.md`; no filename-, page-, or
sample-specific branch was added.

## D020 - Keep AnyDoc as provisional TEXT default without full cutover

Task 014 records AnyDoc as the default local fast backend for `TEXT` pages, based
on local binding/provenance evidence. This is not a complete enterprise cutover:
real Kelpie hard-path measurements and manual/judge quality scores are
unavailable. The current EDAG baseline is explicitly out of scope because its
PDF set and invocation/telemetry contract are not supplied. Retain the explicit
pdfplumber rollback/fallback and revisit the decision after measurements on
permitted, synthetic, or public PDFs.

## D021 - Release with fallback and audit boundaries preserved

Task 015 packages version `0.1.0` with optional `anydoc`, `kelpie`, and `dev`
extras. The release keeps pdfplumber rollback explicit, does not install model
artifacts, and records direct Python plus native AnyDoc license evidence. The
EDAG baseline remains outside scope; public/approved PDFs and synthetic fixtures
are the permitted evaluation inputs.

## D022 - Image-context verification remains evidence-bounded

The image-context enhancement is verified offline with synthetic `TEXT`,
`COMPLEX`, and `SCANNED` fixtures, fake vision calls, deterministic assets,
cache-aware metrics, sidecars, failure isolation, and explicit fallback tests.
Image records remain owned by the document sidecar; image calls and aggregate
usage, latency, and cache totals remain in `run.json`.

The optional Kelpie image probe and the authorized read-only corpus check remain
environment-dependent. A skipped or unavailable run is recorded as a limitation,
not as evidence of enterprise cutover. The explicit pdfplumber fallback and the
no-hosted-OCR boundary remain unchanged.

## D023 - Close the post-trial image-context defects without claiming cutover

Tasks 022-025 close the verified public-runtime, prompt-packaging, figure-order,
and warm-cache sidecar defects. The normal API and CLI now assemble the configured
AnyDoc, Kelpie hard-page, and image adapters; prompt resources are packaged and
resolved independently of the current working directory; overlapping figures
retain source order; and cache-hit telemetry does not alter document content.

Final offline verification on the migration workspace produced 90 passed and 5
skipped tests, with Ruff passing and the Python-3.12-targeted mypy run passing.
The default mypy target remains blocked only by the installed NumPy stub's
Python-3.12 `type` syntax. The installed public command resolved the wheel from
the disposable environment and resolved both packaged prompts.

The installed public CLI representative check completed four documents with no
CLI-level aborts; optional AnyDoc/Kelpie absence isolated nine page failures and
produced no image records. The exact permitted read-only corpus guard passed in
aggregate-only mode. No Kelpie service variables were available, so real Kelpie
calls remain safely skipped. These results do not claim enterprise cutover.
