#!/usr/bin/env python3
"""
Simple Markdown preprocessor run inside the container.

Rules implemented (idempotent):
1. Ensure there is a blank line immediately before the first list item of a list block
   when using '-' or '*' markers, unless the list starts at the very top of the file
   or is already preceded by a blank line. The check skips content inside fenced
   code blocks (``` or ~~~).

2. Convert pseudo-headings (paragraphs with only bold text, optionally ending with ':')
   to proper markdown headings at appropriate level, tracking heading hierarchy.

Example:
  **huhu**
  - a
  - b

Becomes:
  **huhu**

  - a
  - b

Example pseudo-heading:
  **Performance Concerns:**
  Some text

Becomes:
  ##### Performance Concerns
  Some text
"""
from __future__ import annotations

import io
import os
import re
import sys
from typing import List


LIST_ITEM_RE = re.compile(r"^[\t ]*[-\*] ")
FENCE_RE = re.compile(r"^[\t ]*(```|~~~)")
HEADING_RE = re.compile(r"^(#{1,6})\s+")
# Match line that starts with **text** (optionally with :) and optionally has trailing text
PSEUDO_HEADING_RE = re.compile(r"^\*\*([^*]+)\*\*:?\s*(.*)$")


def preprocess_lines(lines: List[str]) -> List[str]:
    out: List[str] = []
    in_fence = False
    fence_marker = None  # type: str | None
    current_heading_level = 0  # Track deepest heading level seen
    just_converted_heading = False  # Track if we just converted a pseudo-heading

    # First pass: remove trailing spaces before --- to prevent Setext heading misinterpretation
    # This prevents Pandoc from treating "text\n---" as a Setext H1 heading
    processed_lines = []
    for i, line in enumerate(lines):
        processed_lines.append(line)
        # If this line is exactly "---" (a thematic break), check if previous line has trailing spaces
        if (
            i > 0
            and line.strip() == "---"
            and processed_lines[i - 1].endswith((" ", "\t"))
        ):
            # Remove trailing whitespace from the line before ---
            processed_lines[i - 1] = processed_lines[i - 1].rstrip()

    lines = processed_lines

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

        # Track heading levels to determine pseudo-heading level
        if not in_fence:
            heading_match = HEADING_RE.match(line)
            if heading_match:
                current_heading_level = len(heading_match.group(1))

        # Convert pseudo-headings to real headings
        # Only if: line starts with **text:** or **text** (standalone)
        converted_this_line = False
        if not in_fence:
            pseudo_match = PSEUDO_HEADING_RE.match(line)
            if pseudo_match:
                heading_text_raw = pseudo_match.group(1).strip()
                trailing_text = pseudo_match.group(2).strip()

                # Check if this looks like a heading:
                # - Standalone with optional colon: **Performance Concerns:** or **Performance Concerns**
                # - NOT a label-value pair: **Effort:** some text (trailing text present)
                has_colon = heading_text_raw.endswith(":")
                heading_text = heading_text_raw.rstrip(":").strip()
                is_standalone = trailing_text == ""

                # Only convert if:
                # 1. Standalone (no trailing text) - with or without colon
                # 2. NOT a label-value pair (colon + trailing text = skip)
                is_short_heading = len(heading_text) <= 100
                looks_like_heading = (
                    is_standalone  # Must be standalone, colon is optional
                )

                if is_short_heading and looks_like_heading:
                    # Check if next non-blank line exists
                    next_content_idx = idx + 1
                    while (
                        next_content_idx < len(lines)
                        and lines[next_content_idx].strip() == ""
                    ):
                        next_content_idx += 1

                    has_following_content = next_content_idx < len(lines)

                    if has_following_content:
                        # Convert to heading: use current level + 1, max at h6
                        new_level = min(current_heading_level + 1, 6)
                        if new_level == 0:  # No previous headings, default to h5
                            new_level = 5

                        heading_marker = "#" * new_level
                        line = f"{heading_marker} {heading_text}"
                        current_heading_level = new_level
                        converted_this_line = True

                        # If there was trailing text (shouldn't happen with our rules), add it as next line
                        if trailing_text and has_colon:
                            out.append(line)
                            out.append("")
                            line = trailing_text
                            converted_this_line = False

        # After a converted pseudo-heading, ensure blank line before next content
        if just_converted_heading and line.strip() != "":
            out.append("")

        just_converted_heading = converted_this_line

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
