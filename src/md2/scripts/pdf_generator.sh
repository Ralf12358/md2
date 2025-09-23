#!/usr/bin/env bash
set -euo pipefail

# Unified PDF generation script that handles HTML->PDF conversion and post-processing
# Usage: pdf_generator.sh <input_html> <output_pdf> <page_numbers_enabled>

INPUT_HTML="${1:-/work/input.html}"
OUTPUT_PDF="${2:-/work/output.pdf}"
PAGE_NUMBERS="${3:-true}"

if [[ ! -f "$INPUT_HTML" ]]; then
    echo "Error: Input HTML file $INPUT_HTML does not exist" >&2
    exit 1
fi

# If page numbers are enabled, create a temporary HTML copy with TOC placeholders
WORKING_HTML="$INPUT_HTML"
if [[ "$PAGE_NUMBERS" == "true" ]]; then
    TEMP_HTML="/tmp/temp_pdf_$(basename "$INPUT_HTML")"
    echo "Creating temporary HTML with TOC placeholders: $TEMP_HTML"
    cp "$INPUT_HTML" "$TEMP_HTML"

    # Add TOC placeholders to the temporary copy
    python3 /scripts/html_postprocess.py "$TEMP_HTML" true
    WORKING_HTML="$TEMP_HTML"
fi

# Create temporary PDF for processing
TEMP_PDF="/tmp/temp_$(basename "$OUTPUT_PDF")"

echo "Converting HTML to PDF: $WORKING_HTML -> $TEMP_PDF"

# Convert HTML to PDF using print.js
node /app/print.js "$WORKING_HTML" "$TEMP_PDF" --pageNumbers="$PAGE_NUMBERS"

echo "Processing PDF for page numbers: $PAGE_NUMBERS"

# Process PDF for page numbers (if enabled) and move to final location
python3 /scripts/pdf_processor.py "$TEMP_PDF" "$OUTPUT_PDF" "$PAGE_NUMBERS"

# Clean up temporary files
rm -f "$TEMP_PDF"
if [[ "$PAGE_NUMBERS" == "true" && -f "$TEMP_HTML" ]]; then
    rm -f "$TEMP_HTML"
fi

echo "PDF generation complete: $OUTPUT_PDF"
