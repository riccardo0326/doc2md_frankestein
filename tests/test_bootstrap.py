import importlib
import subprocess
import sys


def test_placeholder_package_imports_without_heavy_adapters() -> None:
    module = importlib.import_module("doc2md")

    assert module.__version__ == "0.1.0"
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys, doc2md; "
                "assert not any(name in sys.modules for name in ('anydoc', 'docling', 'kelpie'))"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert probe.stderr == ""
