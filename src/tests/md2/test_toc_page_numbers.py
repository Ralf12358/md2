from aimport import *
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from md2.pdf_parser import (
    extract_heading_pages,
    find_toc_placeholders,
    extract_toc_structure,
)
from md2.pdf_editor import apply_toc_page_numbers
from md2.toc_postprocess import postprocess_pdf_toc, has_toc_placeholders
from md2.html_postprocess import add_toc_page_number_placeholders


def test_pdf_parser_with_sample_data():
    """Test PDF parsing with mock data"""
    with patch("md2.pdf_parser.fitz") as mock_fitz:
        # Mock PDF document
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz.open.return_value = mock_doc

        # Mock search results for placeholders
        mock_rect = MagicMock()
        mock_rect.x0, mock_rect.y0, mock_rect.x1, mock_rect.y1 = 100, 200, 120, 220
        mock_page.search_for.return_value = [mock_rect]
        mock_page.get_textbox.return_value = "P#01"

        # Test find_toc_placeholders
        placeholders = find_toc_placeholders(Path("dummy.pdf"))
        assert len(placeholders) > 0
        assert placeholders[0][0] == "P#01"


def test_html_postprocess():
    """Test HTML post-processing to add TOC placeholders"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        html_content = """<html>
<body>
<nav id="TOC">
<ul>
<li><a href="#section-1" id="toc-section-1">Section 1</a></li>
<li><a href="#section-2" id="toc-section-2">Section 2</a></li>
</ul>
</nav>
</body>
</html>"""
        f.write(html_content)
        f.flush()

        html_path = Path(f.name)

        # Test with page numbers enabled
        add_toc_page_number_placeholders(html_path, True)

        with open(html_path, "r") as result_f:
            result = result_f.read()

        assert 'class="toc-page-numbers"' in result
        assert 'data-toc-placeholder="P#0001"' in result
        assert 'data-toc-placeholder="P#0002"' in result

        # Clean up
        html_path.unlink()


def test_html_postprocess_disabled():
    """Test HTML post-processing when page numbers are disabled"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        html_content = """<html>
<body>
<nav id="TOC">
<ul>
<li><a href="#section-1" id="toc-section-1">Section 1</a></li>
</ul>
</nav>
</body>
</html>"""
        f.write(html_content)
        f.flush()

        html_path = Path(f.name)
        original_content = html_content

        # Test with page numbers disabled
        add_toc_page_number_placeholders(html_path, False)

        with open(html_path, "r") as result_f:
            result = result_f.read()

        # Should be unchanged
        assert result == original_content

        # Clean up
        html_path.unlink()


def test_postprocess_pdf_toc_disabled():
    """Test that TOC post-processing is skipped when disabled"""
    dummy_path = Path("dummy.pdf")

    # Should return original path when disabled
    result = postprocess_pdf_toc(dummy_path, False)
    assert result == dummy_path


def test_has_toc_placeholders():
    """Test detection of TOC placeholders in PDF"""
    with patch("md2.toc_postprocess.find_toc_placeholders") as mock_find:
        dummy_path = Path("dummy.pdf")

        # Test with placeholders
        mock_find.return_value = [("P#01", 100, 200, 0)]
        assert has_toc_placeholders(dummy_path) == True

        # Test without placeholders
        mock_find.return_value = []
        assert has_toc_placeholders(dummy_path) == False


def test_extract_toc_structure_parsing():
    """Test TOC structure extraction logic"""
    with patch("md2.pdf_parser.fitz") as mock_fitz:
        # Mock PDF document
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz.open.return_value = mock_doc

        # Mock page text that matches our expected pattern
        mock_page.get_text.return_value = """Table of Contents
1
P#0001
Section 1
2
P#0002
Section 2"""

        # Mock find_toc_placeholders to return placeholders on page 0
        with patch("md2.pdf_parser.find_toc_placeholders") as mock_find_placeholders:
            mock_find_placeholders.return_value = [
                ("P#0001", 100, 200, 0),
                ("P#0002", 100, 220, 0),
            ]

            # Mock extract_heading_pages to return headings
            with patch("md2.pdf_parser.extract_heading_pages") as mock_extract_headings:
                mock_extract_headings.return_value = {"Section 1": 2, "Section 2": 3}

                result = extract_toc_structure(Path("dummy.pdf"))

                assert len(result) == 2
                assert result[0]["placeholder"] == "P#0001"
                assert result[0]["heading"] == "1 Section 1"
                assert result[0]["page"] == 2
                assert result[1]["placeholder"] == "P#0002"
                assert result[1]["heading"] == "2 Section 2"
                assert result[1]["page"] == 3
