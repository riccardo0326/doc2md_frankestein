# task-011 - Implement the benchmark runner

## What to build

Implement a cold-cache benchmark runner that executes selected documents across selected pipelines and repetitions, writes isolated outputs, captures environment metadata, and produces the exact `results.csv` contract. Support a fake current-system adapter and an optional real baseline adapter without requiring it.

## Why

Performance claims must be reproducible across AnyDoc, pdfplumber, hybrid, full vision, and the current EDAG baseline when available.

## Relevant files

Read before starting:

- `C:\Users\rp99480\dev\doc2md\ARCHITECTURE.md` section 7
- `bench/suite.toml` and `bench/rubric.md` in the old repository
- `src/doc2md/api.py`
- `src/doc2md/models.py`

Create:

- `src/doc2md/bench/__init__.py`
- `src/doc2md/bench/suite.py`
- `src/doc2md/bench/pipelines.py`
- `src/doc2md/bench/runner.py`
- `src/doc2md/bench/baseline_current.py`
- `tests/test_benchmark.py`
- `bench/suite.toml`

Modify:

- `src/doc2md/cli.py`
- `docs/decisions.md`

## Steps

1. Write fixture CSV and suite-loader tests.
2. Implement suite validation and pipeline selection.
3. Implement isolated repetition directories and cold-cache setup.
4. Implement fake baseline behavior and optional external adapter seam.
5. Capture exact results columns and environment metadata.
6. Add deterministic report input fixtures.

## Acceptance criteria

- [x] Runner executes document/pipeline/repetition combinations.
- [x] Cold cache is truly isolated per benchmark run.
- [x] `results.csv` has the exact documented columns and order.
- [x] AnyDoc, Kelpie, cache, and failure metrics are represented.
- [x] Benchmark works without the current EDAG baseline.
- [x] Outputs do not copy confidential documents into Git.
- [x] CLI run command is deterministic except timestamps/run IDs.

## Edge cases to handle

- When the baseline command is unavailable: mark it skipped or unavailable, do not abort other pipelines.
- When one document/pipeline fails: record the error row and continue.
- When token usage is unavailable: leave the baseline field empty and explain it in the report.

## Definition of done

- [x] Benchmark unit tests pass offline with fake backends.
- [x] A two-document synthetic suite runs end to end.
- [x] Ruff and mypy pass.
- [x] Results schema is documented.

## Status

completed

### Dev notes
Files created:
- `src/doc2md/bench/__init__.py`
- `src/doc2md/bench/suite.py`
- `src/doc2md/bench/pipelines.py`
- `src/doc2md/bench/runner.py`
- `src/doc2md/bench/baseline_current.py`
- `tests/test_benchmark.py`
- `bench/suite.toml`

Files modified:
- `src/doc2md/cli.py`
- `docs/decisions.md`
- `MIGRATION-PLAN.md`
- `workflow/ROADMAP.md`
- `workflow/tasks/task-010-alternate-pipelines.md`
- `workflow/tasks/task-011-benchmark-runner.md`

Deviations from spec (if any):
- Baseline execution is represented by a protocol and optional fake adapter;
  no current EDAG command is assumed or invoked.
- The committed suite contains anonymised placeholder sample paths only; tests
  use temporary synthetic documents and never copy them into Git.

Verification:
- Offline suite: `47 passed, 2 skipped`; Ruff and mypy pass.
- Two-document, three-pipeline, two-repetition matrix passes with exact CSV
  schema and isolated cache directories.

Suggestions for follow-up (do not act on these):
- Add report/review generation only in the next quality-review task.
