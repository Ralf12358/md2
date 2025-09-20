from aimport import *
import tempfile
import os
from pathlib import Path
from md2.conversion import md2pdf, html2pdf


def test_md2pdf_with_page_numbers():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test\n\nSome content.\n\n## Section\n\nMore content.")
        temp_md = f.name

    try:
        result = md2pdf([temp_md], page_numbers=True)
        assert len(result) == 1
        assert result[0].suffix == ".pdf"
        assert result[0].exists()
    finally:
        os.unlink(temp_md)
        if result[0].exists():
            os.unlink(result[0])


def test_md2pdf_without_page_numbers():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test\n\nSome content.\n\n## Section\n\nMore content.")
        temp_md = f.name

    try:
        result = md2pdf([temp_md], page_numbers=False)
        assert len(result) == 1
        assert result[0].suffix == ".pdf"
        assert result[0].exists()
    finally:
        os.unlink(temp_md)
        if result[0].exists():
            os.unlink(result[0])


def test_html2pdf_with_page_numbers():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(
            "<html><head><title>Test</title></head><body><h1>Test</h1><p>Content</p></body></html>"
        )
        temp_html = f.name

    try:
        result = html2pdf([temp_html], page_numbers=True)
        assert len(result) == 1
        assert result[0].suffix == ".pdf"
        assert result[0].exists()
    finally:
        os.unlink(temp_html)
        if result[0].exists():
            os.unlink(result[0])


def test_html2pdf_without_page_numbers():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(
            "<html><head><title>Test</title></head><body><h1>Test</h1><p>Content</p></body></html>"
        )
        temp_html = f.name

    try:
        result = html2pdf([temp_html], page_numbers=False)
        assert len(result) == 1
        assert result[0].suffix == ".pdf"
        assert result[0].exists()
    finally:
        os.unlink(temp_html)
        if result[0].exists():
            os.unlink(result[0])
