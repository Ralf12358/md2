from aimport import *
import sys
from pathlib import Path
from typing import List, Optional
from .conversion import md2html, md2pdf, html2pdf, md2docx


def usage_md2html() -> None:
    usage = """Usage: md2html [options] file1.md [file2.md ...]

Markdown dialect options:
    --pandoc         Pandoc Markdown (default; richest features)
    --commonmark     CommonMark-X flavor
    --github         Github Flavored Markdown (limited extensions)

Markdown extension options:
      --fcollapse-whitespace
                       Collapse non-trivial whitespace
      --flatex-math    Enable LaTeX style mathematics spans
      --fpermissive-atx-headers
                       Allow ATX headers without delimiting space
      --fpermissive-url-autolinks
                       Allow URL autolinks without '<', '>'
      --fpermissive-www-autolinks
                       Allow WWW autolinks without any scheme (e.g. 'www.example.com')
      --fpermissive-email-autolinks
                       Allow e-mail autolinks without '<', '>' and 'mailto:'
      --fpermissive-autolinks
                       Same as --fpermissive-url-autolinks --fpermissive-www-autolinks
                       --fpermissive-email-autolinks
      --fhard-soft-breaks
                       Force all soft breaks to act as hard breaks
      --fstrikethrough Enable strike-through spans
      --ftables        Enable tables
      --ftasklists     Enable task lists
      --funderline     Enable underline spans
      --fwiki-links    Enable wiki links

Markdown suppression options:
      --fno-html-blocks
                       Disable raw HTML blocks
      --fno-html-spans
                       Disable raw HTML spans
      --fno-html       Same as --fno-html-blocks --fno-html-spans
      --fno-indented-code
                       Disable indented code blocks

HTML generator options:
      --fverbatim-entities
                       Do not translate entities
    --no-toc         Disable Table of Contents (default: enabled)
    --toc-depth=N    TOC depth (levels), default per Pandoc
      --html-title=TITLE Sets the title of the document
      --html-css=URL   In full HTML or XHTML mode add a css link
      --css=PATH       CSS file to use for styling
"""
    print(usage, file=sys.stderr)
    sys.exit(1)


def main_md2html(argv: Optional[List[str]] = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    css_path = None
    dialect = "pandoc"
    markdown_flags = ["--toc"]  # TOC enabled by default
    html_title = None
    html_css = None
    files = []
    i = 0

    while i < len(argv):
        arg = argv[i]

        if arg == "--css":
            if i + 1 >= len(argv):
                print("--css requires a value", file=sys.stderr)
                usage_md2html()
            css_path = argv[i + 1]
            i += 2
        elif arg.startswith("--html-title="):
            html_title = arg[13:]  # len("--html-title=")
            i += 1
        elif arg.startswith("--html-css="):
            html_css = arg[11:]  # len("--html-css=")
            i += 1
        elif arg == "--no-toc":
            # Remove any prior --toc and record explicit disable
            markdown_flags = [f for f in markdown_flags if f != "--toc"]
            if "--no-toc" not in markdown_flags:
                markdown_flags.append("--no-toc")
            i += 1
        elif arg.startswith("--toc-depth="):
            markdown_flags.append(arg)
            i += 1
        elif arg == "--commonmark":
            dialect = "commonmark"
            i += 1
        elif arg == "--github":
            dialect = "github"
            i += 1
        elif arg in [
            "--fcollapse-whitespace",
            "--flatex-math",
            "--fpermissive-atx-headers",
            "--fpermissive-url-autolinks",
            "--fpermissive-www-autolinks",
            "--fpermissive-email-autolinks",
            "--fpermissive-autolinks",
            "--fhard-soft-breaks",
            "--fstrikethrough",
            "--ftables",
            "--ftasklists",
            "--funderline",
            "--fwiki-links",
            "--fno-html-blocks",
            "--fno-html-spans",
            "--fno-html",
            "--fno-indented-code",
            "--fverbatim-entities",
        ]:
            markdown_flags.append(arg)
            i += 1
        elif arg.startswith("-"):
            print(f"Unknown option: {arg}", file=sys.stderr)
            usage_md2html()
        else:
            files.append(arg)
            i += 1

    if not files:
        usage_md2html()

    md2html(
        [Path(f) for f in files],
        css=css_path,
        dialect=dialect,
        markdown_flags=markdown_flags,
        html_title=html_title,
        html_css=html_css,
    )


def usage_md2pdf() -> None:
    usage = """Usage: md2pdf [options] file1.md [file2.md ...]

Markdown dialect options:
    --pandoc         Pandoc Markdown (default; richest features)
    --commonmark     CommonMark-X flavor
    --github         Github Flavored Markdown (limited extensions)

Markdown extension options:
      --fcollapse-whitespace
                       Collapse non-trivial whitespace
      --flatex-math    Enable LaTeX style mathematics spans
      --fpermissive-atx-headers
                       Allow ATX headers without delimiting space
      --fpermissive-url-autolinks
                       Allow URL autolinks without '<', '>'
      --fpermissive-www-autolinks
                       Allow WWW autolinks without any scheme (e.g. 'www.example.com')
      --fpermissive-email-autolinks
                       Allow e-mail autolinks without '<', '>' and 'mailto:'
      --fpermissive-autolinks
                       Same as --fpermissive-url-autolinks --fpermissive-www-autolinks
                       --fpermissive-email-autolinks
      --fhard-soft-breaks
                       Force all soft breaks to act as hard breaks
      --fstrikethrough Enable strike-through spans
      --ftables        Enable tables
      --ftasklists     Enable task lists
      --funderline     Enable underline spans
      --fwiki-links    Enable wiki links

Markdown suppression options:
      --fno-html-blocks
                       Disable raw HTML blocks
      --fno-html-spans
                       Disable raw HTML spans
      --fno-html       Same as --fno-html-blocks --fno-html-spans
      --fno-indented-code
                       Disable indented code blocks

HTML generator options:
      --fverbatim-entities
                       Do not translate entities
    --no-toc         Disable Table of Contents (default: enabled)
    --toc-depth=N    TOC depth (levels), default per Pandoc
      --html-title=TITLE Sets the title of the document
      --html-css=URL   In full HTML or XHTML mode add a css link
      --css=PATH       CSS file to use for styling
"""
    print(usage, file=sys.stderr)
    sys.exit(1)


def main_md2pdf(argv: Optional[List[str]] = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    css_path = None
    dialect = "pandoc"
    markdown_flags = ["--toc"]  # TOC enabled by default
    html_title = None
    html_css = None
    files = []
    i = 0

    while i < len(argv):
        arg = argv[i]

        if arg == "--css":
            if i + 1 >= len(argv):
                print("--css requires a value", file=sys.stderr)
                usage_md2pdf()
            css_path = argv[i + 1]
            i += 2
        elif arg.startswith("--html-title="):
            html_title = arg[13:]  # len("--html-title=")
            i += 1
        elif arg.startswith("--html-css="):
            html_css = arg[11:]  # len("--html-css=")
            i += 1
        elif arg == "--no-toc":
            # Remove any prior --toc and record explicit disable
            markdown_flags = [f for f in markdown_flags if f != "--toc"]
            if "--no-toc" not in markdown_flags:
                markdown_flags.append("--no-toc")
            i += 1
        elif arg.startswith("--toc-depth="):
            markdown_flags.append(arg)
            i += 1
        elif arg == "--commonmark":
            dialect = "commonmark"
            i += 1
        elif arg == "--github":
            dialect = "github"
            i += 1
        elif arg in [
            "--fcollapse-whitespace",
            "--flatex-math",
            "--fpermissive-atx-headers",
            "--fpermissive-url-autolinks",
            "--fpermissive-www-autolinks",
            "--fpermissive-email-autolinks",
            "--fpermissive-autolinks",
            "--fhard-soft-breaks",
            "--fstrikethrough",
            "--ftables",
            "--ftasklists",
            "--funderline",
            "--fwiki-links",
            "--fno-html-blocks",
            "--fno-html-spans",
            "--fno-html",
            "--fno-indented-code",
            "--fverbatim-entities",
        ]:
            markdown_flags.append(arg)
            i += 1
        elif arg.startswith("-"):
            print(f"Unknown option: {arg}", file=sys.stderr)
            usage_md2pdf()
        else:
            files.append(arg)
            i += 1

    if not files:
        usage_md2pdf()

    md2pdf(
        [Path(f) for f in files],
        css=css_path,
        dialect=dialect,
        markdown_flags=markdown_flags,
        html_title=html_title,
        html_css=html_css,
    )


def usage_html2pdf() -> None:
    print("Usage: html2pdf file1.html [file2.html ...]", file=sys.stderr)
    sys.exit(1)


def main_html2pdf(argv: Optional[List[str]] = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    files = []
    for arg in argv:
        if arg.startswith("-"):
            print(f"Unknown option: {arg}", file=sys.stderr)
            usage_html2pdf()
        else:
            files.append(arg)

    if not files:
        usage_html2pdf()

    html2pdf([Path(f) for f in files])


if __name__ == "__main__":
    main_md2html()


def usage_md2docx() -> None:
    usage = """Usage: md2docx [options] file1.md [file2.md ...]

Markdown dialect options:
    --pandoc         Pandoc Markdown (default; richest features)
    --commonmark     CommonMark-X flavor
    --github         Github Flavored Markdown (limited extensions)

Markdown extension options:
      --fcollapse-whitespace
                       Collapse non-trivial whitespace
      --flatex-math    Enable LaTeX style mathematics spans
      --fpermissive-atx-headers
                       Allow ATX headers without delimiting space
      --fpermissive-url-autolinks
                       Allow URL autolinks without '<', '>'
      --fpermissive-www-autolinks
                       Allow WWW autolinks without any scheme (e.g. 'www.example.com')
      --fpermissive-email-autolinks
                       Allow e-mail autolinks without '<', '>' and 'mailto:'
      --fpermissive-autolinks
                       Same as --fpermissive-url-autolinks --fpermissive-www-autolinks
                       --fpermissive-email-autolinks
      --fhard-soft-breaks
                       Force all soft breaks to act as hard breaks
      --fstrikethrough Enable strike-through spans
      --ftables        Enable tables
      --ftasklists     Enable task lists
      --funderline     Enable underline spans
      --fwiki-links    Enable wiki links

Markdown suppression options:
      --fno-html-blocks
                       Disable raw HTML blocks
      --fno-html-spans
                       Disable raw HTML spans
      --fno-html       Same as --fno-html-blocks --fno-html-spans
      --fno-indented-code
                       Disable indented code blocks

DOCX options:
    --no-toc         Disable Table of Contents (default: enabled)
    --toc-depth=N    TOC depth (levels), default per Pandoc
    --reference-doc=PATH  Use a Word reference template for styles
"""
    print(usage, file=sys.stderr)
    sys.exit(1)


def main_md2docx(argv: Optional[List[str]] = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    dialect = "pandoc"
    markdown_flags: List[str] = ["--toc"]
    reference_doc: Optional[str] = None
    files: List[str] = []
    i = 0

    while i < len(argv):
        arg = argv[i]
        if arg == "--no-toc":
            markdown_flags = [f for f in markdown_flags if f != "--toc"]
            if "--no-toc" not in markdown_flags:
                markdown_flags.append("--no-toc")
            i += 1
        elif arg.startswith("--toc-depth="):
            markdown_flags.append(arg)
            i += 1
        elif arg.startswith("--reference-doc="):
            reference_doc = arg.split("=", 1)[1]
            i += 1
        elif arg == "--reference-doc":
            if i + 1 >= len(argv):
                print("--reference-doc requires a value", file=sys.stderr)
                usage_md2docx()
            reference_doc = argv[i + 1]
            i += 2
        elif arg == "--commonmark":
            dialect = "commonmark"
            i += 1
        elif arg == "--github":
            dialect = "github"
            i += 1
        elif arg in [
            "--fcollapse-whitespace",
            "--flatex-math",
            "--fpermissive-atx-headers",
            "--fpermissive-url-autolinks",
            "--fpermissive-www-autolinks",
            "--fpermissive-email-autolinks",
            "--fpermissive-autolinks",
            "--fhard-soft-breaks",
            "--fstrikethrough",
            "--ftables",
            "--ftasklists",
            "--funderline",
            "--fwiki-links",
            "--fno-html-blocks",
            "--fno-html-spans",
            "--fno-html",
            "--fno-indented-code",
            "--fverbatim-entities",
        ]:
            markdown_flags.append(arg)
            i += 1
        elif arg.startswith("-"):
            print(f"Unknown option: {arg}", file=sys.stderr)
            usage_md2docx()
        else:
            files.append(arg)
            i += 1

    if not files:
        usage_md2docx()

    md2docx(
        [Path(f) for f in files],
        dialect=dialect,
        markdown_flags=markdown_flags,
        reference_doc=reference_doc,
    )
