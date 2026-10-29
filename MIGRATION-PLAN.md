# Frankenstein Migration Plan

**Status:** draft; Phase 0 is signed off, task-015 is reviewed, and the
image-context corrective loop through task-026 is complete.

## Objective

Replace the fragile Python fast parser with a tested AnyDoc Rust adapter while preserving the useful `doc2md` domain contract: per-page routing, provenance-rich JSON, deterministic Markdown, Kelpie hard pages, image handling, cache, metrics, and isolated failures.

The migration is not a rewrite of the whole application. Rust owns deterministic document parsing. Python owns orchestration and the stable output contract. Kelpie owns OCR and visual transcription.

## Source And Workspace

- Source implementation: `C:\Users\rp99480\dev\doc2md`
- Migration workspace: `C:\Users\rp99480\dev\doc2md_frankestein`
- Source implementation is read-only until a later cutover decision.
- Confidential PDFs, outputs, credentials, prompts containing secrets, and model responses stay outside Git.

## Target Architecture

```text
PDF
 |
 +-- PdfSource: open once, expose page bytes and rendered images
 |
 +-- Inspector: pdfplumber signals and configurable route decision
 |      |
 |      +-- TEXT ----------------> AnyDocFastExtractor (local Rust)
 |      |                            |
 |      |                            +-- Markdown -> common Block model
 |      |
 |      +-- COMPLEX --------------> KelpieHardExtractor
 |      |
 |      +-- SCANNED --------------> KelpieHardExtractor (OCR)
 |
 +-- ImageFinder/Filter ----------> Kelpie image descriptions
 |
 +-- Assembly --------------------> Markdown, sidecar JSON, run.json
```

### Ownership rules

- `pdfplumber` owns cheap inspection and routing signals only.
- AnyDoc owns digital-page text/layout extraction and emits canonical Markdown.
- Kelpie owns OCR and visual transcription; no local OCR/model artifacts are added.
- Python owns page numbers, block IDs, failure isolation, cache keys, metrics, and output files.
- The renderer does not reinterpret AnyDoc Markdown. The first adapter version stores one AnyDoc Markdown block per page to avoid another fragile Markdown parser.

## Contract Changes

The existing output contract is retained unless a Phase 0 decision records a change.

Required additions:

- `Provenance.source` gains `anydoc` so output does not falsely claim `pdfplumber` provenance.
- `ToolInfo` records the resolved AnyDoc version and backend.
- Fast backend configuration selects `anydoc` or the emergency `pdfplumber` fallback.
- AnyDoc cache keys include source hash, original page number, AnyDoc version, and backend configuration.
- AnyDoc failures and fallback decisions appear in `PageResult.warnings` and `run.json`.
- A schema version bump is required if the consumer contract treats the new provenance value as breaking.

No Kelpie request or response field may be invented. The existing discovered `VisionBackend` contract remains unchanged.

## Page Granularity

AnyDoc's public PDF API returns Markdown rather than the `doc2md` page/block model. The adapter therefore processes routed digital pages individually in the first implementation.

Phase 0 must verify the supported way to create an in-memory one-page PDF. Prefer an existing permitted dependency and an in-memory path. Do not add a PDF library before checking its license.

The initial output is one stable `anydoc` block per page. Semantic splitting into headings, lists, tables, and paragraphs is a later optimization only if the benchmark proves that block granularity has user value. The Markdown itself remains intact.

## Routing Policy

The first production policy remains compatible with the current specification:

- `TEXT` -> AnyDoc.
- `COMPLEX` -> Kelpie.
- `SCANNED` -> Kelpie.
- AnyDoc import or page conversion failure -> explicit configured `pdfplumber` emergency fallback where usable; otherwise isolated page failure.
- A later benchmark may test AnyDoc-first for `COMPLEX` pages with a quality gate. It must not silently change the default route.

This keeps tables/figures that need visual interpretation on the hard path while proving the Rust fast path on ordinary digital pages first.

## Phases And Gates

### Phase 0 - Discovery and migration contract

No production feature code.

Record:

- current source commit, test/lint/type status, and existing benchmark evidence;
- AnyDoc package/version, Python binding surface, supported Windows/Python wheels, and import behavior;
- one-page PDF construction experiment and page-number preservation;
- AnyDoc output behavior for text, columns, tables, ligatures, German umlauts, empty pages, and malformed PDFs;
- resolved licenses for the Python package, native Rust artifacts, and transitive Rust dependencies;
- current Kelpie discovery and redacted probe evidence, without secrets;
- the exact output/schema decision for `source="anydoc"`;
- migration corpus manifest using only permitted paths and anonymised metadata.

**Gate:** all findings are in `docs/discovery.md`; unresolved API or licensing blockers are listed; the human replies `go`.

### Phase 1 - Adapter spike

Build only a standalone AnyDoc adapter and contract tests. It must not become the default pipeline yet.

The spike proves that a selected original page can be converted to Markdown, wrapped in the common model, and rendered without page drift. It uses fake hard/vision adapters and synthetic PDFs by default.

**Gate:** synthetic digital fixtures pass; a mixed fixture preserves original page numbers; AnyDoc is lazy/import-optional; a missing AnyDoc installation produces a clear configured error; no Kelpie call is made for TEXT pages.

### Phase 2 - Hybrid tiered pipeline

Move the adapter behind the existing fast extraction seam. Keep the current Python parser as an explicit emergency backend, not as a second hidden path.

Implement cache and metrics for AnyDoc pages. Keep Kelpie hard-page and image flows unchanged except for integration with the migrated common model.

**Gate:** end-to-end hybrid conversion passes deterministic, provenance, cache, failure-isolation, and token-accounting tests.

### Phase 3 - Quality hardening

Run the synthetic matrix and the permitted EDAG corpus. Add only general fixes, never filename/page-specific rules.

Test columns, tables, figures, ligatures, German text, blank pages, repeated margins, encrypted/malformed files, mixed digital/scanned documents, and duplicate images.

**Gate:** no regression against the existing accepted outputs; AnyDoc and Kelpie methods are visible in JSON and `run.json`; failed pages remain isolated.

### Phase 4 - Cutover decision

Run cold-cache comparisons for:

- current `pdfplumber` fast path;
- AnyDoc fast path;
- hybrid AnyDoc + Kelpie;
- full vision;
- current EDAG baseline when available.

Measure quality, wall time, hard-page percentage, Kelpie calls, input/output/total tokens, output size, and failure rate.

**Gate:** human approves whether AnyDoc becomes the default fast backend. If not, retain it as an opt-in diagnostic backend and document why.

### Phase 5 - Cleanup and packaging

Remove only code proven unused by the cutover decision. Keep an explicit fallback until the output contract and benchmark evidence justify deleting it. Publish dependency notices and installation instructions for the native AnyDoc package.

## Test Strategy

- Unit tests use fake fast and vision adapters at the seam.
- AnyDoc integration tests are marked separately and require the optional dependency.
- Kelpie integration tests remain marked `kelpie` and skipped without approved environment variables.
- Tests never require confidential PDFs, secrets, network access, or local model artifacts.
- Golden tests assert Markdown, sidecar JSON, page numbers, method provenance, and deterministic output.
- Contract tests run against both the AnyDoc adapter and the emergency pdfplumber adapter.

## Rollback

Rollback is configuration-level during migration:

1. Select `fast.backend=pdfplumber`.
2. Keep Kelpie hard routing and output schema unchanged.
3. Preserve AnyDoc run data and benchmark reports for diagnosis.
4. Do not delete the fallback until a later release explicitly removes it.

No destructive replacement of the original `doc2md` workspace is part of this plan.

## Definition Of Done

- AnyDoc is local-only for digital pages and never silently calls Firecrawl.
- Scanned and visual pages use Kelpie through the discovered contract.
- Every block retains original page provenance and a truthful source method.
- A single bad page cannot abort the document.
- Cache hits make no new Kelpie calls.
- The hybrid pipeline has reproducible benchmark evidence on the permitted corpus.
- The default backend is chosen by evidence and recorded in `docs/decisions.md`.
