import io
import socket

import pytest

from doc2md.converters.pdf.anydoc import AnyDocFastExtractor

pytestmark = pytest.mark.anydoc
anydoc = pytest.importorskip("anydoc")
pytest.importorskip("pypdf")
reportlab_canvas = pytest.importorskip("reportlab.pdfgen.canvas")
from reportlab.lib.pagesizes import letter  # noqa: E402


def synthetic_pdf() -> bytes:
    output = io.BytesIO()
    canvas = reportlab_canvas.Canvas(output, pagesize=letter)
    canvas.drawString(72, 720, "Synthetic AnyDoc page")
    canvas.showPage()
    canvas.save()
    return output.getvalue()


def test_real_local_conversion_preserves_page_and_avoids_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_network(self: socket.socket, address: object) -> None:
        raise AssertionError(f"network attempted: {address!r}")

    monkeypatch.setattr(socket.socket, "connect", fail_network)

    block = AnyDocFastExtractor().extract(synthetic_pdf(), page=4)

    assert "Synthetic AnyDoc page" in block.markdown
    assert block.block_id == "p0004-b001"
    assert block.provenance.page == 4
    assert block.provenance.source == "anydoc"
