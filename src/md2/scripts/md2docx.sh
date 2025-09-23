#!/usr/bin/env bash
set -euo pipefail

# DOCX generation script that handles temporary markdown processing inside container
# Usage: md2docx.sh <input_md> <output_docx> <title> <dialect> <markdown_flags...>

INPUT_MD="${1:-/work/input.md}"
OUTPUT_DOCX="${2:-/work/output.docx}"
DOC_TITLE="${3:-}"
DIALECT="${4:-pandoc}"
shift 4 2>/dev/null || true
MARKDOWN_FLAGS=("$@")

if [[ ! -f "$INPUT_MD" ]]; then
    echo "Error: Input markdown file $INPUT_MD does not exist" >&2
    exit 1
fi

# Determine the actual title to use
ACTUAL_TITLE="$DOC_TITLE"
if [[ -z "$ACTUAL_TITLE" ]]; then
    # Auto-detect title from H1 headers or use filename
    H1_COUNT=$(grep -c '^# ' "$INPUT_MD" 2>/dev/null || echo "0")
    if [[ "$H1_COUNT" == "1" ]]; then
        ACTUAL_TITLE=$(grep '^# ' "$INPUT_MD" | head -1 | sed 's/^# *//' || echo "")
    fi
    if [[ -z "$ACTUAL_TITLE" ]]; then
        ACTUAL_TITLE=$(basename "$INPUT_MD" .md)
    fi
fi

# Check if we need to handle multiple H1s
WORKING_MD="$INPUT_MD"
H1_COUNT=$(grep -c '^# ' "$INPUT_MD" 2>/dev/null || echo "0")

if [[ "$H1_COUNT" -gt 1 ]]; then
    # Create temporary markdown with shifted headings inside container
    TEMP_MD="/tmp/temp_docx_$(basename "$INPUT_MD")"
    echo "Creating temporary markdown with shifted headings: $TEMP_MD"

    # Shift headings and add title
    {
        echo "# $ACTUAL_TITLE"
        echo ""
        # Shift ATX-style headers (add one # to each)
        sed 's/^#\(#*\) /##\1 /' "$INPUT_MD" |
        # Convert Setext-style headers to ATX and shift
        sed '/^.\+$/N;s/\(.*\)\n=\+$/## \1/' |
        sed '/^.\+$/N;s/\(.*\)\n-\+$/### \1/'
    } > "$TEMP_MD"

    WORKING_MD="$TEMP_MD"
fi

# Set input format based on dialect
case "$DIALECT" in
    "github")
        INPUT_FORMAT="gfm+tex_math_dollars+emoji+footnotes+task_lists+strikeout"
        ;;
    "commonmark")
        INPUT_FORMAT="commonmark_x+tex_math_dollars+tex_math_single_backslash+smart+emoji+footnotes+definition_lists+fenced_code_attributes+link_attributes+task_lists+strikeout+pipe_tables+table_captions"
        ;;
    *)
        INPUT_FORMAT="markdown+tex_math_dollars+tex_math_single_backslash+smart+emoji+footnotes+definition_lists+fenced_code_attributes+link_attributes+task_lists+strikeout+pipe_tables+table_captions+auto_identifiers+implicit_header_references"
        ;;
esac

# Build pandoc command
PANDOC_CMD=(
    "pandoc"
    "-f" "$INPUT_FORMAT"
    "-t" "docx"
    "--standalone"
    "--resource-path=/work:/styles:/tmp"
    "--lua-filter=/filters/mermaid.lua"
)

# Add markdown flags
PANDOC_CMD+=("${MARKDOWN_FLAGS[@]}")

# Set document title
PANDOC_CMD+=("--metadata=title:$ACTUAL_TITLE")

# Add input and output
PANDOC_CMD+=("$WORKING_MD" "-o" "$OUTPUT_DOCX")

# Add reference doc if environment variable is set
if [[ -n "${REFERENCE_DOC:-}" ]]; then
    PANDOC_CMD+=("--reference-doc=$REFERENCE_DOC")
fi

echo "Converting markdown to DOCX: $WORKING_MD -> $OUTPUT_DOCX"

# Run pandoc
"${PANDOC_CMD[@]}"

# Clean up temporary file if created
if [[ "$H1_COUNT" -gt 1 && -f "$TEMP_MD" ]]; then
    rm -f "$TEMP_MD"
fi

echo "DOCX generation complete: $OUTPUT_DOCX"
