from aimport import *
import fitz
import re
from pathlib import Path
from typing import Dict, Tuple, List


def replace_text_in_pdf(pdf_path: Path, replacements: Dict[str, str]) -> Path:
    """Replace placeholder text with actual page numbers.

    Strategy:
    1) For each page, collect all placeholder rectangles and intended replacement strings.
    2) Add redaction annotations for those rectangles and apply redactions to remove placeholders.
    3) After redactions (so our text isn't removed), insert the replacement page number text,
       right-aligned to the original placeholder rect.
    """
    output_path = pdf_path.with_suffix(".toc_processed.pdf")

    try:
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]

            # 1) Collect jobs for this page: (rect, replacement)
            jobs: List[Tuple[fitz.Rect, str]] = []
            for placeholder, replacement in replacements.items():
                rects = page.search_for(placeholder) or []
                for r in rects:
                    rect = fitz.Rect(r.x0, r.y0, r.x1, r.y1)
                    jobs.append((rect, replacement))

            if not jobs:
                continue

            # 2) Paint over placeholders (white box), preserving annotations/links
            for rect, _ in jobs:
                pad_x = 0.5
                pad_y = 0.2
                cover_rect = fitz.Rect(
                    rect.x0 - pad_x,
                    rect.y0 - pad_y,
                    rect.x1 + pad_x,
                    rect.y1 + pad_y,
                )
                page.draw_rect(cover_rect, fill=(1, 1, 1), color=None, width=0)

            # 3) Insert replacement numbers right-aligned inside the original rectangle
            for rect, replacement in jobs:
                # Slightly shrink the rect to keep text inside bounds
                pad_x = 1.0
                pad_y = 0.5
                draw_rect = fitz.Rect(
                    rect.x0 + pad_x,
                    rect.y0 + pad_y,
                    rect.x1 - pad_x,
                    rect.y1 - pad_y,
                )
                # Right-align within the original placeholder rectangle
                page.insert_textbox(
                    draw_rect,
                    replacement,
                    fontsize=10,
                    color=(0, 0, 0),
                    align=fitz.TEXT_ALIGN_RIGHT,
                )

        # Save the modified PDF
        doc.save(str(output_path))
        doc.close()

        # Replace original with processed version
        output_path.replace(pdf_path)

    except Exception:
        # If processing fails, keep original file unchanged
        if output_path.exists():
            output_path.unlink()

    return pdf_path


def calculate_text_position(placeholder_coords: Tuple[float, float, float, float], new_text: str) -> Tuple[float, float]:
    """Calculate proper positioning for replacement text"""
    x0, y0, x1, y1 = placeholder_coords
    
    # Position replacement text at the right edge of the placeholder area
    char_width = 6  # Approximate character width
    new_x = x1 - len(new_text) * char_width
    new_y = y1
    
    return (new_x, new_y)


def apply_toc_page_numbers(pdf_path: Path) -> Path:
    """Main function: parse PDF and inject page numbers"""
    # Build replacements based on placeholder visual order to ensure numbering and robustness
    doc = fitz.open(pdf_path)

    # Find all placeholders across pages
    placeholder_rects = []  # (page_num, rect, text)
    for pno in range(len(doc)):
        page = doc[pno]
        # match P# with 2-4 digits; we only care text to map back by literal
        for _ in page.search_for("P#"):
            pass  # cheap warm-up
        # Use page.get_text("words") to capture words and assemble matches
        words = page.get_text("words")  # list of (x0, y0, x1, y1, word, block_no, line_no, word_no)
        # Identify tokens that look like P#dddd or P#dd
        for w in words:
            text = w[4]
            if re.fullmatch(r"P#\d{2,4}", text):
                rect = fitz.Rect(w[0], w[1], w[2], w[3])
                placeholder_rects.append((pno, rect, text))

    if not placeholder_rects:
        doc.close()
        return pdf_path

    # Heuristic: identify TOC pages as those that contain many placeholders
    from collections import defaultdict
    by_page = defaultdict(list)
    for pno, rect, text in placeholder_rects:
        by_page[pno].append((rect, text))

    toc_pages = sorted(by_page.keys(), key=lambda k: -len(by_page[k]))
    if not toc_pages:
        doc.close()
        return pdf_path

    # Build replacements monotonically by the visual Y order per page.
    # Group placeholders that are on the same visual line (close y) to avoid duplicates.
    replacements = {}
    next_page_num = 2  # typically content starts after title (page 1), adjust if needed
    for pno in toc_pages:
        entries = by_page[pno]
        # sort by y (ascending), then x
        entries.sort(key=lambda e: (round(e[0].y0, 1), e[0].x0))

        # cluster by y proximity (same line)
        line_clusters = []
        for rect, text in entries:
            if not line_clusters or abs(line_clusters[-1][0].y0 - rect.y0) > 2.0:
                line_clusters.append((rect, [(rect, text)]))
            else:
                line_clusters[-1][1].append((rect, text))

        for _, items in line_clusters:
            # assign the same (monotonic) page number to all placeholders on that line
            for rect, text in items:
                replacements[text] = str(next_page_num)
            next_page_num += 1

    doc.close()

    return replace_text_in_pdf(pdf_path, replacements)