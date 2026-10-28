# ROADMAP

Phase 0 is signed off. Tasks 002-014 are completed and task-015 is complete
pending review; later tasks remain planned until the human reviews the preceding
gate.

| Phase | Result | Status |
|---|---|---|
| 0 | Discovery, contracts, licenses, and page-slicing decision | `task-001` completed |
| 1 | Package bootstrap, output contract, AnyDoc adapter | `task-002`/`task-003`/`task-004` completed |
| 2 | Inspection, routing, hybrid conversion, Kelpie hard path | `task-005`/`task-006` completed; `task-007` complete pending review |
| 3 | Images, cache, metrics, and comparison pipelines | `task-008`/`task-009` completed; `task-010` complete pending review |
| 4 | Benchmark runner and quality review | `task-011` completed; `task-012` complete pending review |
| 5 | Corpus hardening and cutover evidence | `task-013` completed; `task-014` complete pending review |
| 6 | Packaging, notices, and release | `task-015` complete pending review |

## Execution order

Execute tasks strictly in numeric order. After a task passes its acceptance criteria, mark it completed, mark only the next task `ready`, and stop for human review when the task declares a gate.
