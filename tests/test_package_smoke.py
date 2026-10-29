from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPROVED_TEMP = Path(r"C:\Users\rp99480\AppData\Local\Temp\opencode")


def _copy_packaging_project(destination: Path) -> None:
    shutil.copytree(ROOT / "src", destination / "src")
    shutil.copy2(ROOT / "README.md", destination / "README.md")
    shutil.copy2(ROOT / "pyproject.toml", destination / "pyproject.toml")


def test_wheel_smoke_resolves_workspace_package_and_prompt() -> None:
    with tempfile.TemporaryDirectory(dir=APPROVED_TEMP, prefix="doc2md-package-smoke-") as path:
        _run_wheel_smoke(Path(path))


def _run_wheel_smoke(tmp_path: Path) -> None:
    project = tmp_path / "project"
    wheel_dir = tmp_path / "wheels"
    venv_dir = tmp_path / "venv"
    project.mkdir()
    wheel_dir.mkdir()
    _copy_packaging_project(project)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            str(project),
            "--wheel-dir",
            str(wheel_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(wheel_dir.glob("doc2md-*.whl"))
    assert len(wheels) == 1
    with zipfile.ZipFile(wheels[0]) as archive:
        names = set(archive.namelist())
    assert "doc2md/prompts/describe_image.v1.txt" in names
    assert "doc2md/prompts/transcribe_page.v1.txt" in names
    model_artifact_suffixes = (".bin", ".onnx", ".pt", ".pth", ".safetensors")
    assert not any(name.lower().endswith(model_artifact_suffixes) for name in names)

    subprocess.run(
        [sys.executable, "-m", "venv", "--system-site-packages", str(venv_dir)],
        check=True,
        capture_output=True,
        text=True,
    )
    venv_python = venv_dir / "Scripts" / "python.exe"
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "--no-deps", str(wheels[0])],
        check=True,
        capture_output=True,
        text=True,
    )

    command = venv_dir / "Scripts" / "doc2md.exe"
    if not command.exists():
        command = venv_dir / "Scripts" / "doc2md"
    help_result = subprocess.run(
        [str(command), "--help"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Usage:" in help_result.stdout

    probe = subprocess.run(
        [
            str(venv_python),
            "-c",
            (
                "import doc2md; "
                "from doc2md.config import VisionConfig; "
                "from doc2md.vision.kelpie import KelpieVisionBackend; "
                "print(doc2md.__file__); "
                "print(KelpieVisionBackend(VisionConfig())._prompt('describe_image.v1'))"
            ),
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    resolved = Path(probe.stdout.splitlines()[0]).resolve()
    assert venv_dir in resolved.parents
    assert ROOT not in resolved.parents
    assert "Describe the visible content" in probe.stdout
