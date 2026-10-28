# task-017 - Integrate embedded images in TEXT pages

## Objective

Connect the image-stage seam to the tiered `PdfConverter` for pages classified
`TEXT`. After the text block is produced by AnyDoc, or by the explicitly
configured `pdfplumber` fallback, collect eligible embedded images, render and
filter them, describe them through the injected `VisionBackend`, save stable
assets when requested, attach `ImageRecord` values to the document, and place
figure blocks relative to the existing page blocks.

## Why

This is the direct fix for the documented bug: a text-bearing page must not be
reported as complete while its informative embedded figures disappear from
Markdown, provenance, sidecar JSON, usage, or cache accounting.

## Dependencies And Initial State

- Depends on `task-016`.
- Initial status: `planned`; it becomes `ready` only after `task-016` QA.

## Files To Read

- `docs/limitations.md` - the observed TEXT-page gap and required behavior.
- `docs/decisions.md` - D012, D014, and D015.
- `src/doc2md/converters/pdf/hybrid.py` - page loop and fallback seam.
- `src/doc2md/converters/pdf/images.py` - adapter result and placement rules.
- `src/doc2md/models.py` - `ConvertedDocument`, `PageResult`, and
  `ImageRecord`.
- `src/doc2md/render/markdown.py` and `src/doc2md/render/sidecar.py` - output
  contract.
- `src/doc2md/config.py` - image and fallback settings.
- `tests/test_hybrid_converter.py`, `tests/test_images.py`, and
  `tests/test_render.py` - existing expectations.

## Files To Create

- `tests/test_hybrid_images.py` - end-to-end fake-backed TEXT fixtures and
  assertions for Markdown, sidecar, and page provenance.
- `tests/fixtures/pdf_images.py` - extend the shared synthetic builder only if
  `task-016` did not already provide the needed fixture.

## Files To Modify

- `src/doc2md/converters/pdf/hybrid.py` - inject the image stage/backend,
  invoke it for TEXT pages, aggregate records/drafts, and place drafts without
  changing AnyDoc normalization.
- `src/doc2md/converters/pdf/images.py` - extend the canonical-record handoff
  so duplicates encountered on later pages reuse the first occurrence's path
  and description without a second vision call.
- `src/doc2md/models.py` - only if a strictly additive internal result field is
  required; preserve the existing serialized contract and method literals.
- `src/doc2md/render/sidecar.py` - only if required to serialize already-owned
  image records; do not add a second image envelope.
- `tests/test_hybrid_converter.py` - add regression assertions only where the
  existing mixed conversion contract is affected.

## Test-First Steps

1. Add a failing synthetic PDF test with a `TEXT` page containing extractable
   text and one embedded image; inject fake AnyDoc, fake renderer, and fake
   vision backend.
2. Assert the text block remains `provenance.source="anydoc"`, the figure block
   has the original page and image bounding box, and the figure follows the
   correct preceding block.
3. Assert the `ImageRecord` is in the document sidecar, the deterministic PNG
   is under `images/pNNNN-iNN.png`, and Markdown references that relative path.
4. Add a failing test where AnyDoc fails but configured `fallback="pdfplumber"`
   succeeds; assert the fallback warning/method and image processing both remain
   visible.
5. Add a failing test where the crop renderer fails; assert the page remains
   isolated and usable, the image record is failed, and no vision call occurs.
   The deterministic failure placeholder is hardened in `task-020`.
6. Add a failing cross-page duplicate test; assert the second occurrence keeps
   its page/bbox provenance while reusing the first canonical path/description.
7. Implement the converter wiring with one shared per-run deduplication map and
   canonical-record registry in deterministic page order.

## Acceptance Criteria

- [ ] Every eligible embedded image on a `TEXT` page reaches the existing
  filter/dedupe/description stage exactly once per canonical SHA-256.
- [ ] Figure blocks retain original page provenance, truthful `vision` source,
  stable IDs, and correct placement after preceding page content.
- [ ] `ConvertedDocument.images` and the JSON sidecar contain described,
  skipped, and failed image records as applicable.
- [ ] Output assets use stable relative paths and do not contain absolute
  workspace paths.
- [ ] A rendering or description failure does not fail the surrounding TEXT
  page or another page.
- [ ] A duplicate image on a later page reuses the first canonical asset and
  description while retaining its own occurrence record and figure provenance.
- [ ] The explicit `pdfplumber` fallback remains opt-in and is not used for
  image descriptions.
- [ ] `images.enabled=False` produces `vision_disabled` records with no backend
  call and does not silently discard eligible image context.

## Edge Cases

- When a TEXT page has no images, the existing AnyDoc-only output is unchanged.
- When the page has only filtered images, records explain the filter reason and
  no vision call is made.
- When AnyDoc fails and pdfplumber fallback is disabled, the page failure remains
  isolated; the converter must not make an image-only page successful.
- When output is in-memory only, Markdown must not point to an invented file;
  use the existing data/description behavior of the image stage.
- When multiple images share a digest across pages, only the canonical image is
  described while each occurrence retains its own provenance.

## Definition Of Done

- [ ] Failing-first TEXT integration tests pass offline with fake adapters.
- [ ] Existing hybrid, image, render, cache, and metrics tests remain green.
- [ ] `python -m pytest -q` passes.
- [ ] `python -m ruff check src tests` passes.
- [ ] `python -m mypy src` passes.
- [ ] No filename/page/document-specific branch or reserved data is added.

## Status

planned
