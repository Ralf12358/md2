import subprocess
from pathlib import Path


def test_md2rebuild_help():
    venv_bin = Path(__file__).parent.parent.parent / ".venv" / "bin"
    cmd = [str(venv_bin / "md2rebuild"), "--help"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 1
    assert "Force rebuild" in result.stderr
    assert "Docker/Podman" in result.stderr


def test_md2rebuild_rejects_unknown_args():
    venv_bin = Path(__file__).parent.parent.parent / ".venv" / "bin"
    cmd = [str(venv_bin / "md2rebuild"), "--unknown"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 1
    assert "Unknown option" in result.stderr
