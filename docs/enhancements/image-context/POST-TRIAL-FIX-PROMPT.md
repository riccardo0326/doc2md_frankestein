# Operational Prompt: Post-Trial Image-Context Fix Loop

You are implementing the post-trial corrective loop in
`C:\Users\rp99480\dev\doc2md_frankestein`.

## Scope

Execute these tasks strictly in order:

1. `workflow/tasks/task-022-public-runtime-image-wiring.md`
2. `workflow/tasks/task-023-package-prompts-and-smoke.md`
3. `workflow/tasks/task-024-image-placement-order.md`
4. `workflow/tasks/task-025-warm-cache-determinism.md`
5. `workflow/tasks/task-026-real-user-trial-regression.md`

## Non-negotiable rules

1. Read `AGENTS.md`, `MIGRATION-PLAN.md`, `workflow/PROJECT.md`,
   `workflow/STRATEGY.md`, `workflow/ROADMAP.md`, this prompt, and the current
   task file before editing.
2. Work only on `enhancement/image-context-integration`.
3. Treat `C:\Users\rp99480\dev\doc2md` and
   `C:\Users\rp99480\dev\ai4tc_webapp` as read-only.
4. The current task file is the source of truth. Start only a task whose status
   is `ready`; mark only the current task `in_progress`; leave later tasks
   `planned` until their dependency gate passes.
5. Do not implement a later task early. Keep every change within the current
   task's files, objective, acceptance criteria, and Definition of Done.
6. Use tests first: add a failing offline test, run the narrow test and confirm
   the intended failure, then make the smallest general production change.
7. Preserve the discovered `VisionBackend` and Kelpie contract. Do not invent
   request/response fields, retries, credentials, model values, token formulas,
   or environment aliases.
8. Keep pdfplumber fallback explicit and opt-in. Never turn AnyDoc, rendering,
   or Kelpie failure into hosted Firecrawl OCR or a local model path.
9. Never add filename-, document-, image-name-, page-number-, or corpus-specific
   branches.
10. Keep PDFs, rendered pages, Markdown, JSON, model responses, credentials,
    environment values, and token values out of Git. Use synthetic fixtures and
    fake backends for automated tests.
11. Put disposable environments, wheel files, trial outputs, and corpus reports
    under `C:\Users\rp99480\AppData\Local\Temp\opencode` only. Remove any
    packaging `build/` artifact created in the workspace by the loop.
12. Do not commit, amend, push, or create a PR. The user did not request Git
    history changes.

## Trial findings to fix

- Normal public CLI/API conversion did not construct `ImageStage`; embedded
  image output had no `ImageRecord` or figure blocks.
- Normal public conversion had no configured per-page Kelpie hard adapter, so
  COMPLEX and SCANNED pages failed when no custom converter was injected.
- The installed wheel omitted `prompts/describe_image.v1.txt`, causing real
  Kelpie image calls to fail before the request.
- Three same-band figures were emitted in reverse order around the AnyDoc text.
- Warm-cache Markdown matched cold output, but document sidecars differed due to
  operational `cache_hit:anydoc` warnings.
- Bare global `doc2md` resolved another checkout; isolated installation must
  prove the package and entry point resolve this workspace.

## Per-task loop

For each task:

1. Read the complete task file and verify `Status: ready`.
2. Read every file listed under `Read before starting`.
3. Mark the task `in_progress`.
4. Add the failing test/assertion described by `Test-First Steps`.
5. Run the narrowest relevant test and confirm the failure reason.
6. Implement only the current task.
7. Run the narrow test, then from the workspace root run:

   ```text
   python -m pytest -q
   python -m ruff check src tests
   python -m mypy src
   ```

8. If the known workstation NumPy-stub Python-target error affects
   `python -m mypy src`, run `python -m mypy --python-version 3.12 src`, record
   both results, and do not hide unrelated type errors.
9. Run optional AnyDoc/Kelpie/corpus checks only with their documented
   dependencies and guards. Real corpus inputs are read in place and outputs
   go only to the approved temporary directory.
10. Review the diff against the task for contract fidelity, provenance,
    fallback boundaries, cache/usage/latency accounting, deterministic output,
    and data safety.
11. If a defect is within scope, fix it and repeat all checks. If resolving it
    requires an invented contract or scope change, create a concise
    `workflow/tasks/task-NNN-BLOCKED.md`, leave the task `in_progress`, and stop.
12. After QA passes, mark the task `completed`, write verification notes, mark
    only the next task `ready`, and continue without asking for confirmation.

## Final gate

After task-026:

1. Run the full offline suite, Ruff, mypy, and guarded optional checks once more.
2. Verify the installed wheel smoke and public CLI results from the temporary
   trial area without copying outputs into the repository.
3. Inspect `git status` and the complete diff. Remove only trial-generated
   artifacts created by this loop; never revert user changes.
4. Confirm tasks 022-026 are `completed`, no later task was started early, and
   no source PDF, output, response, credential, or token is tracked.
5. Report the public CLI result, Kelpie/corpus pass or skip state, remaining
   defects, and exact verification commands. Do not commit.
