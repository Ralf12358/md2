#!/usr/bin/env python3
import html
import re
import sys
from pathlib import Path
from typing import NamedTuple


REQUIRED_TAGS = {"sender", "receiver"}
OPTIONAL_TAGS = {"senderline", "date", "email", "phone", "reference"}
SUPPORTED_TAGS = REQUIRED_TAGS | OPTIONAL_TAGS
META_TAG_RE = re.compile(r"^<([A-Za-z][A-Za-z0-9_-]*)>\s*$")
CLOSE_TAG_RE = re.compile(r"^</([A-Za-z][A-Za-z0-9_-]*)>\s*$")


class LetterPreprocessError(ValueError):
    pass


class ParsedTag(NamedTuple):
    name: str
    lines: list[str]


def preprocess_letter_markdown(text: str) -> str:
    tags, body = _parse_letter_metadata(text.splitlines())
    _validate_required_tags(tags)
    return _render_letter_header(tags) + "\n\n" + "\n".join(body).lstrip("\n")


def _parse_letter_metadata(lines: list[str]) -> tuple[dict[str, ParsedTag], list[str]]:
    tags: dict[str, ParsedTag] = {}
    body_start = _first_non_blank_index(lines)
    index = body_start

    while index < len(lines):
        line = lines[index]
        if line.strip() == "":
            index += 1
            continue

        open_match = META_TAG_RE.match(line)
        if not open_match:
            break

        tag_name = open_match.group(1)
        if tag_name not in SUPPORTED_TAGS:
            raise LetterPreprocessError(f"Unknown letter tag <{tag_name}>")
        if tag_name in tags:
            raise LetterPreprocessError(f"Duplicate letter tag <{tag_name}>")

        parsed, index = _parse_tag(lines, index, tag_name)
        tags[tag_name] = parsed

    body = lines[:body_start] + lines[index:]
    return tags, body


def _first_non_blank_index(lines: list[str]) -> int:
    for index, line in enumerate(lines):
        if line.strip():
            return index
    return len(lines)


def _parse_tag(lines: list[str], start: int, tag_name: str) -> tuple[ParsedTag, int]:
    content: list[str] = []
    index = start + 1
    while index < len(lines):
        line = lines[index]
        close_match = CLOSE_TAG_RE.match(line)
        if close_match:
            close_name = close_match.group(1)
            if close_name != tag_name:
                raise LetterPreprocessError(
                    f"Mismatched closing tag </{close_name}> for <{tag_name}>"
                )
            _validate_tag_content(tag_name, content)
            return ParsedTag(tag_name, content), index + 1

        if META_TAG_RE.match(line) or CLOSE_TAG_RE.match(line):
            raise LetterPreprocessError(f"Nested or unexpected tag inside <{tag_name}>")

        content.append(line)
        index += 1

    raise LetterPreprocessError(f"Unclosed letter tag <{tag_name}>")


def _validate_tag_content(tag_name: str, lines: list[str]) -> None:
    if tag_name in REQUIRED_TAGS and not _non_empty_lines(lines):
        raise LetterPreprocessError(f"Required letter tag <{tag_name}> is empty")


def _validate_required_tags(tags: dict[str, ParsedTag]) -> None:
    missing = sorted(REQUIRED_TAGS - tags.keys())
    if missing:
        names = ", ".join(f"<{name}>" for name in missing)
        raise LetterPreprocessError(f"Missing required letter tag: {names}")


def _render_letter_header(tags: dict[str, ParsedTag]) -> str:
    sender_lines = _non_empty_lines(tags["sender"].lines)
    receiver_lines = _non_empty_lines(tags["receiver"].lines)
    senderline = _senderline(tags, sender_lines)

    html_lines = [
        '<div class="md2-letter-header">',
        f'  <div class="md2-letter-sender-line">{senderline}</div>',
        f'  <div class="md2-letter-receiver">{_join_html_lines(receiver_lines)}</div>',
    ]

    meta_items = _render_meta_items(tags)
    if meta_items:
        html_lines.append('  <dl class="md2-letter-meta">')
        html_lines.extend(meta_items)
        html_lines.append("  </dl>")

    html_lines.append("</div>")
    return "\n".join(html_lines)


def _senderline(tags: dict[str, ParsedTag], sender_lines: list[str]) -> str:
    if "senderline" in tags:
        custom_lines = _non_empty_lines(tags["senderline"].lines)
        if custom_lines:
            return _join_html_lines(custom_lines)
    return " - ".join(html.escape(line) for line in sender_lines)


def _render_meta_items(tags: dict[str, ParsedTag]) -> list[str]:
    labels = {
        "email": "E-Mail",
        "phone": "Telefon",
        "reference": "Referenz",
        "date": "Datum",
    }
    items: list[str] = []
    for name, label in labels.items():
        if name not in tags:
            continue
        lines = _non_empty_lines(tags[name].lines)
        if not lines:
            continue
        items.append(
            f'    <div class="md2-letter-meta-{name}"><dt>{label}</dt><dd>{_join_html_lines(lines)}</dd></div>'
        )
    return items


def _non_empty_lines(lines: list[str]) -> list[str]:
    return [line.strip() for line in lines if line.strip()]


def _join_html_lines(lines: list[str]) -> str:
    return "<br>".join(html.escape(line) for line in lines)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: letter_preprocess.py input.md output.md", file=sys.stderr)
        return 2

    input_path = Path(argv[0])
    output_path = Path(argv[1])
    try:
        output_path.write_text(
            preprocess_letter_markdown(input_path.read_text(encoding="utf-8")),
            encoding="utf-8",
        )
    except LetterPreprocessError as exc:
        print(f"letter_preprocess: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
