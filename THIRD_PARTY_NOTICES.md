# Third-Party Notices

This file records the direct dependency license basis for the approved package
extras. Full resolved Python output is generated with `pip-licenses`; the native
AnyDoc SBOM is recorded in `docs/discovery.md`.

| Package | Use | License |
|---|---|---|
| pydantic | common models | MIT |
| pdfplumber | inspection/signals | MIT |
| typer | CLI | MIT |
| firecrawl-anydoc | optional local parser | MIT |
| pypdf | optional page slicing | BSD-3-Clause |
| reportlab | optional synthetic fixtures | BSD |
| openai | optional Kelpie transport | Apache-2.0 |
| httpx | optional Kelpie HTTP client | BSD-3-Clause |
| pypdfium2 | optional page rendering | BSD-3-Clause / Apache-2.0 |
| pytest | development tests | MIT |
| Ruff | development lint | MIT |
| mypy | development type checking | MIT |
| pip-licenses | development license audit | MIT |

The `firecrawl-anydoc` native SBOM contains 118 Rust components. Its `anydoc`
and `pdf-inspector` components are MIT. `ryu` is consumed under its approved
Apache-2.0 option; see decision D007.
