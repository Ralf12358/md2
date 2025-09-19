# md2

Markdown → HTML → PDF using Podman or Docker (Pandoc + Mermaid + MathJax + Puppeteer) as a Python library and CLI tools.

Container image builds on-demand (tag: `md2:latest`). Supports both Podman and Docker runtimes with automatic detection. Defaults favor high-fidelity CommonMark-X with useful extensions enabled.

## Core Components

md2 is built on a carefully selected stack of proven open-source tools, containerized for consistent results:

### Document Processing
- **[Pandoc](https://pandoc.org/)** (v3.8): Universal document converter and Markdown parser with extensive format support
- **[MathJax](https://www.mathjax.org/)** (v3.2.2): High-quality mathematical typography and LaTeX math rendering
- **[Mermaid CLI](https://mermaid-js.github.io/mermaid-cli/)** (v11.9.0): Diagram generation from textual descriptions

### PDF Generation
- **[Puppeteer](https://pptr.dev/)** (v24.10.2): Headless Chrome automation for HTML → PDF conversion
- **[Node.js](https://nodejs.org/)** (v22): JavaScript runtime for Puppeteer and print pipeline

### Container Platform
- **[Podman](https://podman.io/)** / **[Docker](https://www.docker.com/)**: Container runtime with automatic detection (prefers Podman)
- **[Debian Bookworm Slim](https://hub.docker.com/_/node)**: Lightweight, stable base image with Node.js

### Python Integration
- **[Python](https://python.org/)** (≥3.10): Host language with minimal dependencies

### Font & Typography
- **DejaVu Fonts**: High-quality, comprehensive Unicode font family
- **Liberation Fonts**: Metric-compatible alternatives for common fonts
- **System Fonts**: Additional font support for diverse character sets

This architecture ensures **reproducible**, **high-quality** document generation across different systems while maintaining **minimal host dependencies**.

## Install (git URL)

Using uv (required):

```sh
uv tool install md2 --from git+https://github.com/Ralf12358/md2.git
```

Or add to a project:

```sh
uv add git+https://github.com/Ralf12358/md2.git
```

## Command Line Usage

### md2html
```sh
md2html file.md
md2html --css styles/custom.css file.md
md2html --github notes.md
md2html --ftables --fstrikethrough file.md
md2html --html-title="My Document" --html-css="custom.css" file.md
md2html a.md b.md c.md
```

### md2pdf (Markdown → HTML → PDF)
```sh
md2pdf doc.md
md2pdf --css styles/custom.css doc.md
md2pdf --github --ftables doc.md
md2pdf --html-title="Report" doc.md
md2pdf --toc-depth=2 doc.md
```

### html2pdf
```sh
html2pdf doc.html other.html
```

### Available Options

Both `md2html` and `md2pdf` support extensive Markdown processing options:

#### Markdown dialect options:
- Default: Pandoc Markdown with useful extensions (math via TeX, smart punctuation, emoji, footnotes, definition lists, fenced code/link attributes, task lists, strikeout, pipe tables, table captions, auto identifiers, implicit header refs).
- `--commonmark` - CommonMark-X (subset; fewer extensions).
- `--github` - GitHub Flavored Markdown (limited extensions; use for strict GFM).

#### Markdown extension options:
- `--fcollapse-whitespace` - Collapse non-trivial whitespace
- `--flatex-math` - Enable LaTeX style mathematics spans
- `--fpermissive-atx-headers` - Allow ATX headers without delimiting space
- `--fpermissive-url-autolinks` - Allow URL autolinks without '<', '>'
- `--fpermissive-www-autolinks` - Allow WWW autolinks without any scheme
- `--fpermissive-email-autolinks` - Allow e-mail autolinks without '<', '>' and 'mailto:'
- `--fpermissive-autolinks` - Enable all permissive autolink options
- `--fhard-soft-breaks` - Force all soft breaks to act as hard breaks
- `--fstrikethrough` - Enable strike-through spans
- `--ftables` - Enable tables
- `--ftasklists` - Enable task lists
- `--funderline` - Enable underline spans
- `--fwiki-links` - Enable wiki links

#### Markdown suppression options:
- `--fno-html-blocks` - Disable raw HTML blocks
- `--fno-html-spans` - Disable raw HTML spans
- `--fno-html` - Same as --fno-html-blocks --fno-html-spans
- `--fno-indented-code` - Disable indented code blocks

#### HTML generator options:
- `--fverbatim-entities` - Do not translate entities
- `--html-title=TITLE` - Sets the title of the document
- `--html-css=URL` - In full HTML or XHTML mode add a css link
- `--css=PATH` - CSS file to use for styling

#### TOC options:
- `--no-toc` - Disable Table of Contents (default: enabled)
- `--toc-depth=N` - Maximum heading depth included in TOC (e.g. 2 or 3)

Behavior notes for TOC:
- TOC is enabled by default. Use `--no-toc` to disable it.
- When TOC is enabled and you did not pass `--css`, the tool automatically styles the TOC using `styles/default.toc.css`.
- The TOC CSS works for both on-screen and print/PDF and adds a German heading label `Inhaltsverzeichnis` above the list.
- If you pass `--css`, your stylesheet is used instead (copy and adapt `styles/default.toc.css` if you want to customize TOC appearance or the heading text).

Behavior notes:
- Default dialect: Pandoc Markdown with extensions listed above.
- **Math rendering**: LaTeX mathematics is rendered via MathJax using high-quality typography. MathJax is always embedded for offline use with proper visual quality (connected lines, well-formed symbols).
- Default stylesheet: `styles/default.css` is applied.
- `--css PATH` uses a custom stylesheet by mounting its directory read-only and referencing it in the HTML.
- **Self-contained mode (default)**: Inlines the main stylesheet and embeds images/fonts via data URIs. Creates completely portable HTML files that work offline.
- Environment variables: `LINK_CSS=1` forces a `<link href="default.css">` next to the HTML; `INTERNAL_RESOURCES=1` embeds external resources (default behavior). `self_contained=True` sets both appropriately.

## Python API

```python
from pathlib import Path
from md_html_pdf import md_to_html, md_to_pdf, html_to_pdf

# Basic usage
html_paths = md_to_html([Path("notes.md")])
pdf_paths = md_to_pdf([Path("notes.md")])
html_to_pdf([Path("already.html")])

# With CSS and dialect
md_to_html([Path("a.md"), Path("b.md")], css=Path("styles/custom.css"), dialect="github")
md_to_pdf([Path("paper.md")], css=Path("styles/custom.css"))

# Self-contained HTML (embeds all images and CSS)
html_paths = md_to_html([Path("document.md")], self_contained=True)
pdf_paths = md_to_pdf([Path("document.md")], self_contained=True)

# With advanced options
md_to_html(
    [Path("doc.md")],
    dialect="github",
    markdown_flags=["--ftables", "--fstrikethrough", "--flatex-math"],
    html_title="My Document",
    html_css="custom.css",
    self_contained=True  # Creates portable single-file HTML
)

md_to_pdf(
    [Path("report.md")],
    css=Path("styles/report.css"),
    markdown_flags=["--fpermissive-autolinks", "--ftasklists"],
    html_title="Monthly Report",
    self_contained=True  # Embeds all resources
)

# Table of Contents via Python API
md_to_html([Path("doc.md")], markdown_flags=["--toc-depth=2"])  # TOC enabled by default, auto-uses styles/default.toc.css when no css passed
md_to_pdf([Path("doc.md")])  # TOC enabled by default and styled in PDF as well
md_to_html([Path("doc.md")], markdown_flags=["--no-toc"])  # Disable TOC
```

Each function returns a list of output paths.

## Math Support

Built-in LaTeX mathematics rendering via MathJax:

- **Inline math**: `$E = mc^2$` renders as inline formula
- **Display math**: `$$\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}$$` renders as centered display formula: $$\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}$$
- **High-quality typography**: Connected lines, properly formed square roots, brackets, and mathematical symbols
- **Always embedded**: MathJax is included in the output for offline use
- **No setup required**: Math rendering works out-of-the-box

Example:
```markdown
# Math Document

The quadratic formula is $x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$.

$$\sum_{n=1}^{\infty} \frac{1}{n^2} = \frac{\pi^2}{6}$$
```

## Self-Contained HTML Generation

When `self_contained=True` is used with `md_to_html()` or `md_to_pdf()` (default behavior):

- **All external images** are downloaded and embedded as base64 data URIs
- **CSS is inlined** into the HTML document
- **MathJax is embedded** for offline math rendering
- **Result is completely portable** - works without internet connection
- **Perfect for archiving** - preserves all visual content permanently
- **Single file sharing** - no missing images or broken layouts

Example use cases:
- Creating documentation archives that work offline
- Generating reports with embedded charts/images
- Sharing documents without external dependencies
- Long-term document preservation

Size impact: Self-contained HTML files are typically 5-10x larger due to embedded images and MathJax.

### API Parameters

- `input_paths`: List of Path objects for input files
- `css`: Optional Path to CSS file for styling
- `dialect`: "pandoc" (default), "commonmark", or "github"
- `markdown_flags`: List of markdown extension/suppression flags
- `html_title`: Optional HTML document title
- `html_css`: Optional CSS URL for HTML mode
- `self_contained`: Boolean (default False) - when True, embeds all external resources (images, CSS) into the output HTML as data URIs, creating a completely portable single-file document
- `runtime`: Optional container runtime (defaults to auto-detected)
- `ensure`: Whether to ensure Docker image exists (default True)

## How It Works
- **Container Runtime**: Automatically detects and uses Podman or Docker (prefers Podman when both are available)
- **Runtime Selection**: Set `RUNTIME=docker` or `RUNTIME=podman` environment variable to force a specific runtime
- **Image Management**: Builds container image if missing (`md2:latest`)
- **Conversion Pipeline**:
  - Runs `/usr/local/bin/md2html.sh` in container for Markdown → HTML conversion
  - Runs `node /app/print.js` for HTML → PDF conversion
- **Networking**: Uses `--network=slirp4netns` for Podman rootless setups to avoid pasta/TUN requirements

## Development

Clone and run tests:
```sh
uv run pytest -q
```

Edit code under `src/md_html_pdf/`. Add tests under `src/tests/md_html_pdf/`.

## Examples
See `examples/` for sample markdown and produced artifacts.

Generate PDF for example:
```sh
md2pdf examples/doc.md
```

Generate with advanced features:
```sh
# GitHub-flavored markdown with tables and task lists
md2pdf --github --ftables --ftasklists examples/doc.md

# Custom title and CSS
md2html --html-title="Documentation" --css styles/custom.css examples/doc.md

# LaTeX math support
md2pdf --flatex-math math-document.md

# Table of Contents (enabled by default)
md2html --toc-depth=3 examples/doc.md
md2pdf examples/doc.md
```

## Troubleshooting
- **Missing runtime**: Install either Docker or Podman (or both). md2 will automatically detect and use the available runtime.
- **Runtime selection**: Use `RUNTIME=docker` or `RUNTIME=podman` environment variable to force a specific container runtime.
- **Podman rootless networking**: This tool uses `--network=slirp4netns` to avoid pasta/TUN requirements. If networking fails, ensure `slirp4netns` is available in your Podman setup.
- **Build failures**: Remove container image `md2:latest` and retry: `podman rmi md2:latest` or `docker rmi md2:latest`.
- **Styling not applied**: Ensure you didn't pass invalid flags; verify the generated HTML has either a `<style>` block (self-contained) or a `<link rel="stylesheet" href="default.css">` next to the file. When using `--css`, confirm the file exists and is mounted.

## License
MIT License. See [LICENSE](LICENSE) file for details.
