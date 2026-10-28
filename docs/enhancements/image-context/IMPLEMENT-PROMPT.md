# Operational Prompt: Image Context Integration

You are implementing the `image-context` enhancement in
`C:\Users\rp99480\dev\doc2md_frankestein`.

## Non-Negotiable Rules

1. Read `AGENTS.md`, `MIGRATION-PLAN.md`, `workflow/PROJECT.md`,
   `docs/enhancements/image-context/PLAN.md`, and the current task file before
   doing anything else in a task.
2. Work only on branch `enhancement/image-context-integration`.
3. Treat `C:\Users\rp99480\dev\doc2md` and
   `C:\Users\rp99480\dev\ai4tc_webapp` as read-only references. Do not copy
   their files or content.
4. The current task file is the source of truth. Do not start a task whose
   status is not `ready`, and do not invent tasks outside `task-016` through
   `task-021`. Since `task-015` is currently pending review, first verify that
   its review gate has been accepted. If it has not, stop with that blocker. If
   it has, mark only `task-016` `ready` and begin; no human confirmation is
   requested between enhancement tasks.
5. Do not implement the next task early. Keep each change limited to the
   current task's objective, files, acceptance criteria, and Definition of
   Done.
6. Use tests first. Write a failing test or contract assertion before the
   production change, then implement the smallest general fix.
7. Preserve the discovered `VisionBackend` and Kelpie contract. Use only
   `docs/discovery.md`, `docs/kelpie-example.md` when it exists, and the
   already documented reference implementation. Never invent request fields,
   response fields, retries, credentials, model values, or token behavior.
8. Keep the `pdfplumber` fallback explicit and opt-in. Never turn a rendering,
   AnyDoc, or Kelpie failure into hosted Firecrawl OCR or a local model path.
9. Never add a branch based on a filename, document name, image name, page
   number, or corpus-specific content.
10. Keep PDFs, rendered pages, Markdown, JSON output, model responses,
    credentials, environment values, and token values out of Git. Synthetic
    fixtures and fake backends are the default.

## Task Loop

Execute these tasks strictly in order:

1. `workflow/tasks/task-016-image-stage-seam.md`
2. `workflow/tasks/task-017-text-image-assembly.md`
3. `workflow/tasks/task-018-complex-scanned-routing.md`
4. `workflow/tasks/task-019-image-cache-metrics-sidecars.md`
5. `workflow/tasks/task-020-image-robustness-determinism.md`
6. `workflow/tasks/task-021-kelpie-corpus-regression.md`

At the beginning of the run, verify the branch and repository state. If the
branch is wrong, the worktree has a conflicting change in a file required by
the current task, or a real prerequisite is missing, stop and report the
blocker. Do not discard user changes and do not use destructive Git commands.

For each task:

1. Read the task file completely and re-check its `Status` is `ready`.
2. Read every file listed under `Files To Read` before editing.
3. Update the task's `Status` to `in_progress` only when starting that task.
4. Add the failing test or assertion described by `Test-First Steps`.
5. Run the narrowest relevant test and confirm it fails for the intended reason.
6. Implement only the current task's smallest general change.
7. Run the narrow test again, then run all required checks from the workspace
   root:

   ```text
   python -m pytest -q
   python -m ruff check src tests
   python -m mypy src
   ```

8. Run optional AnyDoc/Kelpie integration tests only when their optional
   dependency and approved environment are available. Without them, require
   safe, explicit skips and continue offline QA.
9. Perform an automatic AI review of the current diff against the task file.
   The review must check acceptance criteria, edge cases, test-first evidence,
   provenance, cache/usage/latency accounting, fallback boundaries, contract
   fidelity, and secret/data safety. It must also check that no future task was
   implemented.
10. If QA or review finds a defect, fix it within the current task and repeat
    the complete checks. If a real blocker cannot be resolved without changing
    scope or inventing a contract, create a concise blocked report beside the
    task, leave the task `in_progress`, and stop.
11. Only after tests, Ruff, mypy, optional-test handling, and AI review pass,
    mark the current task `completed` and record verification notes in that
    task file.
12. Mark only the next task `ready`. Leave every later task `planned` and then
    proceed automatically to the next task without asking for human
    confirmation.

## Required Review Questions After Every Task

- Does the implementation process `TEXT` images without losing text blocks or
  original page provenance?
- Does it keep `COMPLEX` hard extraction authoritative while recording only
  separately proven embedded figures?
- Are full-page `SCANNED` images excluded from `describe_image()` and from
  duplicate `ImageRecord` accounting?
- Are crop, filter, area, aspect-ratio, SHA-256, deterministic save, placement,
  and render-failure behaviors general and configuration-driven?
- Do image records, figure blocks, usage, latency, cache hits/misses, and
  `run.json` agree with actual calls?
- Does disabled vision produce explicit `vision_disabled` behavior without a
  backend call?
- Does a single bad image or page remain isolated?
- Is the `pdfplumber` fallback still explicit and limited to AnyDoc text
  extraction?
- Were fake offline tests used, with optional Kelpie tests guarded safely?
- Did the diff avoid secrets, PDFs, model responses, token values, and
  document-specific rules?

## Final Gate

After `task-021` is completed and its AI review passes:

1. Run the full test, Ruff, mypy, and optional-test checks one final time.
2. Inspect `git status`, `git diff`, `git log --oneline -10`, and the complete
   list of commits and changed files.
3. Verify the diff contains only the approved image-context implementation,
   its tests, task status/verification notes, and explicitly required decision
   or limitation updates. Confirm no confidential data or secrets are present.
4. Confirm all six tasks are `completed` and no task outside `task-016` through
   `task-021` was started.
5. Create one final concise commit only after all tasks and QA pass. Do not
   commit at the beginning or mid-way through the task sequence.
6. Report the final commit hash, tests, optional skips, corpus verification
   status, and any residual blockers.

If any final check fails, do not commit and stop with the exact blocker.
