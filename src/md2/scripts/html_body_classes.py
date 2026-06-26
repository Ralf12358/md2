#!/usr/bin/env python3
import re
import sys
from pathlib import Path


BODY_RE = re.compile(r"<body(?P<attrs>[^>]*)>", re.IGNORECASE)
CLASS_RE = re.compile(r"\bclass\s*=\s*([\"'])(?P<value>.*?)\1", re.IGNORECASE | re.DOTALL)


class BodyClassError(ValueError):
    pass


def add_body_classes(html: str, classes: list[str]) -> str:
    match = BODY_RE.search(html)
    if not match:
        raise BodyClassError("No <body> tag found")

    attrs = match.group("attrs")
    class_match = CLASS_RE.search(attrs)
    if class_match:
        existing = class_match.group("value").split()
        merged = existing[:]
        for class_name in classes:
            if class_name not in merged:
                merged.append(class_name)
        new_class_attr = f'class="{" ".join(merged)}"'
        new_attrs = attrs[: class_match.start()] + new_class_attr + attrs[class_match.end() :]
    else:
        new_attrs = attrs + f' class="{" ".join(classes)}"'

    return html[: match.start()] + f"<body{new_attrs}>" + html[match.end() :]


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: html_body_classes.py file.html class [class ...]", file=sys.stderr)
        return 2

    path = Path(argv[0])
    classes = argv[1:]
    try:
        path.write_text(
            add_body_classes(path.read_text(encoding="utf-8"), classes),
            encoding="utf-8",
        )
    except BodyClassError as exc:
        print(f"html_body_classes: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
