# ROADMAP

Phase 0 is signed off. Tasks 002-014 are completed, task-015 is reviewed, and
image-context tasks 016-021 are completed. Post-trial corrective task-022 is
completed; tasks 023-026 are completed.

| Phase | Result | Status |
|---|---|---|
| 0 | Discovery, contracts, licenses, and page-slicing decision | `task-001` completed |
| 1 | Package bootstrap, output contract, AnyDoc adapter | `task-002`/`task-003`/`task-004` completed |
| 2 | Inspection, routing, hybrid conversion, Kelpie hard path | `task-005`/`task-006` completed; `task-007` complete pending review |
| 3 | Images, cache, metrics, and comparison pipelines | `task-008`/`task-009` completed; `task-010` complete pending review |
| 4 | Benchmark runner and quality review | `task-011` completed; `task-012` complete pending review |
| 5 | Corpus hardening and cutover evidence | `task-013` completed; `task-014` complete pending review |
| 6 | Packaging, notices, and release | `task-015` reviewed |
| 7 | Post-trial public runtime, packaging, ordering, determinism, and corpus gate | `task-022`-`task-026` completed |

## Execution order

Execute tasks strictly in numeric order. After a task passes its acceptance criteria, mark it completed, mark only the next task `ready`, and stop for human review when the task declares a gate.
