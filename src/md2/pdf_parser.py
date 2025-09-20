from aimport import *
import fitz
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def extract_heading_pages(pdf_path: Path) -> Dict[str, int]:
    """Parse PDF and return mapping of heading text to page numbers"""
    heading_pages = {}
    
    try:
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if "lines" not in block:
                    continue
                    
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        font_size = span["size"]
                        
                        # Identify headings by font size (larger fonts = headings)
                        # This is a heuristic that works well for most documents
                        if font_size > 14 and text and len(text) > 3:
                            # Clean up heading text (remove numbering if present)
                            clean_text = re.sub(r'^\d+(\.\d+)*\s+', '', text)
                            if clean_text and clean_text not in heading_pages:
                                heading_pages[clean_text] = page_num + 1  # 1-based page numbers
        
        doc.close()
        
    except Exception:
        # If parsing fails, return empty dict
        pass
    
    return heading_pages


def find_toc_placeholders(pdf_path: Path) -> List[Tuple[str, float, float, int]]:
    """Find placeholder positions in PDF (P#01, P#02, etc.)"""
    placeholders = []
    
    try:
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text_instances = page.search_for("P#")
            
            for inst in text_instances:
                # Get the full text around this position
                rect = fitz.Rect(inst.x0 - 10, inst.y0 - 5, inst.x1 + 20, inst.y1 + 5)
                text = page.get_textbox(rect)
                
                # Look for placeholder pattern (flexible: 2 or 4 digits)
                match = re.search(r'P#(\d{2,4})', text)
                if match:
                    placeholder_id = match.group(1)
                    placeholders.append((f"P#{placeholder_id}", inst.x0, inst.y0, page_num))
        
        doc.close()
        
    except Exception:
        # If parsing fails, return empty list
        pass
    
    return placeholders


def extract_toc_structure(pdf_path: Path) -> List[Dict]:
    """Extract TOC structure with headings and placeholder positions"""
    placeholders = find_toc_placeholders(pdf_path)
    heading_pages = extract_heading_pages(pdf_path)
    
    toc_structure = []
    
    try:
        doc = fitz.open(pdf_path)
        
        # Find TOC page(s) by looking for placeholder patterns
        toc_pages = set()
        for _, _, _, page_num in placeholders:
            toc_pages.add(page_num)
        
        # Extract TOC entries for each TOC page
        for page_num in toc_pages:
            page = doc[page_num]
            text = page.get_text()
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Pattern: section number + placeholder + heading text
            # E.g.: "1.2" -> "P#0003" -> "Training Prerequisites"
            for i, line in enumerate(lines):
                if line.startswith('P#'):
                    placeholder = line
                    
                    # Look for the pattern: section_num + placeholder + heading_text
                    section_num = ""
                    heading_text = ""
                    
                    # Check line before placeholder for section number
                    if i - 1 >= 0:
                        prev_line = lines[i - 1]
                        if re.match(r'^\d+(\.\d+)*$', prev_line):
                            section_num = prev_line
                    
                    # Check line after placeholder for heading text
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        # Skip if it's another section number or placeholder
                        if not re.match(r'^\d+(\.\d+)*$', next_line) and not next_line.startswith('P#'):
                            heading_text = next_line
                    
                    # Combine section number and heading text
                    if section_num and heading_text:
                        full_heading = f"{section_num} {heading_text}"
                    elif heading_text:
                        full_heading = heading_text
                    elif section_num:
                        full_heading = section_num
                    else:
                        continue  # Skip if we can't find a heading
                    
                    # Find matching page number in the document
                    actual_page = None
                    for head_text, page_no in heading_pages.items():
                        # More flexible matching
                        heading_clean = full_heading.lower().replace(' ', '').replace('.', '')
                        head_clean = head_text.lower().replace(' ', '').replace('.', '')
                        
                        # Try different matching strategies
                        if (heading_clean in head_clean or 
                            head_clean in heading_clean or
                            full_heading.lower() in head_text.lower() or 
                            head_text.lower() in full_heading.lower() or
                            heading_text.lower() in head_text.lower()):
                            actual_page = page_no
                            break
                    
                    if actual_page and actual_page > 1:  # Skip title page
                        toc_structure.append({
                            'heading': full_heading,
                            'placeholder': placeholder,
                            'page': actual_page
                        })
                    else:
                        # If no match found, add with a reasonable default page
                        # Based on the placeholder number (approximate)
                        placeholder_num = int(re.search(r'P#(\d+)', placeholder).group(1))
                        estimated_page = max(3, (placeholder_num // 5) + 2)  # Rough estimate
                        toc_structure.append({
                            'heading': full_heading,
                            'placeholder': placeholder,
                            'page': estimated_page
                        })
        
        doc.close()
        
    except Exception:
        # If parsing fails, return empty list
        pass
    
    return toc_structure