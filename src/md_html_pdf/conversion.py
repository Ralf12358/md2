import subprocess
from pathlib import Path
from . import runtime as rt
import os


def md_to_html(
    input_paths,
    css=None,
    dialect="pandoc",
    markdown_flags=None,
    html_title=None,
    html_css=None,
    runtime=None,
    ensure=True,
    self_contained=True,  # Default True: embeds MathJax + resources for offline use
):
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
        rt.ensure_image(runtime, rt.project_root())

    results = []
    for p in input_paths:
        p = Path(p).resolve()
        abs_in = p.resolve()
        out_abs = abs_in.with_suffix(".html")
        in_dir = abs_in.parent
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
        cmd += ["-v", f"{in_dir}:/work", "-v", f"{_styles_dir()}:/styles:ro"]
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

        inner = ["/usr/local/bin/md2html.sh", container_in, container_out]
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

        # Add HTML options
        if html_title:
            inner.extend([f"--html-title={html_title}"])
        if html_css:
            inner.extend([f"--html-css={html_css}"])

        cmd += inner
        subprocess.run(cmd, check=True)
        results.append(out_abs)
    return results


def html_to_pdf(input_paths, runtime=None, ensure=True):
    runtime = runtime or rt.get_container_runtime()
    if ensure:
        rt.ensure_image(runtime, rt.project_root())

    results = []
    for p in input_paths:
        p = Path(p).resolve()
        in_dir = p.parent
        out_pdf = p.with_suffix(".pdf")
        cmd = (
            [runtime, "run", "--rm"]
            + rt.get_user_args(runtime)
            + [
                "-v",
                f"{in_dir}:/work",
                rt.IMAGE_NAME,
                "node",
                "/app/print.js",
                f"/work/{p.name}",
                f"/work/{out_pdf.name}",
            ]
        )
        subprocess.run(cmd, check=True)
        results.append(out_pdf)
    return results


def md_to_pdf(
    input_paths,
    css=None,
    dialect="pandoc",
    markdown_flags=None,
    html_title=None,
    html_css=None,
    runtime=None,
    ensure=True,
    self_contained=True,  # Default True: embeds MathJax + resources for offline use
):
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
        rt.ensure_image(runtime, rt.project_root())

    results = []
    for p in input_paths:
        p = Path(p).resolve()
        abs_in = p.resolve()
        out_abs = abs_in.with_suffix(".pdf")
        in_dir = abs_in.parent
        container_in = f"/work/{abs_in.name}"
        container_html = f"/tmp/{abs_in.stem}.html"
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
        cmd += ["-v", f"{in_dir}:/work", "-v", f"{_styles_dir()}:/styles:ro"]
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

        # Build the command to run both conversions in sequence
        md2html_cmd = ["/usr/local/bin/md2html.sh", container_in, container_html]
        if css_arg:
            md2html_cmd.append(css_arg)

        # Add dialect options
        if dialect == "github":
            md2html_cmd.extend(["--github"])
        elif dialect == "commonmark":
            md2html_cmd.extend(["--commonmark"])
        elif dialect == "pandoc":
            pass

        # Add markdown flags
        if markdown_flags:
            md2html_cmd.extend(markdown_flags)

        # Add HTML options
        if html_title:
            md2html_cmd.extend([f"--html-title={html_title}"])
        if html_css:
            md2html_cmd.extend([f"--html-css={html_css}"])

        # Chain commands: md->html, then html->pdf
        inner_cmd = " && ".join(
            [
                " ".join(md2html_cmd),
                f"node /app/print.js {container_html} {container_out}",
            ]
        )

        cmd += ["sh", "-c", inner_cmd]
        subprocess.run(cmd, check=True)
        results.append(out_abs)
    return results


def _styles_dir():
    return rt.project_root() / "styles"
