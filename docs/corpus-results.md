# Corpus Hardening Results

**Date:** 2026-10-28  
**Scope:** synthetic regression matrix plus the six user-authorized PDFs under
`C:\Users\rp99480\dev\doc2md\samples\unstructured-demo`.  
**Safety:** PDFs were read-only inputs outside this repository. No PDF bytes,
Markdown output, model response, credential, or token value was committed.

## Synthetic Matrix

Command:

```text
python -m pytest -q
```

Result: **53 passed, 2 skipped**. The skips are the optional AnyDoc and Kelpie
integration tests without their respective environments. Ruff and mypy also
pass.

The regression coverage includes text, columns, tables, figures, ligatures,
German text, blank pages, scanned pages, malformed/empty adapter responses,
page provenance, image deduplication, hard-path isolation, cache behavior, and
all comparison pipeline policies.

## Authorized Corpus

The corpus was inspected and converted in a temporary environment with
`pdfplumber` signals, local AnyDoc where available, and a socket guard that
failed any network connection. Outputs were written outside the repository and
removed after the summary was captured.

| Anonymised input | Pages | TEXT | COMPLEX | SCANNED | OK | Failed | Methods |
|---|---:|---:|---:|---:|---:|---:|---|
| `unstructured-demo-01` | 1 | 0 | 1 | 0 | 0 | 1 | none |
| `unstructured-demo-02` | 1 | 1 | 0 | 0 | 1 | 0 | anydoc |
| `unstructured-demo-03` | 4 | 2 | 0 | 2 | 2 | 2 | anydoc |
| `unstructured-demo-04` | 2 | 0 | 2 | 0 | 0 | 2 | none |
| `unstructured-demo-05` | 2 | 2 | 0 | 0 | 2 | 0 | anydoc |
| `unstructured-demo-06` | 1 | 0 | 0 | 1 | 0 | 1 | none |
| **Total** | **11** | **5** | **3** | **3** | **5** | **6** | |

The 5 TEXT pages converted locally through AnyDoc. The 3 COMPLEX and 3 SCANNED
pages remained isolated failures because the current hybrid slice does not yet
wire a hard extractor into its default converter instance. This is an explicit
capability limitation, not a filename/page-specific rule. The dedicated
Kelpie hard adapter and fake tests are green, but its integration into the
hybrid default is outside this corpus-hardening task's safe scope.

One input was image-based and raised the documented OCR/hard-path boundary;
blank pages were also isolated. No hosted Firecrawl OCR or Kelpie call was made
by this corpus run.

## Findings

- No new general parser defect was demonstrated by the permitted corpus run.
- The dominant limitation is hard-path wiring availability for COMPLEX/SCANNED
  pages, already represented by explicit page failures and regression tests.
- Text-bearing image pages and multi-column text pages retained AnyDoc method
  provenance and original page numbers in the successful cases.
- No document-specific, filename-specific, or page-specific branch was added.

## Reproduction Notes

Use the six files from the authorized external path, not copies in this repo.
Run the full offline suite first, then run `inspect_pdf` and `convert` against
each permitted input with `Config(cache=CacheConfig(enabled=False))`. Keep the
output directory temporary and preserve only aggregate counts like this report.
