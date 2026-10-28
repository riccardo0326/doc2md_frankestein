# doc2md-frankestein

Migration workspace for a tiered PDF-to-Markdown converter.

## Installation

Development/test installation contains the common contract and tooling; it is
not sufficient by itself for AnyDoc conversion:

```text
python -m pip install -e ".[dev]"
```

Optional local AnyDoc adapter and synthetic integration tools:

```text
python -m pip install -e ".[anydoc]"
```

For a normal local digital-PDF conversion, install both extras:

```text
python -m pip install -e ".[dev,anydoc]"
```

Optional Kelpie client and page rendering:

```text
python -m pip install -e ".[kelpie]"
```

AnyDoc uses the local `firecrawl-anydoc` Rust binding. Its hosted OCR option is
not used. Enterprise OCR and visual transcription are available only through
the approved Kelpie service; no OCR, layout, or LLM model files are installed
on the enterprise PC.

## Usage

Inspect routing without invoking an extractor:

```text
doc2md inspect input.pdf
doc2md inspect input.pdf --json
```

Convert with the tiered policy:

```text
doc2md convert input.pdf --out out
```

Comparison policies are explicit and share the same converter loop. They are
diagnostic modes: `full-vision` needs an injected/configured vision seam, while
`docling-only` needs its development hard extractor; neither silently installs
models or changes the default tiered route.

```text
doc2md convert input.pdf --pipeline full-vision --out out
doc2md convert input.pdf --pipeline docling-only --out out
```

## Try A Local PDF

From PowerShell, using a PDF already on your machine:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,anydoc]"

doc2md inspect "C:\path\to\document.pdf" --json
doc2md convert "C:\path\to\document.pdf" --out "C:\temp\doc2md-out" --no-cache
```

The Markdown, JSON sidecar, and `run.json` will be under
`C:\temp\doc2md-out\document\`. For a text-only digital PDF this uses local
AnyDoc and makes no hosted Firecrawl OCR call. Complex/scanned pages require
the approved Kelpie hard path; without it they remain isolated failures.

Run a benchmark and quality review:

```text
doc2md bench run --suite bench/suite.toml --out bench_runs
doc2md bench review-sheet bench_runs/<run-id>
doc2md bench report bench_runs/<run-id>
```

## Outputs

Conversion writes `<out>/<stem>/` containing Markdown, a provenance-rich JSON
sidecar, and `run.json`. Blocks retain original 1-based pages and a truthful
method (`anydoc`, `pdfplumber`, `vision`, or `docling`). Cache entries are
content-addressed JSON and can be disabled with `--no-cache`.

## Enterprise Boundary

- AnyDoc is local-only for digital `TEXT` pages.
- `COMPLEX` and `SCANNED` pages use the Kelpie hard-path seam; without it, the
  affected page fails in isolation.
- Firecrawl hosted OCR is never enabled implicitly.
- TLS verification remains enabled for Kelpie traffic.
- Credentials are environment variables only and never belong in this repo.
- Confidential PDFs and outputs stay outside Git.

## Cutover

AnyDoc is the provisional local fast backend for `TEXT` pages. The complete
enterprise hybrid cutover remains pending real Kelpie hard-path measurements and
manual/judge quality review. The current EDAG baseline is explicitly out of
scope because its PDFs and invocation/telemetry contract were not supplied.

Rollback is configuration-level: select `fast.backend=pdfplumber` and retain
the explicit fallback. See `docs/FINDINGS.md` and `docs/cutover-decision.md`.

## Development

```text
python -m pytest -q
python -m ruff check src tests
python -m mypy src
pip-licenses --fail-on "GPL;AGPL;LGPL;SSPL"
python -m pip wheel --no-deps . --wheel-dir dist
```

See `MIGRATION-PLAN.md` and `workflow/PROJECT.md` before changing architecture
or dependencies.
