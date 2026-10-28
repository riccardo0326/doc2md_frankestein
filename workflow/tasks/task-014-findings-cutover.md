# task-014 - Produce findings and make the cutover decision

## What to build

Run the cold-cache comparison of pdfplumber, AnyDoc, hybrid AnyDoc plus Kelpie, full vision, and the current EDAG baseline when available. Produce a findings report with token, time, quality, robustness, and failure metrics, then record an explicit default-backend decision.

## Why

The migration should become the default only because evidence supports it, with a documented rollback if the quality or operational criteria are missed.

## Relevant files

Read before starting:

- `MIGRATION-PLAN.md` cutover decision and rollback sections
- `C:\Users\rp99480\dev\doc2md\PROJECT-SPEC.md` success criteria
- `src/doc2md/bench`
- `docs/corpus-results.md`
- benchmark run outputs

Create:

- `docs/FINDINGS.md`
- `docs/cutover-decision.md`

Modify:

- `docs/decisions.md`
- `workflow/ROADMAP.md`

## Steps

1. Run cold-cache comparisons using the same corpus and environment.
2. Verify every result has environment, version, and configuration metadata.
3. Compare Kelpie calls, token usage, time, quality, output size, and failures.
4. State which criteria pass, fail, or cannot be measured.
5. Record the default fast backend decision.
6. Record rollback configuration and unresolved risks.

## Acceptance criteria

- [x] Findings cite exact run directories and versions.
- [x] The current baseline is explicitly marked unavailable when absent.
- [x] Token savings are separated from local CPU savings.
- [x] Quality scores include manual/judge limitations.
- [x] The default backend decision is explicit: AnyDoc or pdfplumber.
- [x] Rollback remains possible through configuration.

## Edge cases to handle

- When the current baseline has no token telemetry: report time/quality comparison only.
- When a threshold is not approved by stakeholders: label it proposed, not final.
- When results disagree: report the disagreement rather than averaging it away.

## Definition of done

- [x] Findings and cutover decision are reviewable by the human.
- [x] Decisions are recorded.
- [x] No cleanup removes the fallback before approval.

## Status

completed

### Dev notes
Files created:
- `docs/FINDINGS.md`
- `docs/cutover-decision.md`

Files modified:
- `docs/decisions.md`
- `workflow/ROADMAP.md`
- `workflow/tasks/task-013-corpus-hardening.md`
- `workflow/tasks/task-014-findings-cutover.md`

Deviations from spec (if any):
- No real product cutover claim is made because baseline, Kelpie telemetry, and
  quality scores are unavailable. The decision is explicitly provisional.
- The cited cold-cache run is a deterministic fake-backed smoke run for schema
  and orchestration, not a quality benchmark.

Verification:
- Findings cite `bench_runs/20261028-103214/`, versions, corpus results, and
  rollback configuration.
- No confidential inputs, model responses, credentials, or token values were
  committed.

Suggestions for follow-up (do not act on these):
- Revisit this decision after hard-path wiring and approved benchmark evidence.
