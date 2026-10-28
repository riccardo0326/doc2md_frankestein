# Findings

**Date:** 2026-10-28  
**Scope:** Phase 4 cutover evidence available in this workspace.  
**Decision status:** provisional; no enterprise go/no-go quality claim is made.

## Evidence

| Evidence | Location | Environment |
|---|---|---|
| Offline synthetic and contract suite | `python -m pytest -q` | 53 passed, 2 skipped; Python 3.14.7; Windows 11 AMD64 |
| Authorized corpus aggregate | `docs/corpus-results.md` | 6 read-only PDFs, 11 pages; no bytes/output committed |
| Cold-cache comparison smoke | `bench_runs/20261028-103214/` | `env.json` records Python/OS/CPU, versions, config hash, cold cache |

The comparison run is a schema and orchestration smoke run using deterministic
fake conversion results. It is not a production quality or token-savings
measurement. The current EDAG baseline is explicitly out of scope because its
PDF set and invocation/telemetry contract are not supplied.

Versions in the smoke environment:

- `doc2md`: 0.1.0
- `pydantic`: 2.14.1
- `pdfplumber`: 0.11.10
- `firecrawl-anydoc`: 0.2.4
- `openai`: not installed in the offline smoke environment

## Comparison

| Criterion | Result | Interpretation |
|---|---|---|
| Token savings | Not measurable | Fake smoke usage is zero; real Kelpie telemetry is unavailable |
| Local CPU time | Smoke-only | Values are fake deterministic timings and must not support a product claim |
| Quality | Not measurable | No completed manual/judge scores; EDAG baseline is out of scope |
| Robustness | Partial pass | Synthetic suite passes; corpus hard pages remain isolated failures until hard wiring is complete |
| Provenance/methods | Pass in contract tests | Original pages and method values are preserved by the tested seams |
| Baseline comparison | Out of scope | EDAG PDFs and invocation/telemetry contract are not supplied |
| Rollback | Available | Keep `fast.backend=pdfplumber` and explicit fallback configuration |

Token savings must remain separated from local CPU savings. No threshold from
the project specification is treated as final; proposed stakeholder thresholds
remain proposals until approved with real benchmark evidence.

## Quality Limits

The authorized corpus contains text, columns, images, empty pages, complex
tables, and image-only input. Five text pages converted through local AnyDoc.
Three COMPLEX and three SCANNED pages failed in isolation because the current
default hybrid converter does not yet wire the hard extractor. This is a known
capability limit, not evidence that Kelpie quality is poor.

The judge is optional and remote. Its scores can reflect approved-model/style
bias, and missing judge or manual scores are reported as pending rather than
treated as zero. The current EDAG OCR baseline is intentionally out of scope,
so quality and token comparisons against it are not made. Evaluation uses the
permitted corpus, synthetic fixtures, and public/approved PDFs obtained without
confidential data.

## Recommendation

Keep **AnyDoc as the default local fast backend for TEXT pages** because the
Phase 0/1 evidence proves the optional local binding, page provenance seam, and
offline contract. Do **not** claim the complete hybrid pipeline is enterprise
cut over: hard-path integration, real Kelpie benchmark measurements, manual or
judge quality scores, and the current EDAG baseline remain open.

Retain pdfplumber as an explicit emergency backend/fallback. Do not delete it,
do not silently route hard pages to AnyDoc, and do not enable hosted Firecrawl
OCR.

## Next Evidence

1. Wire the Kelpie hard extractor into the hybrid assembly and run the permitted
   corpus with real page/image usage telemetry.
2. Run identical cold-cache AnyDoc, hybrid, full-vision, and pdfplumber
   comparisons on the approved corpus.
3. Add public/approved PDF fixtures when available, preserving an anonymised
   manifest and provenance.
4. Complete blind manual review and optional Kelpie judge review.

No production cleanup or destructive cutover is justified by the current
evidence.
