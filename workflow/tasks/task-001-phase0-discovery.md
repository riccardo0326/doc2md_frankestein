# task-001 - Phase 0 migration discovery

## What to build

Produce the evidence and decisions required to safely replace the existing Python fast parser with an optional local AnyDoc Rust adapter. Do not add production feature code, modify the source `doc2md` workspace, call hosted Firecrawl OCR, or call Kelpie during this task.

## Why

The migration is only safe if the AnyDoc binding can process selected original pages on the target Windows/Python environment and if its output can satisfy the existing provenance and licensing constraints.

## Relevant files

Read before starting:

- `MIGRATION-PLAN.md` - target architecture and phase gates.
- `workflow/PROJECT.md` - migration constraints.
- `C:\Users\rp99480\dev\doc2md\PROJECT-SPEC.md` - functional and enterprise requirements.
- `C:\Users\rp99480\dev\doc2md\ARCHITECTURE.md` - current contracts and dependency rules.
- `C:\Users\rp99480\dev\doc2md\docs/research-anydoc.md` - existing AnyDoc primary-source research.
- `C:\Users\rp99480\dev\doc2md\docs/discovery.md` - existing Kelpie and environment evidence, if present.

Create:

- `docs/discovery.md` - redacted, reproducible Phase 0 findings.

Modify:

- `docs/decisions.md` - decisions made from evidence only.

## Steps

1. Record the source workspace path and its current Git commit without copying source files or confidential outputs.
2. Run the source workspace test, lint, and type-check commands and record pass/fail summaries.
3. Record Python version, operating system, CPU, memory, pip availability, and native wheel compatibility.
4. Install or inspect the permitted `firecrawl-anydoc` package in an isolated development environment only.
5. Record the exact AnyDoc Python import and `to_markdown_bytes` behavior for bytes input.
6. Verify that the local path makes no network request and does not enable hosted OCR.
7. Create a synthetic multi-page digital PDF and determine the permitted in-memory one-page slicing method.
8. Convert isolated pages through AnyDoc and record whether headings, columns, tables, ligatures, umlauts, blank pages, and malformed inputs produce usable Markdown.
9. Record how page slicing preserves or changes resources, page geometry, embedded images, and text encoding.
10. Audit the Python package, native Rust artifacts, and transitive Rust dependencies against the allowed license list.
11. Compare the AnyDoc page output with the current sidecar contract and decide whether one block per page is sufficient for the first adapter.
12. Record the proposed `anydoc` provenance value, schema version impact, cache-key fields, fallback behavior, and open risks.
13. Write `docs/discovery.md` with commands, versions, redacted outputs, evidence links, and unresolved blockers.
14. Stop and request human sign-off with the exact word `go` before creating a production adapter.

## Acceptance criteria

- [x] `docs/discovery.md` answers every step with evidence or marks it as blocked.
- [x] No production code was added.
- [x] No source files, confidential PDFs, credentials, model responses, or token values were copied.
- [x] The AnyDoc local path is proven separate from hosted Firecrawl OCR.
- [x] A page-slicing approach and its limitations are documented.
- [x] License findings cover native and transitive dependencies, not only the top-level MIT declaration.
- [x] The proposed provenance/schema change is explicit and reviewable.
- [x] Human sign-off is requested before Phase 1.

## Edge cases to handle

- When no compatible AnyDoc wheel exists: record the supported installation blocker; do not compile or provision artifacts on the enterprise PC.
- When a page cannot be sliced without changing semantics: record the limitation and evaluate a native Rust page-level seam before implementation.
- When AnyDoc produces Markdown but no block metadata: retain the one-block-per-page design for the spike; do not invent bounding boxes.
- When an input contains scanned pages: verify local failure behavior without enabling hosted OCR.

## Definition of done

- [x] Discovery is reproducible and redacted.
- [x] Decisions are recorded in `docs/decisions.md`.
- [x] No production migration task has started.
- [x] Human sign-off is pending or received explicitly.

## Status

completed

### Dev notes
Files created:
- `docs/discovery.md`
- `IMPORTANTE.md`

Files modified:
- `docs/decisions.md`
- `workflow/tasks/task-001-phase0-discovery.md`

Deviations from spec (if any):
- No production code was added.
- Kelpie and hosted Firecrawl OCR were not called, as required by this task.
- The human approved the Rust license and signed off Phase 0 with `go` on
  2026-10-27.

Suggestions for follow-up (do not act on these):
- Use the documented `pypdf` in-memory seam for the adapter spike.
- Pre-check blank/image-only pages before AnyDoc and preserve original page
  numbers outside the sliced PDF.
- Keep the authorized six-file sample corpus read-only and outside this repo.

Human sign-off: received. The human replied `go` on 2026-10-27.
