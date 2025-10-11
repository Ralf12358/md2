#!/usr/bin/env python3
"""
Simple Markdown preprocessor run inside the container.

Rule implemented (idempotent):
- Ensure there is a blank line immediately before the first list item of a list block
  when using '-' or '*' markers, unless the list starts at the very top of the file
  or is already preceded by a blank line. The check skips content inside fenced
  code blocks (``` or ~~~).

Example:
  **huhu**
  - a
  - b

Becomes:
  **huhu**

  - a
  - b
"""
from __future__ import annotations

import io
import os
import re
import sys
from typing import List


LIST_ITEM_RE = re.compile(r"^[\t ]*[-\*] ")
FENCE_RE = re.compile(r"^[\t ]*(```|~~~)")


def preprocess_lines(lines: List[str]) -> List[str]:
    out: List[str] = []
    in_fence = False
    fence_marker = None  # type: str | None

    for idx, line in enumerate(lines):
        # Detect fenced code blocks, track open/close using the same marker
        fence_match = FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)
            if not in_fence:
                in_fence = True
                fence_marker = marker
            else:
                # Only close if the same marker is used
                if fence_marker == marker:
                    in_fence = False
                    fence_marker = None

        if not in_fence and LIST_ITEM_RE.match(line):
            prev = out[-1] if out else None
            if prev is not None:
                # If previous line is non-blank and not already a list item, insert a blank line
                if prev.strip() != "" and not LIST_ITEM_RE.match(prev):
                    out.append("")

        out.append(line)

    return out


def preprocess_file(src: str, dst: str) -> None:
    with io.open(src, "r", encoding="utf-8") as f:
        # Preserve line endings; splitlines(keepends=False) to manage blank lines cleanly
        lines = f.read().splitlines()
    new_lines = preprocess_lines(lines)
    # Write with trailing newline if original had it; default to newline-terminated
    with io.open(dst, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))
        f.write("\n")


def main(argv: List[str]) -> int:
    if len(argv) < 3:
        sys.stderr.write("Usage: preprocess_md.py <input.md> <output.md>\n")
        return 2
    src, dst = argv[1], argv[2]
    try:
        preprocess_file(src, dst)
        return 0
    except Exception as e:
        sys.stderr.write(f"preprocess error: {e}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
