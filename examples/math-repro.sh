#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
./md2pdf.sh --css styles/default.css examples/math-repro.md
