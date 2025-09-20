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

# Create temporary PDF for processing
TEMP_PDF="/tmp/temp_$(basename "$OUTPUT_PDF")"

echo "Converting HTML to PDF: $INPUT_HTML -> $TEMP_PDF"

# Convert HTML to PDF using print.js
node /app/print.js "$INPUT_HTML" "$TEMP_PDF" --pageNumbers="$PAGE_NUMBERS"

echo "Processing PDF for page numbers: $PAGE_NUMBERS"

# Process PDF for page numbers (if enabled) and move to final location
python3 /usr/local/bin/pdf_processor.py "$TEMP_PDF" "$OUTPUT_PDF" "$PAGE_NUMBERS"

# Clean up temporary file
rm -f "$TEMP_PDF"

echo "PDF generation complete: $OUTPUT_PDF"