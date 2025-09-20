from aimport import *
from pathlib import Path
from .pdf_parser import find_toc_placeholders
from .pdf_editor import apply_toc_page_numbers


def should_add_toc_page_numbers(page_numbers_enabled: bool) -> bool:
    """Determine if TOC page numbers should be added"""
    return page_numbers_enabled


def has_toc_placeholders(pdf_path: Path) -> bool:
    """Check if PDF contains TOC placeholders"""
    placeholders = find_toc_placeholders(pdf_path)
    return len(placeholders) > 0


def postprocess_pdf_toc(pdf_path: Path, page_numbers_enabled: bool) -> Path:
    """Main entry point for TOC page number processing"""
    if not page_numbers_enabled:
        return pdf_path  # Return original PDF unchanged

    if not has_toc_placeholders(pdf_path):
        return pdf_path  # No TOC or no placeholders found

    return apply_toc_page_numbers(pdf_path)
