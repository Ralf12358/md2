from aimport import *
from pathlib import Path
import md2.conversion as conv
import md2.runtime as rt
import subprocess


class Recorder:
    def __init__(self):
        self.cmds = []

    def __call__(self, cmd, check=False, **k):
        self.cmds.append(cmd)

        class R:
            pass

        return R()


def test_md2html_basic(monkeypatch, tmp_path):
    f = tmp_path / "a.md"
    f.write_text("# A")
    rec = Recorder()
    monkeypatch.setattr(conv.subprocess, "run", rec)
    monkeypatch.setattr(rt, "ensure_image", lambda runtime, root: None)
    monkeypatch.setattr(rt, "get_container_runtime", lambda: "docker")
    out = conv.md2html([f])
    assert out[0].name == "a.html"
    assert rec.cmds[0][0] == "docker"


def test_md2pdf_basic(monkeypatch, tmp_path):
    f = tmp_path / "b.md"
    f.write_text("# B")
    rec = Recorder()
    monkeypatch.setattr(conv.subprocess, "run", rec)
    monkeypatch.setattr(rt, "ensure_image", lambda runtime, root: None)
    monkeypatch.setattr(rt, "get_container_runtime", lambda: "docker")
    conv.md2pdf([f])
    assert len(rec.cmds) == 1
    assert rec.cmds[0][0] == "docker"
    assert "sh" in rec.cmds[0]
    assert "-c" in rec.cmds[0]


def test_md2pdf_podman(monkeypatch, tmp_path):
    f = tmp_path / "c.md"
    f.write_text("# C")
    rec = Recorder()
    monkeypatch.setattr(conv.subprocess, "run", rec)
    monkeypatch.setattr(rt, "ensure_image", lambda runtime, root: None)
    monkeypatch.setattr(rt, "get_container_runtime", lambda: "podman")
    conv.md2pdf([f])
    assert rec.cmds[0][0] == "podman"
    assert "sh" in rec.cmds[0]
    assert "-c" in rec.cmds[0]


def test_toc_enabled_by_default(monkeypatch, tmp_path):
    f = tmp_path / "d.md"
    f.write_text("# D")
    rec = Recorder()
    monkeypatch.setattr(conv.subprocess, "run", rec)
    monkeypatch.setattr(rt, "ensure_image", lambda runtime, root: None)
    monkeypatch.setattr(rt, "get_container_runtime", lambda: "docker")
    conv.md2html([f])
    # Check that --toc is in the command
    assert "--toc" in rec.cmds[0]


def test_toc_can_be_disabled(monkeypatch, tmp_path):
    f = tmp_path / "e.md"
    f.write_text("# E")
    rec = Recorder()
    monkeypatch.setattr(conv.subprocess, "run", rec)
    monkeypatch.setattr(rt, "ensure_image", lambda runtime, root: None)
    monkeypatch.setattr(rt, "get_container_runtime", lambda: "docker")
    conv.md2html([f], markdown_flags=["--no-toc"])
    # Check that --toc is NOT in the command
    assert "--toc" not in rec.cmds[0]
    assert (
        "--no-toc" not in rec.cmds[0]
    )  # --no-toc is processed by our code, not passed to pandoc


def test_md2docx_basic(monkeypatch, tmp_path):
    f = tmp_path / "w.md"
    f.write_text("# W")
    rec = Recorder()
    monkeypatch.setattr(conv.subprocess, "run", rec)
    monkeypatch.setattr(rt, "ensure_image", lambda runtime, root: None)
    monkeypatch.setattr(rt, "get_container_runtime", lambda: "docker")
    out = conv.md2docx([f])
    assert out[0].name == "w.docx"
    assert rec.cmds[0][0] == "docker"
    assert "pandoc" in rec.cmds[0]


def test_md2docx_reference_doc(monkeypatch, tmp_path):
    f = tmp_path / "x.md"
    f.write_text("# X")
    ref = tmp_path / "ref.docx"
    ref.write_text("dummy")
    rec = Recorder()
    monkeypatch.setattr(conv.subprocess, "run", rec)
    monkeypatch.setattr(rt, "ensure_image", lambda runtime, root: None)
    monkeypatch.setattr(rt, "get_container_runtime", lambda: "docker")
    conv.md2docx([f], reference_doc=str(ref))
    cmd = rec.cmds[0]
    assert any("--reference-doc=" in a for a in cmd)
