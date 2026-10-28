# Phase 0 Discovery

**Date:** 2026-10-27  
**Status:** discovery complete; human sign-off `go` received on 2026-10-27.  
**Scope:** AnyDoc feasibility for the migration workspace only. No production
adapter was added, the source workspace was not modified, and neither Kelpie nor
hosted Firecrawl OCR was called by this task.

## Executive Result

AnyDoc `0.2.4` has a compatible Windows AMD64 CPython wheel for the current
Python 3.14 environment and exposes an in-memory `to_markdown_bytes()` binding.
The local path is deterministic, fast on the synthetic text fixture, and did not
open a network socket. It produced usable Markdown for headings, columns,
tables, ligatures, German umlauts, and a multi-page digital PDF.

It is not a drop-in page adapter yet. Its public PDF result is a single Markdown
string with no page/block metadata. Isolated pages must therefore be wrapped in
the common model by Python. `pypdfium2` can write an in-memory one-page PDF, but
AnyDoc classified an isolated page containing text plus an embedded image as
`ImageBased`; a blank isolated page raised `NeedsOcrError`. A `pypdf` experiment
preserved the page and image resources but had the same AnyDoc behavior. This is
an unresolved page-slicing limitation, not a reason to silently enable hosted
OCR.

The native Rust SBOM contains 118 components. Top-level and `pdf-inspector`
licenses are MIT. The human approved consumption of `ryu 1.0.23`, declared
`Apache-2.0 OR BSL-1.0`, under its Apache-2.0 option.

## 1. Source Baseline

Source workspace: `C:\Users\rp99480\dev\doc2md` (read-only).  
Current commit: `af11eb9f4152dc34c8a7e7c7da085478ab007099`.  
Source branch: `feature/task-013-parser-fixes`, tracking
`origin/feature/task-013-parser-fixes`.

The source worktree was already dirty before this task with one untracked file,
`docs/research-anydoc.md`; it was not changed.

Commands and results:

| Command | Result |
|---|---|
| `python -m pytest` | 83 passed, 2 skipped, 4 deselected; 85 selected; 8.68 s |
| `ruff check .` | pass: `All checks passed!` |
| `mypy .` | fail: 12 pre-existing errors in `tests/test_signals.py`, `scripts/kelpie_probe.py`, `tests/test_phase6.py`, `tests/test_phase7.py`, `tests/test_hard.py` |

The mypy failure is recorded, not fixed, because Phase 0 forbids production
changes and the source workspace is read-only.

## 2. Environment

Collected on the current workstation, not necessarily the future enterprise
host:

| Item | Evidence |
|---|---|
| OS | Windows 11 Enterprise 10.0.26200, 64-bit |
| Python | 3.14.7 (`C:\Python314`) |
| CPU | 12 logical processors |
| Memory | 16,802,504,704 bytes, approximately 15.7 GiB |
| pip | 26.2.1 |
| uv | unavailable (`uv` command not found) |

AnyDoc was installed only in the disposable environment
`C:\Users\rp99480\AppData\Local\Temp\opencode\doc2md-phase0-venv`.
Synthetic PDFs and the temporary wheel were kept under the pre-approved temp
directory and are not migration inputs.

## 3. AnyDoc Package And Wheel

Installation command:

```text
<phase0-venv>\Scripts\python.exe -m pip install --upgrade firecrawl-anydoc
```

Observed package:

| Item | Result |
|---|---|
| Python package | `firecrawl-anydoc==0.2.4` |
| Import | `import anydoc` |
| Wheel | `firecrawl_anydoc-0.2.4-cp310-abi3-win_amd64.whl` |
| Python requirement | `>=3.10` |
| Current wheel compatibility | CPython 3.14 AMD64 Windows: installed successfully |
| Python dependencies | none declared by the wheel |
| Native artifact | `anydoc\_anydoc.pyd` plus type stubs |
| Package license | MIT |

The `cp310-abi3-win_amd64` tag supports the current CPython ABI family on
Windows AMD64 from Python 3.10 upward. This evidence does not establish support
for Windows ARM, 32-bit Windows, or other operating systems.

Public binding surface observed with `inspect.signature`:

```text
anydoc.to_markdown_bytes(
    data: bytes | bytearray,
    format: Format | None = None,
    *,
    ocr: Literal['reject', 'hosted'] = 'reject',
    api_key: str | None = None,
    api_url: str | None = None,
) -> str

anydoc.to_markdown(path, *, ocr='reject', api_key=None, api_url=None) -> str
```

The binding has `NeedsOcrError`, `MalformedError`, `UnsupportedError`, and
other typed conversion errors. There is no `anydoc.convert()` function.

## 4. Local Import And Hosted Boundary

The exact local call used in the experiment was:

```python
import anydoc
markdown = anydoc.to_markdown_bytes(pdf_bytes, format="pdf", ocr="reject")
```

The installed binding source documents that `ocr="reject"` is the default and
that `ocr="hosted"` is the separate Firecrawl Parse fallback. Its hosted helper
constructs a `POST` to `/v2/parse`, sends the whole document, and uses
`FIRECRAWL_API_KEY`/`FIRECRAWL_API_URL` if configured. Those options were not
used.

Evidence for local-only behavior:

- A local conversion was run with `socket.socket.connect` patched to fail. The
  conversion completed, so no network socket was opened.
- The binding's `_parse_hosted` helper was patched to fail. The local conversion
  completed without calling it.
- The local conversion returned Markdown from bytes with `ocr="reject"`.
- No Firecrawl URL, API key, credential, or hosted response was used.

For an image-only synthetic PDF, local conversion raised
`NeedsOcrError: page 1 of 1 needs OCR`. This is the required safe failure. The
adapter must never change this into hosted OCR implicitly.

Primary references:

- Installed metadata: `firecrawl_anydoc-0.2.4.dist-info/METADATA`.
- Installed binding: `anydoc/__init__.py`.
- Existing primary-source report: `C:\Users\rp99480\dev\doc2md\docs\research-anydoc.md`.
- Upstream repository: `https://github.com/firecrawl/anydoc`.

## 5. Synthetic PDF Experiment

The fixture was generated in memory with ReportLab and Arial, then written only
to the temporary work directory. It contained three digital pages:

1. Heading, two visual columns, German `Straße`/`Übergröße`, and ligatures
   `ﬁ ﬂ ﬀ ﬃ ﬄ ﬅ ﬆ`.
2. A GFM-compatible table, German text, and one embedded raster image.
3. A blank page.

The direct multi-page call was:

```text
anydoc.to_markdown_bytes(digital_pdf_bytes, format="pdf")
```

Observed result:

| Case | Result |
|---|---|
| Conversion time | 0.006 s on this warm synthetic run; not a benchmark |
| Output type | `str`, UTF-8 Python text |
| Trailing newline | present |
| Heading | emitted as Markdown heading |
| Columns | both columns emitted, but reading order was left/right by line rather than separate page blocks |
| Table | emitted as a pipe table with header separator |
| Ligatures | normalized to `fi`, `fl`, `ff`, `ffi`, `ffl`, `st`, `st` |
| German umlauts and `ß` | preserved in the Python string and Markdown |
| Blank page | omitted from the combined Markdown; no blank-page marker |
| Embedded image | no image record or image Markdown was emitted by the PDF API |
| Page metadata | no page markers, page array, block IDs, or source method |

Redacted/compact output evidence, with Unicode escaped:

```text
# Heading One

Stra\xdfe \xdcbergr\xf6\xdfe and ligatures: fi fl ff ffi ffl st st

Left column line one Right column line one Left column line two Right column line two

|Kopf|Wert|
|---|---|
|Stra\xdfe|\xdcbergr\xf6\xdfe|
|A|B|

# Table Page
```

Malformed input:

```text
anydoc.to_markdown_bytes(b"%PDF-1.7\\nnot a valid pdf", format="pdf")
-> MalformedError: malformed document: invalid PDF structure
```

The source-level research also records that local PDF conversion returns only a
Markdown string, not the generic asset/block document model. This must not be
assumed to provide sidecar provenance.

## 6. Page Slicing And Page Provenance

### pypdfium2 experiment

Installed `pypdfium2==5.14.0` exposes `PdfDocument.new()`,
`PdfDocument.import_pages(pdf, pages=[...])`, and `save(file_like)`. A page was
selected in memory and saved to an in-memory `BytesIO` object.

Observed for the synthetic fixture:

| Selected source page | Slice result through AnyDoc |
|---:|---|
| 1, text/columns | usable Markdown; content remained extractable |
| 2, table plus embedded image | `UnsupportedError: unsupported input: PDF has no extractable text (ImageBased, 1 pages)` |
| 3, blank | `NeedsOcrError: page 1 of 1 needs OCR` |

The slice retained page size `(612.0, 792.0)` and the page object list included
`PdfImage` for page 2. The page number in the sliced PDF is nevertheless local
page 1; AnyDoc emitted no original page number. Python must retain and attach the
original 1-based page number outside the AnyDoc result.

### pypdf comparison

`pypdf==6.21.3` was downloaded after inspecting its wheel metadata
(`License-Expression: BSD-3-Clause`) and installed only in the disposable
environment. Its `PdfReader`/`PdfWriter.add_page()` path preserved page geometry
and the page-2 XObject, but produced the same AnyDoc outcomes: page 1 worked,
page 2 with an image was `ImageBased`, and the blank page raised
`NeedsOcrError`. A table-only page sliced with pypdf converted successfully.

### Decision and limitation

An in-memory one-page PDF path exists. The selected Phase 1 approach is
`pypdf==6.21.3` with `PdfReader`/`PdfWriter.add_page()` and `BytesIO`, because
it preserved page geometry and image XObjects in both synthetic and real sample
tests. The adapter must retain the original page number outside AnyDoc and must
pre-check pages before conversion. Blank/image-only pages remain outside the
AnyDoc fast path; they must use the configured hard/fallback behavior and never
implicitly enable hosted OCR. A native Rust page-level seam is only a fallback
investigation if a valid routed TEXT page fails this pre-check.

### Real sample verification

The user-authorized, read-only corpus path was
`C:\Users\rp99480\dev\doc2md\samples\unstructured-demo`. Six PDFs were tested
without copying content or storing Markdown:

| Anonymised sample | Pages | Whole-document AnyDoc | Per-page pypdf slice |
|---|---:|---|---|
| `unstructured-demo-01` | 1 | ok | 1/1 ok; embedded image present |
| `unstructured-demo-02` | 1 | ok | 1/1 ok; 3 embedded images present |
| `unstructured-demo-03` | 4 | ok | 2/4 `NeedsOcrError` blank pages; 2/4 ok |
| `unstructured-demo-04` | 2 | ok | 2/2 ok |
| `unstructured-demo-05` | 2 | ok | 2/2 ok |
| `unstructured-demo-06` | 1 | `NeedsOcrError` image-based | 1/1 `NeedsOcrError`; 1 image |

The real corpus confirms the seam for text-bearing pages and image-bearing pages
with a usable text layer. It also confirms that blank pages and image-based
pages must be routed or isolated before AnyDoc. The experiment patched both
socket connection and the hosted helper to fail; no network or hosted OCR was
used.

## 7. Kelpie Discovery (Redacted Existing Evidence)

Kelpie was not called in this task, as required. The existing source discovery
and redacted probe evidence were used as the reference record. The reference
project `C:\Users\rp99480\dev\ai4tc_webapp` remains read-only.

Reference files recorded by the existing discovery:

- `utils/kelpie_client.py`: lazy Kelpie authentication and OpenAI transport.
- `utils/llm_loader.py`: deployment selection and Responses API wrapper.
- `config/llm_gateway_settings.py`: environment aliases and timeouts.
- `backend/services/ingestion/vision/pdf_extraction.py`: page image request shape.
- `backend/services/ingestion/vision/image_extraction.py`: image-plus-text shape.
- `tests/check_kelpie_install.py` and `tests/check_kelpie_vision.py`: diagnostics.
- `utils/llm_errors.py`: retry/failure classification.

Redacted convention:

- Transport: OpenAI Python SDK Responses API through the Kelpie-authenticated
  DARE gateway.
- Auth configuration names only: `KELPIE_SERVICE_ACCOUNT_KEY_FILE`,
  `LLM_GATEWAY_ENDPOINT`, `LLM_VISION_DEPLOYMENT`, `LLM_CHAT_DEPLOYMENT`,
  `LLM_TIMEOUT`, `LLM_REQUEST_TIMEOUT_SECONDS`, `SSL_CERT_FILE`, and
  `SSL_CERT_DIR`. No values are recorded.
- Base URL construction: gateway endpoint plus `/openai/v1`; the local proxy
  evidence used a loopback URL, while enterprise service endpoints remain
  configuration values and were not called here.
- Text request: `responses.create(model, instructions, input,
  max_output_tokens, store=False)`.
- Image request: Responses input content with text plus a base64 image data URL,
  mapped to `input_text` and `input_image` in the thin-client shape.
- Response: `output_text` for text, raw response usage for token accounting.
- Usage: the redacted probe observed input/output/total usage on successful
  calls; missing usage must be estimated and flagged by doc2md.
- Timeouts/retries: reference defaults to a 600-second timeout, disables SDK
  retries, and has application handling for HTTP 502. It has no complete 429
  policy. The future doc2md adapter must implement its own required timeout,
  429/5xx retry policy.
- Image size/concurrency: no fixed image byte/pixel maximum was evidenced;
  safe concurrency was not established. Existing evidence recommends starting
  with one worker.
- Vision deployment observed by the existing redacted probe: `DARE-NoCloud-Helios`.
  Text/judge candidate: `DARE-NoCloud-Nova`; Nova was not vision-capable in the
  recorded probe. No model files are installed on the enterprise PC.

This task did not create `scripts/kelpie_probe.py`, did not call Kelpie, and did
not create `docs/kelpie-example.md`; those already exist in the source evidence
referenced above and must not be copied with secrets or model responses.

## 8. Licensing Audit

Commands/evidence:

```text
<phase0-venv>\Scripts\pip-licenses.exe --packages firecrawl-anydoc --format=markdown
-> firecrawl-anydoc 0.2.4 MIT
```

The installed wheel has no Python `Requires-Dist` entries. Its bundled SBOM is
`firecrawl_anydoc-0.2.4.dist-info/sboms/anydoc-python.cyclonedx.json`.

| Artifact | Evidence | Result |
|---|---|---|
| Python package | wheel metadata | MIT, allowed |
| Native anydoc crate | SBOM component `anydoc 0.2.4` | MIT, allowed |
| Native binding | SBOM component `anydoc-python 0.2.4` | MIT, allowed |
| PDF parser | SBOM component `pdf-inspector 1.14.2` | MIT, allowed |
| Rust transitive set | SBOM | 118 components; no missing license expression |
| Rust transitive exception | `ryu 1.0.23` | `Apache-2.0 OR BSL-1.0`; human approved Apache-2.0 consumption on 2026-10-27 |
| Slicing experiment only | `pypdf 6.21.3` | BSD-3-Clause, allowed; not yet a project dependency |

The existing environment-wide pip report also contains unrelated Docling
packages, including a Torch BSL-1.0 expression. That is not evidence that AnyDoc
requires Torch; AnyDoc declares no Python dependencies. It remains outside this
AnyDoc package decision.

The license review is resolved by the human approval recorded above. The
selected legal basis is the Apache-2.0 option; no BSL-1.0 exception is being
requested.

## 9. Current Contract Comparison

The existing sidecar contract requires every block to have an original page,
stable block ID, Markdown/text, and truthful `source`; it also requires
page-level failure isolation, image records, cache keys, metrics, and
`run.json`. AnyDoc's PDF binding provides only a Markdown string and does not
provide those fields.

The first adapter can still use one stable `anydoc` block per successfully
converted routed page:

- `block_id`: Python-generated `p{original_page:04d}-b001`.
- `provenance.page`: original 1-based page number retained outside AnyDoc.
- `provenance.source`: new value `anydoc`.
- `markdown` and `text`: AnyDoc output, without reinterpretation.
- `bbox`: `null`; no AnyDoc PDF block metadata was observed.
- page warnings: record AnyDoc error/fallback reason and whether a pre-check
  skipped blank/image-only input.

One block per page is sufficient for the Phase 1 adapter spike because AnyDoc
does not expose stable PDF block metadata. Semantic splitting would invent
provenance and is deferred.

## 10. Proposed Migration Decisions

| Item | Phase 0 proposal |
|---|---|
| Provenance | Add `anydoc` to the `Provenance.source` literal. This is a schema contract change; use the next schema version if consumers treat the literal as closed. |
| Tool metadata | Record AnyDoc package/native version and backend in `ToolInfo`. |
| Cache key | Source hash + original page number + AnyDoc version + backend/config hash. |
| Routing | Keep `TEXT -> AnyDoc`, `COMPLEX/SCANNED -> Kelpie` as the default. Do not route scans to Firecrawl. |
| AnyDoc failure | Configured pdfplumber emergency fallback only where usable; otherwise isolate the page failure and record the reason. |
| Blank/image-bearing slices | Pre-check and route according to page class; do not classify `NeedsOcrError` as permission to call hosted OCR. |
| Page seam | Prove the adapter with synthetic text/table fixtures first; evaluate a native Rust page-level seam if the slicing limitation affects valid TEXT pages. |
| Kelpie | Implement a thin client after sign-off using the discovered reference convention; do not import or copy the reference project. |

## 11. Corpus Manifest

No PDF was copied into this workspace and no Markdown output was stored. The
user-authorized source corpus was processed read-only for metadata, conversion
status, and error classification only.

The six-file anonymised manifest is recorded in section 6. Existing source
evidence also records two separate confidential five-page samples; those were
not copied or opened by this follow-up. No filenames, excerpts, model
responses, credentials, or token values are repeated here.

## 12. Open Blockers And Risks

1. **Page slicing boundary:** AnyDoc has no public page/block API. In-memory
   slicing works for text-bearing pages and image-bearing pages with a text
   layer, but blank and image-only pages do not produce usable AnyDoc Markdown.
2. **Output contract:** AnyDoc emits no page/block/image/usage/cache metadata;
   Python must provide the complete wrapper and cannot claim AnyDoc supplied
   those fields.
3. **Source quality:** source mypy is currently red with 12 errors even though
   tests and Ruff pass.
4. **Kelpie validation:** this task intentionally did not call Kelpie; the
   recorded reference probe is redacted evidence, not a new target-machine
   connectivity test.

## 13. Reproducibility And Safety

The commands and versions above are sufficient to reproduce the package and
synthetic experiments in the disposable environment. Reproduction must use
synthetic PDFs only. Do not set hosted OCR options, do not provide Firecrawl or
Kelpie credentials, do not copy confidential PDFs, and do not install local OCR
or layout model artifacts on an enterprise PC.

The human reviewed this report and replied with the exact word **`go`** on
2026-10-27. No production migration task was started by this follow-up.
