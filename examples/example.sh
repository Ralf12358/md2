#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
uv run md2html "$SCRIPT_DIR/doc.md"  # TOC is now default
uv run md2pdf "$SCRIPT_DIR/doc.md"   # TOC is now default
