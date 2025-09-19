#!/usr/bin/env bash
set -euo pipefail

# CRITICAL: Math rendering quality depends on using the specific MathJax file
# --mathjax=/mathjax/tex-svg-full.js provides high-quality rendering (connected lines, proper symbols)
# DO NOT change to generic --mathjax flag as it causes visual rendering issues (broken sqrt, brackets)
# The specific file is installed in the container at /mathjax/tex-svg-full.js

IN="${1:-/work/input.md}"
OUT="${2:-/work/output.html}"
CSS_BASENAME="default.css"
BASE_NAME="$(basename "$IN")"
PAGE_TITLE="${BASE_NAME%.*}"

# LINK_CSS=1 externalizes only the main stylesheet (other assets unaffected)
LINK_CSS="${LINK_CSS:-0}"
# INTERNAL_RESOURCES=1 embeds images/fonts/etc. (default = external references)
INTERNAL_RESOURCES="${INTERNAL_RESOURCES:-0}"

# Parse additional arguments for format and HTML options
# Default to a rich Pandoc Markdown with helpful extensions for best results
# Users can override with --github or --commonmark flags
INPUT_FORMAT="markdown+tex_math_dollars+tex_math_single_backslash+smart+emoji+footnotes+definition_lists+fenced_code_attributes+link_attributes+task_lists+strikeout+pipe_tables+table_captions+auto_identifiers+implicit_header_references"
EXTRA_CSS_LINKS=()
HTML_TITLE=""
DOC_TITLE=""
ENABLE_TOC=0
TOC_DEPTH=""

# If a third positional arg exists and is not an option, treat it as CSS
if [[ $# -ge 3 && "${3}" != --* ]]; then
  CSS_BASENAME="${3}"
  shift 3 2>/dev/null || true
else
  # Only input and output were provided; keep default CSS and shift 2
  shift 2 2>/dev/null || true
fi
while [[ $# -gt 0 ]]; do
  case "$1" in
    --commonmark)
      # CommonMark-X: avoid extensions not supported (e.g., auto_identifiers)
  INPUT_FORMAT="commonmark_x+tex_math_dollars+tex_math_single_backslash+smart+emoji+footnotes+definition_lists+fenced_code_attributes+link_attributes+task_lists+strikeout+pipe_tables+table_captions"
      ;;
    --github)
      # Limit to GFM-supported set; avoid unsupported extensions like auto_identifiers
  INPUT_FORMAT="gfm+tex_math_dollars+tex_math_single_backslash+emoji+footnotes+task_lists+strikeout"
      ;;
    --html-title=*)
      HTML_TITLE="${1#--html-title=}"
      ;;
    --doc-title=*)
      DOC_TITLE="${1#--doc-title=}"
      ;;
    --html-css=*)
      EXTRA_CSS_LINKS+=("${1#--html-css=}")
      ;;
    --toc)
      ENABLE_TOC=1
      ;;
    --toc-depth=*)
      TOC_DEPTH="${1#--toc-depth=}"
      ;;
    *)
      # Ignore unknown arguments for now (markdown extension flags are not translated here)
      ;;
  esac
  shift
done

# Auto-upgrade to GFM if input looks like a pipe-table and format is commonmark
# No auto-switching: CommonMark-X already supports pipe_tables

export PUPPETEER_ARGS="--no-sandbox --disable-setuid-sandbox --disable-dev-shm-usage --disable-gpu"

# CRITICAL: Always embed MathJax for offline math support
# Must use specific MathJax file (/mathjax/tex-svg-full.js) for proper visual quality:
# - Connected lines in sqrt symbols
# - Properly rendered brackets and braces
# - High-quality mathematical typography
# DO NOT change to generic --mathjax flag - it breaks visual rendering
MATHJAX_URL="/mathjax/tex-svg-full.js"
OPTS=(
  -f "$INPUT_FORMAT"
  -t html5
  --standalone
  --section-divs
  --resource-path=/work:/styles:/tmp
  --mathjax=$MATHJAX_URL
)

# Title metadata (if provided)
if [[ -n "$HTML_TITLE" ]]; then
  OPTS+=(--metadata=pagetitle:"$HTML_TITLE")
elif [[ -n "$DOC_TITLE" ]]; then
  OPTS+=(--metadata=pagetitle:"$DOC_TITLE")
else
  OPTS+=(--metadata=pagetitle:"$PAGE_TITLE")
fi

# Make the CSS href in the HTML relative (basename only)
CSS_HREF_NAME="$(basename "$CSS_BASENAME")"
OPTS+=(--css="$CSS_HREF_NAME")

# Additional CSS links requested by user (e.g., remote URL)
for css_url in "${EXTRA_CSS_LINKS[@]}"; do
  OPTS+=(--css="$css_url")
done
if [[ "$INTERNAL_RESOURCES" == "1" ]]; then
  OPTS+=(--embed-resources)
fi

# Apply TOC options
if [[ "$ENABLE_TOC" == "1" ]]; then
  OPTS+=(--toc)
  if [[ -n "$TOC_DEPTH" ]]; then
    OPTS+=(--toc-depth="$TOC_DEPTH")
  fi
fi

FILTERS=()
# Do not use toc_unlist_h1.lua: it removes the whole TOC when levels are nested under H1.
# We'll flatten the TOC structure post-generation in HTML instead.
if command -v mermaid >/dev/null 2>&1; then
  FILTERS+=(--lua-filter=/filters/mermaid.lua)
fi
pandoc "${OPTS[@]}" ${FILTERS[@]} "$IN" -o "$OUT"


# When linking CSS, also make MathJax available next to the HTML so the file:// URL works reliably.
if [[ "$LINK_CSS" == "1" ]]; then
  # Ensure the referenced stylesheet is available next to the output HTML
  css_path="$CSS_BASENAME"
  if [[ ! -f "$css_path" && -f /styles/"$CSS_BASENAME" ]]; then
    css_path="/styles/$CSS_BASENAME"
  fi
  if [[ -f "$css_path" ]]; then
    cp -f "$css_path" "$(dirname "$OUT")/$CSS_HREF_NAME" || true
  fi
  # Provide MathJax locally next to the HTML to avoid cross-origin issues on file://
  if [[ -f /mathjax/tex-svg-full.js ]]; then
    cp -f /mathjax/tex-svg-full.js "$(dirname "$OUT")/tex-svg-full.js" || true
    # Update HTML to reference local MathJax path
    sed -i 's|src="/mathjax/tex-svg-full.js"|src="tex-svg-full.js"|g' "$OUT" || true
  fi
else
  # Embed the stylesheet content inline (replace link) when not linking
  css_path="$CSS_BASENAME"
  if [[ ! -f "$css_path" && -f /styles/"$CSS_BASENAME" ]]; then
    css_path="/styles/$CSS_BASENAME"
  fi
  if [[ -f "$css_path" ]]; then
    tmpblock="$(mktemp)" || exit 1
    {
      echo "  <style type=\"text/css\">"
      cat "$css_path"
      echo "  </style>"
    } > "$tmpblock"
    awk -v cssname="$(basename "$CSS_BASENAME")" -v blockfile="$tmpblock" 'BEGIN{inserted=0; block=""; while((getline l < blockfile)>0){block=block l ORS}; close(blockfile)} /<link rel="stylesheet"/ { if($0 ~ cssname) next } /<\/head>/ && !inserted { printf "%s", block; inserted=1 } {print}' "$OUT" > "$OUT.tmp" && mv "$OUT.tmp" "$OUT" || true
    rm -f "$tmpblock" || true
  fi
fi
echo "md → html: wrote $OUT"

# If TOC is enabled, place it after the first </h1> (intro) and before the first <h2>.
if [[ "$ENABLE_TOC" == "1" && -f "$OUT" ]]; then
  # First, flatten the TOC by removing the top-level H1 entry and promoting its children (H2+) to the top level.
  # This keeps anchors intact and preserves valid HTML structure.
  python3 - "$OUT" <<'PY' || true
import io, os, re, sys

path = sys.argv[1]
try:
    with io.open(path, 'r', encoding='utf-8') as f:
        s = f.read()
except Exception:
    sys.exit(0)

def find_tag_block(h, tag, start=0):
    open_re = re.compile(r'<%s(\s[^>]*)?>' % re.escape(tag), re.I)
    close_re = re.compile(r'</%s>' % re.escape(tag), re.I)
    m = open_re.search(h, start)
    if not m:
        return None
    pos = m.start()
    i = m.end()
    depth = 1
    tag_any = re.compile(r'<(/?)%s(\s[^>]*)?>' % re.escape(tag), re.I)
    while depth > 0:
        m2 = tag_any.search(h, i)
        if not m2:
            return None
        if m2.group(1) == '/':
            depth -= 1
        else:
            depth += 1
        i = m2.end()
    return (pos, i)

# Locate the TOC nav
mnav = re.search(r'<nav\b[^>]*\bid\s*=\s*([\"\"])TOC\1[^>]*>', s, flags=re.I)
if not mnav:
    sys.exit(0)
nav_open_start = mnav.start()
nav_open_end = mnav.end()
# Find the closing </nav>
nav_close = s.lower().find('</nav>', nav_open_end)
if nav_close == -1:
    sys.exit(0)
nav_end = nav_close + len('</nav>')

nav_prefix = s[nav_open_start:nav_open_end]
nav_content = s[nav_open_end:nav_close]
nav_suffix = '</nav>'

# In nav_content, find the top-level <ul> block
ul_block = find_tag_block(nav_content, 'ul', 0)
if not ul_block:
    sys.exit(0)
ul_start, ul_end = ul_block
ul_html = nav_content[ul_start:ul_end]

# Within ul_html, find the first top-level <li> block
li_block = find_tag_block(ul_html, 'li', 0)
if not li_block:
    sys.exit(0)
li_start, li_end = li_block
li_html = ul_html[li_start:li_end]

# Inside li_html, find a nested <ul> block (children of H1)
nested_ul = find_tag_block(li_html, 'ul', 0)
if not nested_ul:
    # No nested UL under the first LI; leave as-is
    sys.exit(0)
nul_start, nul_end = nested_ul
nested_ul_html = li_html[nul_start:nul_end]

# Replace the top-level UL with the nested UL from the first LI
new_nav_content = nav_content[:ul_start] + nested_ul_html + nav_content[ul_end:]
s2 = s[:nav_open_start] + nav_prefix + new_nav_content + nav_suffix + s[nav_end:]

with io.open(path, 'w', encoding='utf-8') as f:
    f.write(s2)
PY

  tmpfile="$(mktemp)" || exit 1
  awk '
    BEGIN{toc=""; in_toc=0}
    /<nav[^>]*id="TOC"[^>]*>/ {in_toc=1}
    { if(in_toc) toc = toc $0 ORS; else body[++n]=$0 }
    /<\/nav>/ && in_toc { in_toc=0; next }
    END{
      if (toc=="" || n==0) { for(i=1;i<=n;i++) print body[i]; exit }
      printed_toc=0
      seen_h1_close=0
      for(i=1;i<=n;i++){
        # After closing H1, before first H2 -> insert TOC once
        if(!printed_toc && seen_h1_close && body[i] ~ /<h2[^>]*>/){
          print toc
          printed_toc=1
        }
        print body[i]
        if(body[i] ~ /<\/h1>/){ seen_h1_close=1 }
      }
      if(!printed_toc){
        # fallback: if we saw </h1> but no <h2>, put TOC after </h1>
        if(seen_h1_close){
          for(i=1;i<=n;i++){
            print body[i]
            if(body[i] ~ /<\/h1>/ && !printed_toc){ print toc; printed_toc=1 }
          }
        } else {
          # no h1 found: append at end
          print toc
        }
      }
    }
  ' "$OUT" > "$tmpfile" && mv "$tmpfile" "$OUT" || rm -f "$tmpfile" || true
fi

# If TOC is enabled, add inline backlinks to TOC on all section headings (h2–h6).
if [[ "$ENABLE_TOC" == "1" && -f "$OUT" ]]; then
  python3 - "$OUT" <<'PY' || true
import io, re, sys

path = sys.argv[1]
try:
  with io.open(path, 'r', encoding='utf-8') as f:
    s = f.read()
except Exception:
  sys.exit(0)

# Only proceed if a TOC anchor exists
if re.search(r'<nav\b[^>]*\bid\s*=\s*[\"\']TOC[\"\']', s, flags=re.I) is None:
  sys.exit(0)

def add_backlink(html):
  # Append backlink inside closing tag of h2..h6 if not already present
  def repl(m):
    tag = m.group('tag')
    inner = m.group('inner')
    # Skip if a toc-back link already exists within the header
    if 'class="toc-back"' in inner or "class='toc-back'" in inner:
      return m.group(0)
    link = '<a class="toc-back" href="#TOC" aria-label="Back to table of contents">⇧ TOC</a>'
    return f"<h{tag}{m.group('attrs')}>{inner}{link}</h{tag}>"

  # Regex matching header start and end with minimal inner capture
  pattern = re.compile(r"<h(?P<tag>[2-6])(?P<attrs>[^>]*)>(?P<inner>.*?)</h(?P=tag)>", re.I | re.S)
  return pattern.sub(repl, html)

s2 = add_backlink(s)
if s2 != s:
  with io.open(path, 'w', encoding='utf-8') as f:
    f.write(s2)
PY
fi
