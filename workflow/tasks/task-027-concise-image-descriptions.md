# task-027 - Bound image description verbosity

## What to build

Make the default embedded-image description concise and information-focused.
Update the versioned image prompt to preserve meaningful visual content while
excluding decorative inventory, use the existing image output-token setting with
a lower default of 384 tokens, and add offline tests for the prompt policy and
the separation from page transcription limits.

## Why

The project must preserve informative figures, but exhaustive descriptions add
output tokens and make image-heavy conversions slow. A bounded semantic summary
better matches the quality rubric and the PDF-to-Markdown token-saving goal.

## Relevant files

Read before starting:

- `workflow/PROJECT.md` - repository commands and conventions.
- `docs/enhancements/concise-image-descriptions/PLAN.md` - approved scope and
  non-goals.
- `src/doc2md/config.py` - image and page vision token defaults.
- `src/doc2md/prompts/describe_image.v1.txt` - current image prompt.
- `src/doc2md/prompts/transcribe_page.v1.txt` - page prompt and formatting style.
- `tests/test_prompt_resources.py` - packaged prompt contract.
- `src/doc2md/vision/kelpie.py` - prompt loading and output-token routing.

Create:

- `tests/test_image_description_budget.py` - offline assertions for prompt
  policy and separated image/page defaults.

Modify:

- `src/doc2md/prompts/describe_image.v1.txt` - concise semantic prompt.
- `src/doc2md/config.py` - lower only the default image output budget.
- `workflow/tasks/task-027-concise-image-descriptions.md` - completion notes.

## Steps

1. Add failing tests for the concise prompt requirements and token defaults.
2. Rewrite `describe_image.v1.txt` with explicit semantic priorities and a
   maximum of three concise sentences.
3. Change only `VisionConfig.max_tokens` from 800 to 384.
4. Run the focused tests and fix any contract mismatch.
5. Run the full test, lint, and type-check commands.
6. Update this task with the implementation and verification notes.

## Acceptance criteria

- [x] The prompt asks for semantic, information-bearing content.
- [x] The prompt preserves meaningful labels, numbers, chart/table content, and
  relationships without asking for exhaustive visual inventory.
- [x] The prompt explicitly excludes decorative detail unless meaningful.
- [x] The prompt asks for one compact response of at most three sentences.
- [x] Image descriptions default to 384 output tokens.
- [x] Page transcription still defaults to 1600 output tokens.
- [x] No `VisionBackend` fields, request shape, cache key, or `--no-images`
  behavior changes.

## Edge cases to handle

- When callers provide a custom `VisionConfig.max_tokens`, preserve that value.
- When page transcription is configured separately, do not apply the image budget
  to `transcribe_page`.
- When the prompt is loaded from the installed package, its contents must remain
  identical to the packaged resource.

## Do not touch

- `C:\Users\rp99480\dev\doc2md`
- `C:\Users\rp99480\dev\ai4tc_webapp`
- Confidential PDFs, model responses, credentials, or token values.

## Definition of done

- [x] `python -m pytest -q`
- [x] `python -m ruff check src tests`
- [x] `python -m mypy src`, or the known NumPy stub limitation is recorded.
- [x] All acceptance criteria checked.
- [x] No debug statements or generated artifacts.

## Status

dev-complete

### Dev notes

Files created:
- `docs/enhancements/concise-image-descriptions/PLAN.md`
- `tests/test_image_description_budget.py`

Files modified:
- `src/doc2md/prompts/describe_image.v1.txt`
- `src/doc2md/config.py`
- `workflow/ROADMAP.md`
- `workflow/tasks/task-027-concise-image-descriptions.md`

Deviations from spec (if any):
- The default `python -m mypy src` remains blocked by the installed NumPy stub
  using Python 3.12 `type` syntax; `python -m mypy --python-version 3.12 src`
  passes. This is the documented repository environment limitation.

Suggestions for follow-up (do not act on these):
- Run cold-cache image benchmarks with approved inputs before changing the 384
  token default again.
