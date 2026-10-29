# Post-Trial User Issues

Reviewed: 2026-10-29

This record contains anonymized observations from the installed public-tool trial
against the exact read-only `unstructured-ingest-source` tree. Trial environments,
outputs, and reports were disposable and were removed after inspection.

## Observed Issues

### Global command resolution

The bare global `doc2md` command resolved a different checkout than this
workspace. The isolated installation resolved the intended wheel correctly.
Users must verify `doc2md.__file__` before running a corpus.

### Image-heavy latency

A two-page text document containing 80 embedded image candidates did not finish
within the 120-second trial timeout with normal image descriptions. The explicit
`--no-images` run completed successfully, recorded 80 image records, and made no
vision calls. This is a performance limitation of the current sequential public
image path, not a contract or data-safety failure.

### Corpus aggregate

Read-only inspection covered 44 PDFs and 1,208 pages: 1,179 `TEXT`, 22
`COMPLEX`, and 7 `SCANNED`. The public no-image aggregate completed with 29 hard
calls, two source/PDF-level failures, and two isolated failed pages. Image
description calls were intentionally disabled for this aggregate run.

## Verified Behavior

- A live `TEXT` trial described three embedded figures, wrote three assets, and
  preserved `i01`, `i02`, `i03` order.
- A live `COMPLEX` trial used hard transcription and separately described its
  embedded image.
- Live `SCANNED` pages used the hard path without duplicate image descriptions.
- Cold and warm live image-cache runs produced byte-identical Markdown and
  document sidecars; the warm run made no new calls.

## Boundaries

The trial used the existing Kelpie process and environment-only configuration.
No credentials, raw model responses, token values, corpus filenames, excerpts,
or PDF-derived output is retained in the repository. No local OCR, layout model,
vision model, or hosted Firecrawl OCR path was enabled.
