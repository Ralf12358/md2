from aimport import *
import re
from pathlib import Path
from typing import Optional


def add_toc_page_number_placeholders(
    html_path: Path, page_numbers_enabled: bool
) -> None:
    """Add TOC page number placeholders when page numbers are enabled"""
    if not page_numbers_enabled:
        return

    try:
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check if TOC exists
        if 'id="TOC"' not in content:
            return

        # Add body class for page numbers
        content = re.sub(
            r"<body([^>]*)>", r'<body\1 class="toc-page-numbers">', content
        )

        # Add placeholder attributes to TOC links
        toc_counter = 1

        def add_placeholder(match):
            nonlocal toc_counter
            href = match.group(1)
            toc_id = match.group(2)
            inner_text = match.group(3)

            placeholder = f"P#{toc_counter:04d}"
            toc_counter += 1

            return f'<a href="{href}" id="{toc_id}" data-toc-placeholder="{placeholder}">{inner_text}</a>'

        # Match TOC links and add placeholders
        content = re.sub(
            r'<a href="(#[^"]*)" id="(toc-[^"]*)"[^>]*>([^<]*)</a>',
            add_placeholder,
            content,
        )

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)

    except Exception:
        # If processing fails, keep original file
        pass
