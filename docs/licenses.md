# License Audit

**Audit date:** 2026-10-28  
**Command:** `pip-licenses --fail-on "GPL;AGPL;LGPL;SSPL"`  
**Result:** `forbidden_matches: 0`

## Direct package basis

| Package | License | Scope |
|---|---|---|
| pydantic | MIT | runtime |
| pdfplumber | MIT | runtime |
| typer | MIT | runtime |
| firecrawl-anydoc | MIT | optional AnyDoc |
| pypdf | BSD-3-Clause | optional slicing |
| reportlab | BSD | optional synthetic fixtures |
| openai | Apache-2.0 | optional Kelpie |
| httpx | BSD-3-Clause | optional Kelpie |
| pypdfium2 | BSD-3-Clause / Apache-2.0 | optional rendering |
| pytest | MIT | development |
| Ruff | MIT | development |
| mypy | MIT | development |
| pip-licenses | MIT | development audit |

## Native AnyDoc

The resolved native SBOM is shipped inside the `firecrawl-anydoc` wheel and is
summarized in `docs/discovery.md`: 118 Rust components, with MIT `anydoc` and
`pdf-inspector`. `ryu 1.0.23` has `Apache-2.0 OR BSL-1.0`; this project uses the
human-approved Apache-2.0 option. No BSL exception is required.

## Boundary

License auditing does not authorize model downloads, hosted Firecrawl OCR, or
credential storage. Optional Kelpie traffic remains restricted to the approved
service contract and TLS-verified transport.
