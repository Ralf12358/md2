import subprocess
import re
import shutil
from pathlib import Path
from typing import List, Optional, Set, Tuple, Union
from . import runtime as rt
import os


def collect_local_images(file_path: str | Path) -> set[Path]:
    """
    Extract unique local image paths referenced in a markdown file.
    Returns a set of absolute paths to existing image files.
    """
    file_path = Path(file_path).resolve()
    base_dir = file_path.parent
    images: set[Path] = set()

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Match markdown image syntax: ![alt](path) and ![alt](path "title")
        # Also match HTML img tags: <img src="path" ...>
        md_pattern = r'!\[[^\]]*\]\(([^)\s"]+)'
        html_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'

        paths = re.findall(md_pattern, content)
        paths += re.findall(html_pattern, content, re.IGNORECASE)

        for img_path in paths:
            # Skip URLs
            if img_path.startswith(("http://", "https://", "data:")):
                continue

            img = Path(img_path)
            if img.is_absolute():
                if img.exists():
                    images.add(img.resolve())
            else:
                resolved = (base_dir / img).resolve()
                if resolved.exists():
                    images.add(resolved)

    except Exception:
        pass

    return images


def copy_images_and_rewrite(
    content: str, base_dir: Path, target_dir: Path
) -> tuple[str, list[Path]]:
    """
    Copy external images to target_dir and rewrite paths in content.
    Returns (modified_content, list_of_copied_files).
    """
    copied: list[Path] = []

    # Collect all image references
    md_pattern = r'!\[([^\]]*)\]\(([^)\s"]+)'

    def md_replace(m):
        alt = m.group(1)
        img_path = m.group(2)

        # Skip URLs
        if img_path.startswith(("http://", "https://", "data:")):
            return m.group(0)

        img = Path(img_path)
        if img.is_absolute():
            src = img
        else:
            src = (base_dir / img).resolve()

        # Check if image is outside the target directory
        try:
            src.relative_to(target_dir)
            # Already in target dir, keep as-is but make relative
            rel = src.relative_to(target_dir)
            return f"![{alt}]({rel})"
        except ValueError:
            pass  # Outside target dir, need to copy

        if not src.exists():
            return m.group(0)  # Keep original if not found

        # Copy to target dir with unique name if needed
        dest_name = src.name
        dest = target_dir / dest_name
        counter = 1
        while dest.exists() and dest not in copied:
            stem = src.stem
            suffix = src.suffix
            dest_name = f"{stem}_{counter}{suffix}"
            dest = target_dir / dest_name
            counter += 1

        if dest not in copied:
            shutil.copy2(src, dest)
            copied.append(dest)

        return f"![{alt}]({dest_name})"

    content = re.sub(md_pattern, md_replace, content)

    # Also handle HTML img tags
    html_pattern = r'(<img[^>]+src=["\'])([^"\']+)(["\'][^>]*>)'

    def html_replace(m):
        prefix = m.group(1)
        img_path = m.group(2)
        suffix = m.group(3)

        if img_path.startswith(("http://", "https://", "data:")):
            return m.group(0)

        img = Path(img_path)
        if img.is_absolute():
            src = img
        else:
            src = (base_dir / img).resolve()

        try:
            src.relative_to(target_dir)
            rel = src.relative_to(target_dir)
            return f"{prefix}{rel}{suffix}"
        except ValueError:
            pass

        if not src.exists():
            return m.group(0)

        dest_name = src.name
        dest = target_dir / dest_name
        counter = 1
        while dest.exists() and dest not in copied:
            stem = src.stem
            suffix_ext = src.suffix
            dest_name = f"{stem}_{counter}{suffix_ext}"
            dest = target_dir / dest_name
            counter += 1

        if dest not in copied:
            shutil.copy2(src, dest)
            copied.append(dest)

        return f"{prefix}{dest_name}{suffix}"

    content = re.sub(html_pattern, html_replace, content, flags=re.IGNORECASE)

    return content, copied


def count_h1_headers(file_path: str | Path) -> int:
    """Count the number of H1 headers in a markdown file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Count ATX-style headers (# Header)
        atx_count = len(re.findall(r"^# .*$", content, re.MULTILINE))

        # Count Setext-style headers (underlined with =)
        setext_count = len(re.findall(r"^.+\n=+\s*$", content, re.MULTILINE))

        return atx_count + setext_count
    except Exception:
        return 0


def extract_first_h1_title(file_path: str | Path) -> str | None:
    """Extract the text of the first H1 header in a markdown file."""
    try:
        with open(file_path, encoding="utf-8") as f:
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


def shift_headings_and_add_title(file_path: str | Path, title: str) -> str:
    """
    Shift all headings down by one level and add a title H1 at the top.
    Returns the modified markdown content.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Remove trailing spaces before --- to prevent Setext heading misinterpretation
        # This prevents Pandoc from treating "text\n---" as a Setext H1 heading
        lines = content.split("\n")
        processed_lines = []
        for i, line in enumerate(lines):
            processed_lines.append(line)
            # If next line is exactly "---" (a thematic break), remove trailing spaces from current line
            if (
                i < len(lines) - 1
                and lines[i + 1].strip() == "---"
                and line.endswith((" ", "\t"))
            ):
                processed_lines[-1] = line.rstrip()
        content = "\n".join(processed_lines)

        # Shift ATX-style headers (add one # to each)
        content = re.sub(r"^(#{1,6}) ", r"#\1 ", content, flags=re.MULTILINE)

        # Shift Setext-style headers (convert to ATX and shift)
        # H1 (===) becomes H2 (##)
        content = re.sub(r"^(.+)\n=+\s*$", r"## \1", content, flags=re.MULTILINE)
        # H2 (---) becomes H3 (###)
        content = re.sub(r"^(.+)\n-+\s*$", r"### \1", content, flags=re.MULTILINE)

        # Ensure no heading immediately follows ---
        # This prevents Pandoc from misinterpreting --- as a table separator
        content = re.sub(r"^---\n(#{1,6} )", r"---\n\n\1", content, flags=re.MULTILINE)

        # Add title H1 at the top
        modified_content = f"# {title}\n\n{content}"

        return modified_content

    except Exception:
        # If anything fails, return original content
        with open(file_path, encoding="utf-8") as f:
            return f.read()


def determine_document_title(
    file_path: str | Path, title_override: str | None = None
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
    input_paths: list[str | Path],
    css: str | None = None,
    dialect: str = "pandoc",
    markdown_flags: list[str] | None = None,
    html_title: str | None = None,
    title: str | None = None,
    html_css: str | None = None,
    runtime: str | None = None,
    ensure: bool = True,
    self_contained: bool = True,  # Default True: embeds MathJax + resources for offline use
    add_toc_placeholders: bool = False,
) -> list[Path]:

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
        with open(abs_in, encoding="utf-8") as f:
            content = f.read()

        # Only validate if there are HTTP/HTTPS images
        if re.search(r"!\[[^\]]*\]\([^)]*https?://[^)]+\)", content):
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
                f"/work/{abs_in.name}",
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
        copied_images: list[Path] = []

        # Check if we need to copy external images or shift headings
        external_images = collect_local_images(abs_in)
        external_images = {
            img for img in external_images if not str(img).startswith(str(in_dir))
        }

        if h1_count > 1 or external_images:
            import uuid

            if h1_count > 1:
                modified_content = shift_headings_and_add_title(abs_in, actual_title)
            else:
                modified_content = content  # already read above

            # Copy external images to work dir and rewrite paths
            if external_images:
                modified_content, copied_images = copy_images_and_rewrite(
                    modified_content, abs_in.parent, in_dir
                )

            temp_name = f"tmp_{uuid.uuid4().hex[:8]}.md"
            temp_file = in_dir / temp_name
            temp_file.write_text(modified_content, encoding="utf-8")
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

        # Clean up temporary file and copied images
        if temp_file and temp_file.exists():
            temp_file.unlink()
        for img in copied_images:
            if img.exists():
                img.unlink()

        results.append(out_abs)
    return results


def html2pdf(
    input_paths: list[str | Path],
    runtime: str | None = None,
    ensure: bool = True,
    page_numbers: bool = True,
) -> list[Path]:
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
    input_paths: list[str | Path],
    css: str | None = None,
    dialect: str = "pandoc",
    markdown_flags: list[str] | None = None,
    html_title: str | None = None,
    title: str | None = None,
    html_css: str | None = None,
    runtime: str | None = None,
    ensure: bool = True,
    self_contained: bool = True,  # Default True: embeds MathJax + resources for offline use
    page_numbers: bool = True,
) -> list[Path]:
    # Generate clean HTML first (without TOC placeholders)
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
        add_toc_placeholders=False,  # Keep HTML clean
    )

    # Convert HTML to PDF (container handles all PDF processing including temp files)
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
    input_paths: list[str | Path],
    dialect: str = "pandoc",
    markdown_flags: list[str] | None = None,
    title: str | None = None,
    reference_doc: str | Path | None = None,
    runtime: str | None = None,
    ensure: bool = True,
) -> list[Path]:
    if markdown_flags is None:
        markdown_flags = ["--toc"]

    processed_flags: list[str] = []
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

    results: list[Path] = []
    for p in input_paths:
        p = Path(p).resolve()
        abs_in = p.resolve()
        out_abs = abs_in.with_suffix(".docx")
        in_dir = abs_in.parent

        # Determine the actual title to use
        actual_title = determine_document_title(abs_in, title)

        container_in = f"/work/{abs_in.name}"
        container_out = f"/work/{out_abs.name}"

        cmd = [runtime, "run", "--rm"]
        cmd += rt.get_user_args(runtime)
        cmd += rt.get_security_args(runtime)

        mounts = [
            "-v",
            f"{in_dir}:/work",
            "-v",
            f"{rt.PROJECT_ROOT}/styles:/styles:ro",
            "-v",
            f"{rt.PROJECT_ROOT}/filters:/filters:ro",
            "-v",
            f"{rt.PROJECT_ROOT}/scripts:/scripts:ro",
        ]

        if reference_doc:
            ref_abs = Path(reference_doc).resolve()
            mounts += ["-v", f"{ref_abs.parent}:/ref:ro"]
            cmd += ["-e", f"REFERENCE_DOC=/ref/{ref_abs.name}"]

        cmd += mounts

        if os.environ.get("DOCX_SVG") is not None:
            cmd += ["-e", f"DOCX_SVG={os.environ['DOCX_SVG']}"]

        cmd.append(rt.IMAGE_NAME)

        # Use container script to handle all processing
        inner = [
            "bash",
            "/scripts/md2docx.sh",
            container_in,
            container_out,
            actual_title,
            dialect,
        ]
        # Pass reference doc as explicit pandoc flag so it is visible in the command list/tests
        if reference_doc:
            inner.append(f"--reference-doc=/ref/{ref_abs.name}")
        inner.extend(markdown_flags)

        cmd += inner
        subprocess.run(cmd, check=True)

        results.append(out_abs)

    return results
