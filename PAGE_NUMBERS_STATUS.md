# TOC Page Numbers — Current Status (2025-09-20)

- Status: Not working yet — only white boxes appear where page numbers should be.
- Branch: will create and push `pagenumbers` with this status note.

## Summary
- End-to-end pipeline works: `md2html` → `html2pdf` → TOC PDF postprocessing.
- Tests for conversion pass locally.
- Visual result on the example shows white rectangles covering placeholders, but the expected page numbers are not visible in the PDF.

## What’s Implemented
- Placeholders injected in HTML as `P#0001`… format (4 digits), controlled via body class.
- PDF postprocess uses PyMuPDF to:
  - Find placeholder rectangles.
  - Paint a white box over each placeholder (to avoid redactions that can break links).
  - Insert the computed page number as right-aligned text inside the original placeholder rectangle.
- Number assignment uses visual order: per TOC pages, group by Y (line clusters), then left-to-right X, assign monotonically increasing numbers.

Files of interest:
- `src/md2/pdf_editor.py`
  - `apply_toc_page_numbers`: detects placeholders by words, builds `replacements` by visual order.
  - `replace_text_in_pdf`: paints white and inserts right-aligned text into a slightly shrunken rect.
- `src/md2/toc_postprocess.py` orchestrates the PDF TOC post-processing when enabled.
- `src/md2/pdf_parser.py` contains helper routines used for detection/guarding (e.g., presence of placeholders).

## Reproduction
- Ran `uv run examples/example.sh` which generates:
  - `examples/doc.html`, `examples/doc.pdf`, `examples/doc.docx`.
- Observed in viewer and via extraction that placeholders are not replaced by visible numbers. User observation: white boxes show instead of numbers.

## Observations & Findings
- Post-processing is invoked (white cover rectangles are present), so `replace_text_in_pdf` is running.
- Numbers are not visible after insertion. Possible causes:
  1) Text is inserted into an overly small or miscomputed rectangle (clipped or drawn outside the visible area).
  2) The alignment or padding makes the text box effectively zero-width (right alignment inside a too-tight box).
  3) Font/paint state causes rendering issues (unlikely: fontsize=10, color black on white background).
  4) Z-ordering: white rectangles drawn after text insertion (shouldn’t happen in our code: we draw white first, then insert text).
- Placeholder detection/ordering is separate and appears to collect candidates. Replacement painting indicates placeholders were found at least by literal search (`page.search_for(placeholder)`).
- Link preservation: by painting instead of redaction, link annotations should remain intact. In the example file, link annotations were not detected via quick scripted check (could be due to how links are produced in this doc).

## Hypotheses
- The inserted text rectangle is too small after applying padding/shrinking, causing the right-aligned text to be clipped or not rendered.
- Some placeholder tokens may be composed of multiple spans; word-based detection in `apply_toc_page_numbers` is strict (`re.fullmatch(r"P#\d{2,4}")`) and may miss them for ordering, but replacement painting uses `search_for(placeholder)` which is literal string search and seems to work (white boxes appear). The mismatch suggests the insertion happens but is not visible rather than not being attempted.

## Next Steps (Proposed)
1) Adjust text insertion geometry:
   - Do not shrink the rect; instead, expand it slightly leftward and keep inside bounds.
   - Use a measured width approach: compute a generously wide textbox from the placeholder’s x0 to x1 plus margin; right-align within it.
   - Temporarily set `fontsize=11–12` and verify visibility.
2) As a fallback, use `page.insert_text` at a computed baseline point near `(x1 - margin, y1)` instead of `insert_textbox`, to rule out textbox width issues.
3) Improve placeholder acquisition for ordering (robustness):
   - Scan spans via `page.get_text("dict")` and concatenate adjacent spans on the same line to detect `P#\d{2,4}` even when split.
   - Keep ordering logic identical (Y then X, clustered lines).
4) Verify link annotations on TOC page after paint+insert (should remain unchanged).

## Test Status
- `src/tests/md2` pass.
- Manual example build done; numbers not visible in the TOC after current replacement pass.

## Rollback/Guardrails
- If post-process fails or finds no placeholders, the file is left unchanged.
- Current code avoids redactions to preserve link annotations.

## Action Items Checklist
- [ ] Modify insertion rectangle and/or insertion method; re-build example and visually confirm numbers.
- [ ] Strengthen placeholder detection for ordering using span concatenation.
- [ ] Add a temporary debug mode to draw a faint border around the insertion rect to confirm geometry during development (disabled by default).
- [ ] Validate across multiple sample documents with TOC depth variations.
