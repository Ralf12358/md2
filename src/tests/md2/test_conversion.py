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
    
    # Mock the html file operations
    def mock_open(path, mode="r", **kwargs):
        from io import StringIO
        return StringIO("<html><body>Mock</body></html>")
    
    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr("md2.html_postprocess.add_toc_page_number_placeholders", lambda path, enabled: None)
    monkeypatch.setattr("md2.toc_postprocess.postprocess_pdf_toc", lambda path, enabled: path)
    
    conv.md2pdf([f])
    assert len(rec.cmds) == 2  # Now calls md2html then html2pdf
    assert rec.cmds[0][0] == "docker"  # First call (md2html)
    assert rec.cmds[1][0] == "docker"  # Second call (html2pdf)


def test_md2pdf_podman(monkeypatch, tmp_path):
    f = tmp_path / "c.md"
    f.write_text("# C")
    rec = Recorder()
    monkeypatch.setattr(conv.subprocess, "run", rec)
    monkeypatch.setattr(rt, "ensure_image", lambda runtime, root: None)
    monkeypatch.setattr(rt, "get_container_runtime", lambda: "podman")
    
    # Mock the html file operations
    def mock_open(path, mode="r", **kwargs):
        from io import StringIO
        return StringIO("<html><body>Mock</body></html>")
    
    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr("md2.html_postprocess.add_toc_page_number_placeholders", lambda path, enabled: None)
    monkeypatch.setattr("md2.toc_postprocess.postprocess_pdf_toc", lambda path, enabled: path)
    
    conv.md2pdf([f])
    assert rec.cmds[0][0] == "podman"  # First call should be podman
    assert rec.cmds[1][0] == "podman"  # Second call should be podman


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


def test_temp_files_use_unique_names(monkeypatch, tmp_path):
    # Test that temporary files for multiple H1s use unique names instead of tempfile
    f = tmp_path / "multi_h1.md"
    f.write_text("# First\n\n# Second\n\nContent")
    rec = Recorder()
    monkeypatch.setattr(conv.subprocess, "run", rec)
    monkeypatch.setattr(rt, "ensure_image", lambda runtime, root: None)
    monkeypatch.setattr(rt, "get_container_runtime", lambda: "docker")
    
    # Mock uuid to return predictable values
    import uuid
    monkeypatch.setattr(uuid, "uuid4", lambda: type('obj', (object,), {"hex": "abcd1234" * 4})())
    
    conv.md2html([f])
    
    # Check that container path uses the new temp file pattern
    cmd = rec.cmds[0]
    container_script_args = None
    for i, arg in enumerate(cmd):
        if arg == "bash" and i + 1 < len(cmd) and cmd[i + 1].endswith("md2html.sh"):
            container_script_args = cmd[i + 2:]
            break
    
    assert container_script_args is not None
    assert container_script_args[0] == "/work/tmp_abcd1234.md"


def test_html2pdf_temp_pdf_with_page_numbers(monkeypatch, tmp_path):
    # Test that page numbers enabled creates temp PDF first
    f = tmp_path / "test.html"
    f.write_text("<html><body><h1>Test</h1></body></html>")
    rec = Recorder()
    monkeypatch.setattr(conv.subprocess, "run", rec)
    monkeypatch.setattr(rt, "ensure_image", lambda runtime, root: None)
    monkeypatch.setattr(rt, "get_container_runtime", lambda: "docker")
    
    # Mock uuid and postprocess function
    import uuid
    monkeypatch.setattr(uuid, "uuid4", lambda: type('obj', (object,), {"hex": "efgh5678" * 4})())
    
    def mock_postprocess(pdf_path, page_numbers_enabled):
        # Mock that creates and returns the final PDF path
        if page_numbers_enabled:
            # Simulate processing: temp PDF becomes final PDF
            final_pdf = pdf_path.with_name("test.pdf")
            if pdf_path != final_pdf:
                # Simulate moving temp to final
                final_pdf.write_text("processed pdf content")
                if pdf_path.exists():
                    pdf_path.unlink()
            return final_pdf
        return pdf_path
    
    monkeypatch.setattr("md2.toc_postprocess.postprocess_pdf_toc", mock_postprocess)
    
    result = conv.html2pdf([f], page_numbers=True)
    
    # Check that temp PDF name was used in container command
    cmd = rec.cmds[0]
    expected_temp_pdf = "tmp_efgh5678.pdf"
    assert f"/work/{expected_temp_pdf}" in cmd
    
    # Final result should be the expected PDF name
    assert result[0].name == "test.pdf"


def test_html2pdf_no_temp_pdf_without_page_numbers(monkeypatch, tmp_path):
    # Test that page numbers disabled uses direct PDF name
    f = tmp_path / "test.html"
    f.write_text("<html><body><h1>Test</h1></body></html>")
    rec = Recorder()
    monkeypatch.setattr(conv.subprocess, "run", rec)
    monkeypatch.setattr(rt, "ensure_image", lambda runtime, root: None)
    monkeypatch.setattr(rt, "get_container_runtime", lambda: "docker")
    
    def mock_postprocess(pdf_path, page_numbers_enabled):
        return pdf_path
    
    monkeypatch.setattr("md2.toc_postprocess.postprocess_pdf_toc", mock_postprocess)
    
    result = conv.html2pdf([f], page_numbers=False)
    
    # Check that final PDF name was used directly in container command
    cmd = rec.cmds[0]
    assert "/work/test.pdf" in cmd
    
    # Final result should be the expected PDF name
    assert result[0].name == "test.pdf"
