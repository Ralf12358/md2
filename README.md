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
md2html --title="Custom Title" file.md  # Override automatic title detection
md2html a.md b.md c.md
```

### md2pdf (Markdown → HTML → PDF)
```sh
md2pdf doc.md
md2pdf --css styles/custom.css doc.md
md2pdf --github --ftables doc.md
md2pdf --html-title="Report" doc.md
md2pdf --title="Annual Report 2025" doc.md  # Override automatic title detection
md2pdf --toc-depth=2 doc.md
md2pdf --no-page-numbers doc.md  # Disable page numbers (enabled by default)
```

#### TOC Page Numbers (PDF only)
- Page numbers in the Table of Contents are applied during the PDF post-processing step only.
- HTML output never displays page numbers in the TOC or on pages.
- The tool temporarily inserts invisible placeholder tags during printing, then restores the original HTML.
- TOC entries remain clickable links; we avoid redactions to preserve link annotations.
- Disable via `--no-page-numbers`.

### md2docx (Markdown → DOCX)
```sh
md2docx doc.md
md2docx --reference-doc styles/reference.docx doc.md
md2docx --title="Professional Report" doc.md  # Override automatic title detection
md2docx --github --no-toc doc.md
md2docx --commonmark doc.md
md2docx a.md b.md c.md
```

### html2pdf
```sh
html2pdf doc.html other.html
html2pdf --no-page-numbers doc.html  # Disable page numbers (enabled by default)
```

### Available Options

Both `md2html`, `md2pdf`, and `md2docx` support extensive Markdown processing options:

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
- `--html-title=TITLE` - Sets the HTML title of the document (overridden by --title)
- `--title=TITLE` - Sets the document title (overrides automatic detection and --html-title)
- `--html-css=URL` - In full HTML or XHTML mode add a css link
- `--css=PATH` - CSS file to use for styling

#### TOC options:
- `--no-toc` - Disable Table of Contents (default: enabled)
- `--toc-depth=N` - Maximum heading depth included in TOC (e.g. 2 or 3)

#### DOCX-specific options (md2docx only):
- `--reference-doc=PATH` - Use a Word reference template for styling

#### Title Handling:
The document title is determined automatically based on the source document structure:

- **Single H1 header**: Uses the H1 text as the document title
- **Multiple H1 headers**: Uses the filename (without extension) as the document title and restructures the document:
  - All existing headings are shifted down one level (H1→H2, H2→H3, etc.)
  - A new H1 title is added at the top with the determined title
  - This ensures proper document hierarchy and complete table of contents
- **--title override**: The `--title` option always overrides automatic detection and `--html-title`
- **--html-title**: Only affects HTML title when `--title` is not specified

Examples:
```markdown
# My Document Title
## Section 1
## Section 2
```
→ Title: "My Document Title" (from H1), structure unchanged

```markdown
# Chapter 1
## Section A
# Chapter 2
## Section B
```
→ Title: "filename" (from filename), structure becomes:
```markdown
# filename
## Chapter 1
### Section A
## Chapter 2
### Section B
```

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
from md2 import md2html, md2pdf, html2pdf, md2docx

# Basic usage
html_paths = md2html([Path("notes.md")])
pdf_paths = md2pdf([Path("notes.md")])
docx_paths = md2docx([Path("notes.md")])
html2pdf([Path("already.html")])

# With CSS and dialect
md2html([Path("a.md"), Path("b.md")], css=Path("styles/custom.css"), dialect="github")
md2pdf([Path("paper.md")], css=Path("styles/custom.css"))

# PDF with/without page numbers
md2pdf([Path("document.md")])  # Page numbers enabled by default
md2pdf([Path("document.md")], page_numbers=False)  # Disable page numbers
html2pdf([Path("document.html")], page_numbers=True)  # Enable page numbers

# Note: TOC page numbers are only rendered in PDF, never in HTML.

# DOCX with reference template (custom styling)
md2docx([Path("paper.md")], reference_doc="styles/reference.docx", dialect="github")

# DOCX with different reference templates
md2docx([Path("report.md")], reference_doc="styles/corporate-template.docx")
md2docx([Path("manual.md")], reference_doc="styles/technical-docs.docx")

# Self-contained HTML (embeds all images and CSS)
html_paths = md2html([Path("document.md")], self_contained=True)
pdf_paths = md2pdf([Path("document.md")], self_contained=True)

# With advanced options
md2html(
    [Path("doc.md")],
    dialect="github",
    markdown_flags=["--ftables", "--fstrikethrough", "--flatex-math"],
    html_title="My Document",
    title="Override Title",  # Overrides automatic detection and html_title
    html_css="custom.css",
    self_contained=True  # Creates portable single-file HTML
)

md2pdf(
    [Path("report.md")],
    css=Path("styles/report.css"),
    markdown_flags=["--fpermissive-autolinks", "--ftasklists"],
    title="Annual Report 2025",  # Override automatic title detection
    self_contained=True  # Embeds all resources
)

# Table of Contents via Python API
md2html([Path("doc.md")], markdown_flags=["--toc-depth=2"])  # TOC enabled by default, auto-uses styles/default.toc.css when no css passed
md2pdf([Path("doc.md")])  # TOC enabled by default and styled in PDF as well
md2html([Path("doc.md")], markdown_flags=["--no-toc"])  # Disable TOC
```

Each function returns a list of output paths.

## DOCX (Word Document) Support

Convert Markdown to Microsoft Word documents with full support for diagrams and math:

```python
# Basic DOCX conversion
docx_paths = md2docx([Path("document.md")])

# With custom styling using Word reference template
md2docx(
    [Path("report.md")],
    reference_doc="styles/reference.docx",
    dialect="github",
    markdown_flags=["--no-toc"]
)
```

### DOCX Features
- **Mermaid diagrams**: Rendered as PNG (default) for LibreOffice compatibility, or SVG for modern Word
- **LaTeX math**: Converted to native Word equations (OMML format)
- **Custom styling**: Use Word reference templates to control fonts, headings, and formatting
- **Table of Contents**: Enabled by default, customizable depth

### Mermaid in DOCX
```bash
# Default: PNG for maximum compatibility
md2docx document.md

# SVG for modern Word (better quality)
DOCX_SVG=1 md2docx document.md
```

### Styling DOCX Output

#### Creating a Reference Template

##### Method 1: Generate Pandoc's Default Template
```bash
# Generate Pandoc's default reference template
podman run --rm --userns=keep-id --network=host \
  -v "$PWD:/work" md2:latest \
  pandoc --print-default-data-file reference.docx > styles/reference.docx

# Use the reference template
md2docx --reference-doc=styles/reference.docx document.md
```

##### Method 2: Copy Styles from Existing DOCX
```bash
# Use any existing Word document as a style reference
cp existing-document.docx styles/my-reference.docx
md2docx --reference-doc=styles/my-reference.docx document.md
```

##### Method 3: Create from Scratch in Word/LibreOffice
1. Create a new document in Microsoft Word or LibreOffice Writer
2. Define all the styles you want (see customization section below)
3. Save as `reference.docx`
4. Use with `--reference-doc=path/to/reference.docx`

#### Customizing the Reference Template

Open `reference.docx` in Word/LibreOffice and customize these critical styles:

**Essential Styles to Customize:**
- **Normal**: Base paragraph style (font, size, spacing, color)
- **Heading 1, 2, 3, 4, 5, 6**: Chapter/section headings (fonts, sizes, colors, numbering)
- **Title**: Document title style
- **Subtitle**: Document subtitle style
- **First Paragraph**: Style for the first paragraph after headings
- **Block Text**: Blockquotes and indented content
- **Source Code**: Code blocks and inline code formatting

**Advanced Styles:**
- **Table Grid**: Table appearance, borders, cell padding
- **Caption**: Figure and table captions
- **List Paragraph**: Bulleted and numbered lists
- **List Number**, **List Number 2**, etc.: Multi-level numbering
- **List Bullet**, **List Bullet 2**, etc.: Multi-level bullets
- **Hyperlink**: Link colors and formatting
- **Footnote Text**: Footnote appearance

**Mathematical Content:**
- LaTeX math is automatically converted to Word's native equation format (OMML)
- Math formatting inherits from the surrounding text style
- For custom math appearance, modify the paragraph styles where math appears

#### Style Inheritance and Best Practices

1. **Start with Normal style**: All other styles typically inherit from "Normal"
2. **Use style inheritance**: Define common properties in Normal, override specific properties in other styles
3. **Test with sample content**: Create a test document with headers, code, tables, lists, and math
4. **Font considerations**:
   - Use fonts available on target systems
   - Liberation and DejaVu fonts are included in the container
   - Avoid proprietary fonts unless you know they're available
5. **Page layout**: Set margins, page size, headers/footers in the reference document

#### Example Workflow

```bash
# 1. Generate base template
md2docx --reference-doc=styles/reference.docx sample.md

# 2. Open styles/reference.docx in Word/LibreOffice
# 3. Modify styles as needed
# 4. Save the reference document
# 5. Use your customized template
md2docx --reference-doc=styles/reference.docx my-document.md
```

#### Using Corporate/Brand Templates

To use your organization's document template:

```bash
# Copy your corporate template
cp /path/to/corporate-template.docx styles/company-brand.docx

# Use it for conversions
md2docx --reference-doc=styles/company-brand.docx report.md
```

**Note**: The reference document's content is ignored; only the styles are applied to the converted Markdown content.

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

When `self_contained=True` is used with `md2html()` or `md2pdf()` (default behavior):

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
- `css`: Optional Path to CSS file for styling (HTML/PDF only)
- `dialect`: "pandoc" (default), "commonmark", or "github"
- `markdown_flags`: List of markdown extension/suppression flags
- `html_title`: Optional HTML document title (HTML/PDF only, overridden by `title`)
- `title`: Optional document title that overrides automatic detection and `html_title` (all formats)
- `html_css`: Optional CSS URL for HTML mode (HTML/PDF only)
- `reference_doc`: Optional Path to Word reference template for styling (DOCX only)
- `self_contained`: Boolean (default False) - when True, embeds all external resources (images, CSS) into the output HTML as data URIs, creating a completely portable single-file document (HTML/PDF only)
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

Edit code under `src/md2/`. Add tests under `src/tests/md2/`.

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
md2html --title="Complete Documentation" --css styles/custom.css examples/doc.md
md2html --html-title="Documentation" --css styles/custom.css examples/doc.md

# LaTeX math support
md2pdf --flatex-math math-document.md

# DOCX with custom styling
md2docx --reference-doc=styles/reference.docx examples/doc.md

# DOCX with corporate template
md2docx --reference-doc=styles/corporate-brand.docx examples/doc.md

# Table of Contents (enabled by default)
md2html --toc-depth=3 examples/doc.md
md2pdf examples/doc.md
md2docx --no-toc examples/doc.md
```

## Troubleshooting
- **Missing runtime**: Install either Docker or Podman (or both). md2 will automatically detect and use the available runtime.
- **Runtime selection**: Use `RUNTIME=docker` or `RUNTIME=podman` environment variable to force a specific container runtime.
- **Podman rootless networking**: This tool uses `--network=slirp4netns` to avoid pasta/TUN requirements. If networking fails, ensure `slirp4netns` is available in your Podman setup.
- **Build failures**: Remove container image `md2:latest` and retry: `podman rmi md2:latest` or `docker rmi md2:latest`.
- **Styling not applied**: Ensure you didn't pass invalid flags; verify the generated HTML has either a `<style>` block (self-contained) or a `<link rel="stylesheet" href="default.css">` next to the file. When using `--css`, confirm the file exists and is mounted.

## License
MIT License. See [LICENSE](LICENSE) file for details.
