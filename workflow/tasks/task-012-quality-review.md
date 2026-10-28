# task-012 - Add quality review and judge support

## What to build

Implement deterministic stratified manual-review sheets, blind labels, unblinding maps, rubric validation, optional Kelpie judge calls, tolerant judge parsing, and report merging for the benchmark outputs.

## Why

Token savings are not sufficient if tables, reading order, special characters, or image descriptions become worse. Quality review provides the evidence for the cutover decision.

## Relevant files

Read before starting:

- `C:\Users\rp99480\dev\doc2md\ARCHITECTURE.md` section 7.4
- `bench/rubric.md` in the old repository
- `src/doc2md/bench/runner.py`
- `src/doc2md/vision/base.py`

Create:

- `src/doc2md/bench/review.py`
- `src/doc2md/bench/judge.py`
- `bench/rubric.md`
- `prompts/judge.v1.txt`
- `tests/test_quality_review.py`

Modify:

- `src/doc2md/bench/runner.py`
- `src/doc2md/cli.py`
- `docs/decisions.md`

## Steps

1. Write deterministic stratified sampling tests.
2. Implement blind labels and round-trippable unblinding.
3. Add rubric and review-sheet output.
4. Implement optional Kelpie judge invocation through the existing vision seam.
5. Parse malformed judge responses into structured errors.
6. Merge manual and judge scores with agreement and sample-size notes.

## Acceptance criteria

- [x] Sampling is stratified by page class and reproducible by seed.
- [x] Reviewers cannot see pipeline names in the blind sheet.
- [x] Unblinding round-trips exactly.
- [x] Malformed judge output never crashes the command.
- [x] Judge calls and cache behavior are recorded.
- [x] Reports state judge limitations and missing baseline data.

## Edge cases to handle

- When fewer pages exist than the requested sample: select all available pages without duplication.
- When a judge model is unavailable: produce manual-review output and a structured judge error.
- When manual scores are absent: render a report with an explicit pending state.

## Definition of done

- [x] Offline review tests pass with fake outputs.
- [x] Optional Kelpie judge test is safely skipped without configuration.
- [x] Ruff and mypy pass.
- [x] Golden report tests pass.

## Status

completed

### Dev notes
Files created:
- `src/doc2md/bench/review.py`
- `src/doc2md/bench/judge.py`
- `bench/rubric.md`
- `prompts/judge.v1.txt`
- `tests/test_quality_review.py`

Files modified:
- `src/doc2md/cli.py`
- `docs/decisions.md`
- `MIGRATION-PLAN.md`
- `workflow/ROADMAP.md`
- `workflow/tasks/task-011-benchmark-runner.md`
- `workflow/tasks/task-012-quality-review.md`

Deviations from spec (if any):
- The CLI judge command emits a structured unavailable error unless an approved
  judge backend is explicitly wired; no network call is implicit.
- Page image rendering is represented by the stored path field; review logic
  remains independent of confidential source documents.

Verification:
- Offline suite: `51 passed, 2 skipped`; Ruff and mypy pass.
- Stratified sampling, blind labels, unblinding, tolerant parsing, and pending
  report states are covered by deterministic tests.

Suggestions for follow-up (do not act on these):
- Fill manual scores and enable the approved judge only during quality review.
