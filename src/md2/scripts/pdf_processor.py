#!/usr/bin/env python3
"""
Container-side PDF processor that handles page number insertion and TOC processing.
This replaces the host-side pdf_editor.py and pdf_parser.py functionality.
"""
import sys
import fitz
import re
import os
from pathlib import Path
from typing import Dict, Tuple, List
from collections import defaultdict


def _median(values: List[float], default: float) -> float:
    if not values:
        return default
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 == 1 else 0.5 * (s[mid - 1] + s[mid])


def _estimate_fontsize(
    page: fitz.Page, rect: fitz.Rect, fallback: float = 9.0
) -> float:
    try:
        d = page.get_text("dict")
        sizes = []
        for b in d.get("blocks", []):
            for l in b.get("lines", []):
                for s in l.get("spans", []):
                    x0, y0, x1, y1 = s.get("bbox", (0, 0, 0, 0))
                    if abs(y0 - rect.y0) < 2.0:
                        size = s.get("size")
                        if isinstance(size, (int, float)):
                            sizes.append(float(size))
        val = _median(sizes, fallback)
        return max(6.5, min(11.0, val))
    except Exception:
        return fallback


def find_toc_placeholders(pdf_path: Path) -> List[Tuple[int, fitz.Rect, str]]:
    """Find TOC placeholders in PDF and return their locations"""
    placeholders = []
    try:
        doc = fitz.open(pdf_path)
        for pno in range(len(doc)):
            words = doc[pno].get_text("words")
            for w in words:
                token = w[4] or ""
                if re.fullmatch(r"P#\d{2,4}", token):
                    placeholders.append((pno, fitz.Rect(w[0], w[1], w[2], w[3]), token))
        doc.close()
    except Exception:
        pass
    return placeholders


def replace_text_in_pdf(
    pdf_path: Path, replacements: Dict[str, str], output_path: Path
) -> None:
    """Replace placeholder text in PDF with actual page numbers"""
    doc = fitz.open(pdf_path)
    for page_index in range(len(doc)):
        page = doc[page_index]
        jobs: List[Tuple[fitz.Rect, str]] = []
        for placeholder, replacement in replacements.items():
            for r in page.search_for(placeholder) or []:
                jobs.append((fitz.Rect(r.x0, r.y0, r.x1, r.y1), replacement))
        if not jobs:
            continue

        # Paint a light-grey cover to hide placeholder glyphs, matching TOC background (#fafbfc)
        for rect, _ in jobs:
            pad_x, pad_y = 0.5, 0.2
            cover_rect = fitz.Rect(
                rect.x0 - pad_x, rect.y0 - pad_y, rect.x1 + pad_x, rect.y1 + pad_y
            )
            page.draw_rect(
                cover_rect,
                fill=(250 / 255, 251 / 255, 252 / 255),
                color=None,
                width=0,
            )

        for rect, replacement in jobs:
            draw_rect = fitz.Rect(
                max(0, rect.x0 - 6.0), rect.y0 - 0.8, rect.x1 + 36.0, rect.y1 + 0.8
            )
            if os.environ.get("MD2_TOC_DEBUG"):
                page.draw_rect(draw_rect, color=(0.8, 0.2, 0.2), width=0.3)

            approx = max(6.5, min(10.0, (rect.y1 - rect.y0) * 0.9))
            fontsize = _estimate_fontsize(page, rect, approx)

            overflow = page.insert_textbox(
                draw_rect,
                replacement,
                fontsize=fontsize,
                color=(0, 0, 0),
                fontname="helv",
                align=fitz.TEXT_ALIGN_RIGHT,
            )
            if overflow:
                try:
                    width = fitz.get_text_length(
                        replacement, fontname="helv", fontsize=fontsize
                    )
                except Exception:
                    width = 0.0
                x = max(0.0, rect.x1 - 1.5 - width)
                y = rect.y1 - 0.6
                page.insert_text(
                    (x, y),
                    replacement,
                    fontsize=fontsize,
                    color=(0, 0, 0),
                    fontname="helv",
                )

    doc.save(str(output_path))
    doc.close()


def apply_toc_page_numbers(pdf_path: Path, output_path: Path) -> None:
    """Apply TOC page numbers to PDF"""
    placeholder_infos = find_toc_placeholders(pdf_path)

    if not placeholder_infos:
        # No placeholders found, just copy the file
        if pdf_path != output_path:
            import shutil

            shutil.copy2(pdf_path, output_path)
        return

    doc = fitz.open(pdf_path)

    by_page: Dict[int, List[Tuple[fitz.Rect, str]]] = defaultdict(list)
    for pno, rect, token in placeholder_infos:
        by_page[pno].append((rect, token))
    toc_pages = sorted(by_page.keys())
    max_toc_page = max(toc_pages) if toc_pages else -1

    entries: List[Tuple[str, str]] = []
    for pno in toc_pages:
        page = doc[pno]
        words = page.get_text("words")
        rows = sorted(by_page[pno], key=lambda e: (round(e[0].y0, 1), e[0].x0))
        for rect, token in rows:
            line_words = [t for t in words if abs(t[1] - rect.y0) < 2.0]
            line_words.sort(key=lambda t: t[0])
            left_words = []
            for t in line_words:
                if t[0] >= rect.x0:
                    break
                left_words.append(t[4])
            left_text = " ".join([w for w in left_words if w]).strip()
            parts = left_text.split()
            if parts and re.fullmatch(r"\d+(?:\.\d+)*", parts[0] or ""):
                search_text = " ".join(parts[1:]).strip()
            else:
                search_text = left_text
            search_text = search_text[:80].strip()
            if search_text:
                entries.append((token, search_text))

    replacements: Dict[str, str] = {}
    start_pno = max(max_toc_page + 1, 1)
    current_pno = start_pno
    total_pages = len(doc)

    def norm(s: str) -> str:
        return re.sub(r"\s+", "", s.lower())

    for token, query in entries:
        qn = norm(query)
        found_page = None
        pno = max(current_pno, start_pno)
        while pno < total_pages:
            txt = doc[pno].get_text("text") or ""
            if qn and norm(txt).find(qn) != -1:
                found_page = pno + 1
                break
            pno += 1
        if found_page is None:
            found_page = (
                max(current_pno, start_pno) + 1
                if current_pno >= start_pno
                else start_pno + 1
            )
        else:
            current_pno = max(current_pno, pno)
        replacements[token] = str(found_page)

    doc.close()
    replace_text_in_pdf(pdf_path, replacements, output_path)


def main():
    """Main entry point for PDF processing"""
    if len(sys.argv) != 4:
        print(
            "Usage: pdf_processor.py <input_pdf> <output_pdf> <enable_page_numbers>",
            file=sys.stderr,
        )
        sys.exit(1)

    input_pdf = Path(sys.argv[1])
    output_pdf = Path(sys.argv[2])
    enable_page_numbers = sys.argv[3].lower() == "true"

    if not input_pdf.exists():
        print(f"Error: Input PDF {input_pdf} does not exist", file=sys.stderr)
        sys.exit(1)

    if enable_page_numbers:
        apply_toc_page_numbers(input_pdf, output_pdf)
    else:
        # Just copy the file if page numbers are disabled
        if input_pdf != output_pdf:
            import shutil

            shutil.copy2(input_pdf, output_pdf)

    print(f"PDF processed: {input_pdf} -> {output_pdf}")


if __name__ == "__main__":
    main()
