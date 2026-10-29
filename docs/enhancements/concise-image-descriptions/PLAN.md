# Concise Image Descriptions Enhancement

## Objective

Reduce image-description output tokens while preserving the information that is
not available in the extracted PDF text. The default image prompt must produce
short, semantic descriptions instead of exhaustive visual inventories.

## Baseline

- `describe_image.v1.txt` asks for faithful visible content and information-
  bearing details, but does not explicitly suppress decorative detail or bound
  the response shape.
- `VisionConfig.max_tokens` is the image-description output budget and defaults
  to 800. Page transcription uses the separate `transcribe_max_tokens` budget.
- The quality rubric requires a useful and accurate figure description; it does
  not require exhaustive enumeration.
- Image-heavy documents already show latency risk when descriptions are enabled,
  while `run.json` records the actual per-call token usage.

## Design

1. Rewrite the versioned image prompt to prioritize semantic information:
   charts, tables, labels, numbers, components, and relationships.
2. Explicitly exclude decorative or redundant visual detail unless it carries
   meaning.
3. Ask for one compact paragraph of at most three sentences so the result fits
   the existing inline Markdown figure block.
4. Lower the default image output budget from 800 to 384 tokens. Keep the field
   configurable and leave the page-transcription budget unchanged.
5. Add offline contract tests for the prompt policy and the separated defaults.

## Non-goals

- No change to the `VisionBackend` request or response contract.
- No post-processing or hard truncation of model responses after a call.
- No removal of image descriptions or change to `--no-images` behavior.
- No image-type classifier, filename rule, page-specific rule, or model change.
- No claim of token savings without a benchmark using real telemetry.

## Acceptance Criteria

- Image descriptions request a concise semantic summary and preserve meaningful
  labels, values, table structure, and relationships.
- Decorative inventory language is explicitly discouraged by the packaged prompt.
- The default image budget is 384 output tokens and remains configurable.
- The page transcription default remains 1600 output tokens.
- Existing prompt packaging, image, rendering, cache, and provenance tests pass.
- The full offline test, lint, and type-check commands pass, subject to the
  repository's documented NumPy/mypy environment limitation.

## Measurement Follow-up

Run cold-cache comparisons on approved or synthetic image fixtures and compare
image output tokens, total tokens, figure usefulness, and failure/truncation
rates. Revisit the default budget only from that evidence.
