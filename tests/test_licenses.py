from pathlib import Path


def test_license_report_has_no_forbidden_matches() -> None:
    report = Path("docs/licenses.md").read_text(encoding="utf-8").lower()

    assert "forbidden_matches: 0" in report
    assert "firecrawl-anydoc" in report
    assert "pypdf" in report
    assert "openai" in report


def test_license_documents_contain_no_secret_material() -> None:
    for path in (Path("docs/licenses.md"), Path("THIRD_PARTY_NOTICES.md")):
        content = path.read_text(encoding="utf-8")
        assert "BEGIN PRIVATE KEY" not in content
        assert "Bearer " not in content
        assert "KELPIE_PROXY_API_KEY=" not in content
