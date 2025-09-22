import subprocess
import re
from pathlib import Path
from typing import List, Optional, Union
from . import runtime as rt
import os


def count_h1_headers(file_path: Union[str, Path]) -> int:
    """Count the number of H1 headers in a markdown file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Count ATX-style headers (# Header)
        atx_count = len(re.findall(r"^# .*$", content, re.MULTILINE))

        # Count Setext-style headers (underlined with =)
        setext_count = len(re.findall(r"^.+\n=+\s*$", content, re.MULTILINE))

        return atx_count + setext_count
    except Exception:
        return 0


def extract_first_h1_title(file_path: Union[str, Path]) -> Optional[str]:
    """Extract the text of the first H1 header in a markdown file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Look for ATX-style header first (# Header)
        atx_match = re.search(r"^# (.+)$", content, re.MULTILINE)
        if atx_match:
            return atx_match.group(1).strip()

        # Look for Setext-style header (underlined with =)
        setext_match = re.search(r"^(.+)\n=+\s*$", content, re.MULTILINE)
        if setext_match:
            return setext_match.group(1).strip()

        return None
    except Exception:
        return None


def shift_headings_and_add_title(file_path: Union[str, Path], title: str) -> str:
    """
    Shift all headings down by one level and add a title H1 at the top.
    Returns the modified markdown content.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Shift ATX-style headers (add one # to each)
        content = re.sub(r"^(#{1,6}) ", r"#\1 ", content, flags=re.MULTILINE)

        # Shift Setext-style headers (convert to ATX and shift)
        # H1 (===) becomes H2 (##)
        content = re.sub(r"^(.+)\n=+\s*$", r"## \1", content, flags=re.MULTILINE)
        # H2 (---) becomes H3 (###)
        content = re.sub(r"^(.+)\n-+\s*$", r"### \1", content, flags=re.MULTILINE)

        # Add title H1 at the top
        modified_content = f"# {title}\n\n{content}"

        return modified_content

    except Exception:
        # If anything fails, return original content
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()


def determine_document_title(
    file_path: Union[str, Path], title_override: Optional[str] = None
) -> str:
    """
    Determine the document title based on the following priority:
    1. title_override (--title parameter)
    2. If exactly one H1 header exists, use its text
    3. Otherwise, use the filename stem
    """
    if title_override:
        return title_override

    h1_count = count_h1_headers(file_path)
    if h1_count == 1:
        first_h1 = extract_first_h1_title(file_path)
        if first_h1:
            return first_h1

    # Fallback to filename stem
    return Path(file_path).stem


def md2html(
    input_paths: List[Union[str, Path]],
    css: Optional[str] = None,
    dialect: str = "pandoc",
    markdown_flags: Optional[List[str]] = None,
    html_title: Optional[str] = None,
    title: Optional[str] = None,
    html_css: Optional[str] = None,
    runtime: Optional[str] = None,
    ensure: bool = True,
    self_contained: bool = True,  # Default True: embeds MathJax + resources for offline use
    add_toc_placeholders: bool = False,
) -> List[Path]:

    if markdown_flags is None:
        markdown_flags = ["--toc"]  # TOC enabled by default

    # Process flags to remove --no-toc and ensure --toc is default
    processed_flags = []
    toc_disabled = False
    for flag in markdown_flags:
        if flag == "--no-toc":
            toc_disabled = True
        else:
            processed_flags.append(flag)

    # Add --toc if not disabled and not already present
    if not toc_disabled and "--toc" not in processed_flags:
        processed_flags.insert(0, "--toc")

    # If --no-toc was specified, remove any --toc flags
    if toc_disabled:
        processed_flags = [f for f in processed_flags if f != "--toc"]

    markdown_flags = processed_flags
    runtime = runtime or rt.get_container_runtime()
    if ensure:
        rt.ensure_image(runtime, rt.PROJECT_ROOT)

    results = []
    for p in input_paths:
        p = Path(p).resolve()
        abs_in = p.resolve()

        # Check for remote images and validate if present
        with open(abs_in, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Only validate if there are HTTP/HTTPS images
        if re.search(r'!\[[^\]]*\]\([^)]*https?://[^)]+\)', content):
            scripts_path = Path(__file__).parent / "scripts"
            validation_cmd = [
                runtime,
                "run",
                "--rm",
                "--userns=keep-id",
                "--network=host",
                "-v",
                f"{abs_in.parent}:/work:ro",
                "-v",
                f"{scripts_path}:/scripts:ro",
                "md2:latest",
                "python3",
                "/scripts/validate_images.py",
                f"/work/{abs_in.name}"
            ]
            
            try:
                subprocess.run(validation_cmd, check=False, capture_output=False)
            except Exception:
                pass

        out_abs = abs_in.with_suffix(".html")
        in_dir = abs_in.parent

        # Determine the actual title to use
        actual_title = determine_document_title(abs_in, title)

        # Handle multiple H1s by shifting headings and adding title
        h1_count = count_h1_headers(abs_in)
        temp_file = None
        if h1_count > 1:
            # Create temporary file with shifted headings in container
            modified_content = shift_headings_and_add_title(abs_in, actual_title)
            import uuid

            temp_name = f"tmp_{uuid.uuid4().hex[:8]}.md"
            temp_file = in_dir / temp_name
            temp_file.write_text(modified_content, encoding="utf-8")

            # Use the temporary file for conversion
            container_in = f"/work/{temp_name}"
        else:
            container_in = f"/work/{abs_in.name}"

        container_out = f"/work/{out_abs.name}"

        css_mount = []
        css_arg = None
        toc_enabled = bool(markdown_flags and any(f == "--toc" for f in markdown_flags))
        if css:
            css_abs = Path(css).resolve()
            css_mount = ["-v", f"{css_abs.parent}:/custom-styles:ro"]
            css_arg = f"/custom-styles/{css_abs.name}"
        elif toc_enabled:
            css_arg = "/styles/default.toc.css"

        cmd = [runtime, "run", "--rm"]
        cmd += rt.get_user_args(runtime)
        cmd += rt.get_security_args(runtime)
        cmd += [
            "-v",
            f"{in_dir}:/work",
            "-v",
            f"{rt.PROJECT_ROOT}/styles:/styles:ro",
            "-v",
            f"{rt.PROJECT_ROOT}/filters:/filters:ro",
            "-v",
            f"{rt.PROJECT_ROOT}/scripts:/scripts:ro",
        ]
        cmd += css_mount
        if self_contained:
            cmd += ["-e", "INTERNAL_RESOURCES=1", "-e", "LINK_CSS=0"]
        else:
            link_css = os.environ.get("LINK_CSS")
            internal = os.environ.get("INTERNAL_RESOURCES")
            if link_css is not None:
                cmd += ["-e", f"LINK_CSS={link_css}"]
            if internal is not None:
                cmd += ["-e", f"INTERNAL_RESOURCES={internal}"]
        cmd.append(rt.IMAGE_NAME)

        inner = ["bash", "/scripts/md2html.sh", container_in, container_out]
        if css_arg:
            inner.append(css_arg)

        # Add dialect options
        if dialect == "github":
            inner.extend(["--github"])
        elif dialect == "commonmark":
            inner.extend(["--commonmark"])
        elif dialect == "pandoc":
            # default in script; no flag needed
            pass

        # Add markdown flags
        if markdown_flags:
            inner.extend(markdown_flags)

        # Add HTML options - priority: title > html_title > auto-detected title
        if title:
            # --title overrides everything for HTML title
            inner.extend([f"--html-title={actual_title}"])
        elif html_title:
            # --html-title only overrides auto-detection if --title not specified
            inner.extend([f"--html-title={html_title}"])
        else:
            # Use auto-detected title
            inner.extend([f"--html-title={actual_title}"])

        # Pass the determined title for other purposes (like PDF titles)
        inner.extend([f"--doc-title={actual_title}"])

        if html_css:
            inner.extend([f"--html-css={html_css}"])

        # Add TOC placeholders flag if needed
        if add_toc_placeholders:
            inner.extend(["--add-toc-placeholders"])

        cmd += inner
        subprocess.run(cmd, check=True)

        # Clean up temporary file if created
        if temp_file and temp_file.exists():
            temp_file.unlink()

        results.append(out_abs)
    return results


def html2pdf(
    input_paths: List[Union[str, Path]],
    runtime: Optional[str] = None,
    ensure: bool = True,
    page_numbers: bool = True,
) -> List[Path]:
    runtime = runtime or rt.get_container_runtime()
    if ensure:
        rt.ensure_image(runtime, rt.PROJECT_ROOT)

    results = []
    for p in input_paths:
        p = Path(p).resolve()
        in_dir = p.parent
        out_pdf = p.with_suffix(".pdf")

        # Use unified container script for HTML->PDF conversion and processing
        cmd = (
            [runtime, "run", "--rm"]
            + rt.get_user_args(runtime)
            + [
                "-v",
                f"{in_dir}:/work",
                "-v",
                f"{rt.PROJECT_ROOT}/scripts:/scripts:ro",
                rt.IMAGE_NAME,
                "bash",
                "/scripts/pdf_generator.sh",
                f"/work/{p.name}",
                f"/work/{out_pdf.name}",
                str(page_numbers).lower(),
            ]
        )
        subprocess.run(cmd, check=True)

        results.append(out_pdf)
    return results


def md2pdf(
    input_paths: List[Union[str, Path]],
    css: Optional[str] = None,
    dialect: str = "pandoc",
    markdown_flags: Optional[List[str]] = None,
    html_title: Optional[str] = None,
    title: Optional[str] = None,
    html_css: Optional[str] = None,
    runtime: Optional[str] = None,
    ensure: bool = True,
    self_contained: bool = True,  # Default True: embeds MathJax + resources for offline use
    page_numbers: bool = True,
) -> List[Path]:
    # Generate HTML with TOC placeholders if page numbers are enabled
    html_paths = md2html(
        input_paths=input_paths,
        css=css,
        dialect=dialect,
        markdown_flags=markdown_flags,
        html_title=html_title,
        title=title,
        html_css=html_css,
        runtime=runtime,
        ensure=ensure,
        self_contained=self_contained,
        add_toc_placeholders=page_numbers,  # Add placeholders if page numbers enabled
    )

    # Convert HTML to PDF (container handles all PDF processing)
    pdf_paths = html2pdf(
        html_paths,
        runtime=runtime,
        ensure=False,
        page_numbers=page_numbers,
    )

    return pdf_paths


def _styles_dir() -> Path:
    return rt.PROJECT_ROOT / "styles"


def md2docx(
    input_paths: List[Union[str, Path]],
    dialect: str = "pandoc",
    markdown_flags: Optional[List[str]] = None,
    title: Optional[str] = None,
    reference_doc: Optional[Union[str, Path]] = None,
    runtime: Optional[str] = None,
    ensure: bool = True,
) -> List[Path]:
    if markdown_flags is None:
        markdown_flags = ["--toc"]

    processed_flags: List[str] = []
    toc_disabled = False
    for flag in markdown_flags:
        if flag == "--no-toc":
            toc_disabled = True
        else:
            processed_flags.append(flag)
    if not toc_disabled and "--toc" not in processed_flags:
        processed_flags.insert(0, "--toc")
    if toc_disabled:
        processed_flags = [f for f in processed_flags if f != "--toc"]

    markdown_flags = processed_flags
    runtime = runtime or rt.get_container_runtime()
    if ensure:
        rt.ensure_image(runtime, rt.PROJECT_ROOT)

    results: List[Path] = []
    for p in input_paths:
        p = Path(p).resolve()
        abs_in = p.resolve()
        out_abs = abs_in.with_suffix(".docx")
        in_dir = abs_in.parent

        # Determine the actual title to use
        actual_title = determine_document_title(abs_in, title)

        # Handle multiple H1s by shifting headings and adding title
        h1_count = count_h1_headers(abs_in)
        temp_file = None
        if h1_count > 1:
            # Create temporary file with shifted headings in container
            modified_content = shift_headings_and_add_title(abs_in, actual_title)
            import uuid

            temp_name = f"tmp_{uuid.uuid4().hex[:8]}.md"
            temp_file = in_dir / temp_name
            temp_file.write_text(modified_content, encoding="utf-8")

            # Use the temporary file for conversion
            container_in = f"/work/{temp_name}"
        else:
            container_in = f"/work/{abs_in.name}"

        container_out = f"/work/{out_abs.name}"

        cmd = [runtime, "run", "--rm"]
        cmd += rt.get_user_args(runtime)
        mounts = [
            "-v",
            f"{in_dir}:/work",
            "-v",
            f"{_styles_dir()}:/styles:ro",
            "-v",
            f"{rt.PROJECT_ROOT}/filters:/filters:ro",
        ]
        if reference_doc:
            ref_abs = Path(reference_doc).resolve()
            mounts += ["-v", f"{ref_abs.parent}:/ref:ro"]
        cmd += mounts
        if os.environ.get("DOCX_SVG") is not None:
            cmd += ["-e", f"DOCX_SVG={os.environ['DOCX_SVG']}"]
        cmd.append(rt.IMAGE_NAME)

        if dialect == "github":
            input_format = "gfm+tex_math_dollars+emoji+footnotes+task_lists+strikeout"
        elif dialect == "commonmark":
            input_format = "commonmark_x+tex_math_dollars+tex_math_single_backslash+smart+emoji+footnotes+definition_lists+fenced_code_attributes+link_attributes+task_lists+strikeout+pipe_tables+table_captions"
        else:
            input_format = "markdown+tex_math_dollars+tex_math_single_backslash+smart+emoji+footnotes+definition_lists+fenced_code_attributes+link_attributes+task_lists+strikeout+pipe_tables+table_captions+auto_identifiers+implicit_header_references"

        inner = [
            "pandoc",
            "-f",
            input_format,
            "-t",
            "docx",
            "--standalone",
            "--resource-path=/work:/styles:/tmp",
            "--lua-filter=/filters/mermaid.lua",
        ]
        inner += list(markdown_flags or [])

        # Set document title
        inner += ["--metadata=title:" + actual_title]

        inner += [container_in, "-o", container_out]
        if reference_doc:
            inner += ["--reference-doc=/ref/" + Path(reference_doc).resolve().name]

        cmd += inner
        subprocess.run(cmd, check=True)

        # Clean up temporary file if created
        if temp_file and temp_file.exists():
            temp_file.unlink()

        results.append(out_abs)

    return results
