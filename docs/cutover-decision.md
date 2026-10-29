# Cutover Decision

**Date:** 2026-10-28  
**Decision:** provisional AnyDoc default for local `TEXT` fast extraction; no
complete enterprise hybrid cutover.

## Post-Trial Status — 2026-10-29

The public runtime now constructs the configured AnyDoc, Kelpie hard-page, and
image adapters, and the installed wheel resolves both prompt resources. Live
representative conversions verified image assets and records, hard-path
provenance, scanned-page exclusion, and byte-identical warm-cache document
outputs. The provisional `TEXT` AnyDoc default and explicit pdfplumber rollback
remain unchanged.

Performance remains an open quality concern for image-heavy documents: a
two-page document with 80 image candidates exceeded a short trial timeout with
normal descriptions, while explicit `--no-images` completed successfully. Real
Kelpie quality and broader performance thresholds still require a separate
approved review.

## Default

`fast.backend=anydoc` remains the default for pages classified `TEXT`. This is
an evidence-backed local parser decision, not a claim that the complete tiered
pipeline has passed quality or savings gates.

## Conditions Not Yet Met

- Current EDAG baseline is explicitly out of scope because its PDFs and
  invocation/telemetry contract are not supplied.
- Real Kelpie hard-page benchmark telemetry is not recorded in the smoke run.
- Manual and judge quality scores are pending.
- Authorized corpus COMPLEX/SCANNED pages remain isolated failures until hard
  extraction is wired into the hybrid assembly.
- Token savings and quality thresholds therefore cannot be evaluated.

## Rollback

Rollback remains configuration-level:

```toml
[fast]
backend = "pdfplumber"
fallback = "pdfplumber"
```

Keep Kelpie hard routing and the output schema unchanged. Preserve AnyDoc run
data for diagnosis. Do not remove the fallback before a later approved release.

## Evidence

- Cold-cache smoke: `bench_runs/20261028-103214/`
- Corpus report: `docs/corpus-results.md`
- Full offline suite: 53 passed, 2 skipped

This decision must be revisited after real Kelpie benchmark evidence and
completed quality review on permitted, synthetic, or public PDFs. It does not
require an EDAG baseline unless that scope is explicitly reopened.
