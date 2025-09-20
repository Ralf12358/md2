# TOC Page Numbers Implementation Plan

## Overview

Implement PDF overlay approach to add page numbers to Table of Contents in generated PDFs. This addresses the critical need for print-friendly navigation where clickable TOC links are useless.

## Problem Statement

- **Current**: TOC has clickable links but no page numbers
- **Issue**: When printed, links don't work and TOC becomes unusable
- **Solution**: Parse PDF and inject actual page numbers into TOC

## Technical Approach

### Input/Output
- **Input**: Generated PDF file (from current pipeline)
- **Output**: Modified PDF with page numbers in TOC
- **Fallback**: If `--no-page-numbers` flag used, return original PDF unchanged

### Implementation Strategy

1. **Two-phase generation**:
   - Phase 1: Generate PDF with placeholder page numbers in TOC
   - Phase 2: Parse PDF, extract real page numbers, replace placeholders

2. **Placeholder system**:
   - Use temporary markers like `P#01`, `P#02`, `P#03` in TOC during generation
   - Replace with actual page numbers after PDF analysis

## Detailed Implementation Steps

### Step 1: Modify TOC Generation (CSS/HTML)
```css
/* Add placeholder page numbers to TOC entries */
nav#TOC a::after {
    content: " ........ P#" attr(data-toc-index);
    float: right;
}
```

**Tasks**:
- Modify `styles/default.toc.css` to include placeholder page numbers
- Add `data-toc-index` attributes to TOC links (01, 02, 03, etc.)
- Ensure placeholders are visually similar to final format
- Test placeholder generation with current pipeline

### Step 2: PDF Parsing Module
**File**: `src/md2/pdf_parser.py`

**Functions**:
```python
def extract_heading_pages(pdf_path: Path) -> dict[str, int]:
    """Parse PDF and return mapping of heading text to page numbers"""

def find_toc_placeholders(pdf_path: Path) -> list[tuple[str, float, float]]:
    """Find placeholder positions in PDF (P#01, P#02, etc.)"""

def extract_toc_structure(pdf_path: Path) -> list[dict]:
    """Extract TOC structure with headings and placeholder positions"""
```

**Dependencies**:
- `PyMuPDF` (fitz) - robust PDF parsing
- Alternative: `pypdf` if lighter weight needed

**Algorithm**:
1. **Extract all text blocks** with coordinates and page numbers
2. **Identify headings** by font size, style, or position patterns
3. **Map headings to pages** where they appear
4. **Find placeholder patterns** (P#01, P#02, etc.) in TOC area
5. **Create mapping** of placeholder → actual page number

### Step 3: PDF Editing Module
**File**: `src/md2/pdf_editor.py`

**Functions**:
```python
def replace_text_in_pdf(pdf_path: Path, replacements: dict[str, str]) -> Path:
    """Replace placeholder text with actual page numbers"""

def calculate_text_position(placeholder_coords: tuple, new_text: str) -> tuple:
    """Calculate proper positioning for replacement text"""

def apply_toc_page_numbers(pdf_path: Path) -> Path:
    """Main function: parse PDF and inject page numbers"""
```

**Algorithm**:
1. **Open PDF** for editing
2. **Locate each placeholder** (P#01, P#02, etc.) with coordinates
3. **Calculate replacement position** (right-aligned page numbers)
4. **Remove placeholder text**
5. **Insert actual page number** at calculated position
6. **Save modified PDF**

### Step 4: Integration Module
**File**: `src/md2/toc_postprocess.py`

**Functions**:
```python
def should_add_toc_page_numbers(page_numbers_enabled: bool) -> bool:
    """Determine if TOC page numbers should be added"""

def postprocess_pdf_toc(pdf_path: Path, page_numbers_enabled: bool) -> Path:
    """Main entry point for TOC page number processing"""
```

**Logic**:
```python
def postprocess_pdf_toc(pdf_path: Path, page_numbers_enabled: bool) -> Path:
    if not page_numbers_enabled:
        return pdf_path  # Return original PDF unchanged

    if not has_toc_placeholders(pdf_path):
        return pdf_path  # No TOC or no placeholders found

    return apply_toc_page_numbers(pdf_path)
```

### Step 5: Pipeline Integration
**File**: `src/md2/conversion.py`

**Modifications**:
```python
def html2pdf(input_paths, page_numbers=True, **kwargs):
    # ... existing code ...

    # Generate PDF with current pipeline
    pdf_path = puppeteer_generate_pdf(html_path, output_path, page_numbers)

    # Post-process TOC if page numbers enabled
    if page_numbers:
        pdf_path = postprocess_pdf_toc(pdf_path, page_numbers_enabled=True)

    return pdf_path
```

### Step 6: Error Handling & Edge Cases

**Robust fallbacks**:
- **Parsing fails**: Return original PDF, log warning
- **No headings found**: Return original PDF
- **Placeholder mismatch**: Return original PDF, log error
- **PDF corruption**: Fail fast with clear error message

**Edge cases**:
- **Multiple pages per section**: Use first occurrence page number
- **Nested headings**: Maintain hierarchy in page number mapping
- **Long headings**: Handle text wrapping in TOC entries
- **Custom CSS**: Detect if placeholders are present before processing

## Testing Strategy

### Step 1: Unit Tests
**File**: `src/tests/md2/test_pdf_postprocess.py`

**Test cases**:
- PDF parsing accuracy (heading detection)
- Placeholder extraction correctness
- Page number mapping validation
- Text replacement precision
- Error handling robustness

### Step 2: Integration Tests
**File**: `src/tests/md2/test_toc_integration.py`

**Test cases**:
- End-to-end PDF generation with TOC page numbers
- Fallback behavior when page numbers disabled
- Complex document structures (nested headings)
- Edge cases (no TOC, malformed PDF)

### Step 3: Manual Validation
- **Visual inspection**: Generated PDFs with page numbers
- **Print testing**: Verify usability in printed form
- **Performance testing**: Measure processing time overhead

## Implementation Order

1. **Research & prototyping**: Test PDF parsing libraries with sample PDFs
2. **CSS modifications**: Add placeholder system to TOC generation
3. **PDF parsing module**: Extract headings and page numbers
4. **PDF editing module**: Replace placeholders with page numbers
5. **Integration**: Wire into existing pipeline
6. **Testing**: Unit tests, integration tests, manual validation
7. **Documentation**: Update README with new functionality

## Dependencies

**New dependencies**:
- `PyMuPDF` (or `pypdf`): PDF parsing and editing
- Add to `pyproject.toml` and container image

**Container modifications**:
- Install PDF processing libraries in Dockerfile
- Ensure Python packages available in container environment

## Configuration

**No new CLI flags needed**:
- TOC page numbers enabled automatically when `page_numbers=True`
- Disabled automatically when `--no-page-numbers` flag used
- Graceful fallback maintains current behavior

## Success Criteria

- ✅ **Printed PDFs**: TOC shows accurate page numbers for navigation
- ✅ **Digital PDFs**: TOC links continue to work (dual functionality)
- ✅ **Performance**: Minimal overhead (< 2x generation time)
- ✅ **Reliability**: Robust error handling, fallback to current behavior
- ✅ **Compatibility**: Works with all existing document structures

## Future Enhancements

- **Custom formatting**: Allow page number format customization
- **Right alignment**: Perfect dot leader alignment
- **Performance optimization**: Cache PDF analysis results
- **Advanced layouts**: Support complex TOC structures

---

**Note**: This approach solves the critical print usability issue while maintaining all current functionality and providing robust fallbacks.
