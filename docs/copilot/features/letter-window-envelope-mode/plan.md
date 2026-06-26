## Open Questions/Assumptions

- Should the new mode apply to all `md2*` commands or only the HTML/PDF pipeline?
  - [x] Add `--letter` to `md2html` and `md2pdf`; keep `html2pdf` and `md2docx` unchanged.
  - [ ] Add `--letter` to `md2html`, `md2pdf`, and `md2docx`.
  - [ ] Add `--letter` to all CLI commands, including `html2pdf`.
  - [ ] Custom solution: user can provide their own.
  - Assumption: Add `--letter` only to `md2html` and `md2pdf` because the feature parses Markdown-only tags and produces layout through the existing Markdown → HTML → PDF pipeline.

- How should the recipient tag be handled?
  - [x] Support only `<receiver>`; `<reciver>` was only a typo and must fail as an unknown tag.
  - [ ] Support both `<receiver>` and `<reciver>` as aliases; fail if both appear.
  - [ ] Support only `<reciver>`.
  - [ ] Custom solution: user can provide their own.
  - agent's assumption: Support only `<receiver>`; `<reciver>` was only a typo and must fail as an unknown tag.

- How should unknown or unsupported XML-like tags be handled in letter mode?
  - [x] Fail loudly when a block-level XML-like tag is found in letter metadata position but is not one of the supported letter tags.
  - [ ] Ignore unknown XML-like tags and leave them in the Markdown body.
  - [ ] Warn but continue processing the document.
  - [ ] Custom solution: user can provide their own.
  - agent's assumption: Unknown XML-like tags in the letter metadata block are authoring errors and must stop conversion with a clear message.

- Where should letter contact/date metadata come from?
  - [x] Use optional top-level XML-like blocks such as `<date>`, `<senderline>`, `<email>`, `<phone>`, and `<reference>`; omit absent fields cleanly.
  - [ ] Parse date/contact data from normal prose automatically.
  - [ ] Require all metadata fields in letter mode.
  - [ ] Custom solution: user can provide their own.
  - Assumption: Explicit optional tags keep authoring simple and avoid brittle inference.

- Should the small sender line above the address window be required separately?
  - [x] Derive it from `<sender>` by joining non-empty lines with ` - ` unless optional `<senderline>` is present.
  - [ ] Require `<senderline>` in letter mode.
  - [ ] Never show a repeated sender line.
  - [ ] Custom solution: user can provide their own.
  - Assumption: Deriving the repeated sender line is useful by default; `<senderline>` allows professional overrides.

- What initial envelope-window geometry should be used?
  - [x] Use configurable CSS custom properties with DIN-style starting values: A4, 20mm left receiver block, about 45mm top receiver block, 85mm receiver width, and optional right metadata column.
  - [ ] Hard-code exact positions in generated HTML.
  - [ ] Require users to provide a custom CSS file for all letter positioning.
  - [ ] Custom solution: user can provide their own.
  - Assumption: CSS custom properties in default CSS files provide good initial placement while keeping fine-tuning easy.

# Letter Window Envelope Mode Plan

## Context From Exploration

- CLI entry points are in `src/md2/cli.py`.
  - `md2html` and `md2pdf` manually parse options.
  - `--no-toc` is represented internally in `markdown_flags`; `md2html()` removes it before passing arguments to Pandoc.
  - `md2pdf()` calls `md2html()` first, then `html2pdf()`.
- Conversion orchestration is in `src/md2/conversion.py`.
  - `md2html()` builds the container command and mounts `/styles`, `/filters`, and `/scripts`.
  - `md2html.sh` defaults to `default.css` when no CSS argument is passed; `md2html()` passes `default.toc.css` explicitly only when TOC is active.
  - `md2pdf()` keeps HTML clean and then calls `html2pdf()`.
- Container Markdown processing is in `src/md2/scripts/md2html.sh` and `src/md2/scripts/preprocess_md.py`.
  - `preprocess_md.py` currently handles list spacing and pseudo-headings only.
  - `md2html.sh` calls `preprocess_md.py`, runs Pandoc, then applies HTML post-processing.
- PDF generation is in `src/md2/scripts/print.js`, `src/md2/scripts/pdf_generator.sh`, and `src/md2/scripts/pdf_processor.py`.
  - Puppeteer prints A4 with 10mm margins by default.
  - Page numbers are enabled by default for PDF but can be disabled with `--no-page-numbers`.
- Default CSS files are `src/md2/styles/default.css` and `src/md2/styles/default.toc.css`.
  - Both define many CSS custom properties and print-specific rules.
  - `default.toc.css` duplicates much of `default.css` plus TOC styling.
- Tests are under `src/tests/md2` and run via `uv run pytest` according to `pyproject.toml`.
  - Existing tests mock container calls and assert command construction.
  - Existing preprocessor tests import scripts directly.
- The provided source document currently contains `<sender>` and `<receiver>` blocks at the top.
- The reference screenshot shows a professional A4 letter first page:
  - small sender/company line near the top-left,
  - recipient address below it on the left,
  - contact/reference/date metadata on the right,
  - page indicator on the right.

## Implementation Sequence

- Add `src/md2/scripts/letter_preprocess.py`.
  - Keep the script small and functional; do not expand `preprocess_md.py` with unrelated letter logic.
  - Provide a pure function such as `preprocess_letter_markdown(text: str) -> str` for unit tests.
  - Provide a CLI entry point `letter_preprocess.py <input.md> <output.md>` for `md2html.sh`.
  - Fail with a non-zero exit and clear stderr message on invalid letter input.
- Implement strict letter tag parsing.
  - Parse only block-level tags that start at the beginning of a line and are not inside fenced code blocks.
  - Treat tags as case-sensitive.
  - Required in `--letter`: exactly one `<sender>...</sender>` and exactly one `<receiver>...</receiver>`.
  - Fail if required blocks are missing, duplicated, nested, unclosed, empty, or misspelled.
  - Optional single-instance block tags: `<senderline>`, `<date>`, `<email>`, `<phone>`, and `<reference>`.
  - Fail if an optional tag appears more than once.
  - Fail if an unsupported block-level XML-like tag appears in the initial letter metadata block; this includes `<reciver>`.
  - Optional tags may be multiline; render only non-empty optional values.
  - Remove parsed letter tags from the Markdown body and leave normal content in original order.
- Generate safe raw HTML for Pandoc.
  - Escape all user-provided tag content with HTML escaping before inserting it into generated HTML.
  - Preserve address line breaks by joining escaped sender and receiver lines with `<br>` where rendered.
  - Derive the sender line by joining non-empty escaped `<sender>` lines with ` - ` unless `<senderline>` is present.
  - Prepend one generated block to the remaining Markdown body.
  - Do not infer subject, salutation, location, or date from prose; authors keep those as normal Markdown or explicit tags.
- Add strict HTML body-class postprocessing.
  - Add a small helper script, for example `src/md2/scripts/html_body_classes.py`, to add `letter` and `no-toc` classes while preserving any existing body classes.
  - Use the helper from `md2html.sh` instead of fragile text replacement when letter mode is active.
  - Fail the shell command if body-class postprocessing fails.
- Wire `--letter` through `src/md2/cli.py` and `src/md2/conversion.py`.
  - Add `--letter` to `md2html` and `md2pdf` usage text and option parsing.
  - Add `letter: bool = False` to `md2html()` and `md2pdf()`.
  - In `letter=True`, force TOC off by removing `--toc`, ignoring `--toc-depth`, and adding no TOC command flags.
  - Reject incompatible Markdown flags `--fno-html` and `--fno-html-blocks` in letter mode with a clear boundary error, because the generated letter header uses raw HTML.
  - Pass `--letter` to `md2html.sh`.
  - Ensure `md2pdf(..., letter=True)` passes `letter=True` to the first HTML-generation command.
- Update `src/md2/scripts/md2html.sh`.
  - Parse `--letter` into `LETTER_MODE=1`.
  - Run existing preprocessing first: `preprocess_md.py "$IN" "$PRE_MD"`.
  - If letter mode is active, run `letter_preprocess.py "$PRE_MD" "$LETTER_MD"` and pass the letter-processed file to Pandoc.
  - Do not use fallback copies for `letter_preprocess.py`; invalid letter input must stop the command.
  - Keep TOC disabled in letter mode.
  - After Pandoc, add `letter` and `no-toc` body classes with the strict helper.
- Add CSS for letter layout.
  - Add letter CSS custom properties to both default CSS files near existing `:root` variables.
  - Add selectors for `body.letter` and `.md2-letter-*` classes to both default CSS files.
  - Initial values:
    - `--letter-page-margin-top: 18mm`
    - `--letter-page-margin-left: 20mm`
    - `--letter-window-top: 45mm`
    - `--letter-window-left: 20mm`
    - `--letter-window-width: 85mm`
    - `--letter-sender-line-font-size: 7.5pt`
    - `--letter-address-font-size: 11pt`
    - `--letter-meta-left: 130mm`
    - `--letter-meta-top: 42mm`
    - `--letter-body-top-spacing: 18mm`
  - Use normal document flow for body content; reserve fixed dimensions and margins only for the first-page letter head.
  - Key overrides on `body.letter` so TOC cover-page rules from `default.toc.css` do not affect letter output.
  - If the user supplies `--css`, keep using their CSS; document that custom CSS must define or override letter classes if default letter styling is not included.
- Update `README.md`.
  - Add a concise `--letter` usage section.
  - Document required tags, optional tags, strict unknown-tag errors, TOC behavior, and the `--no-page-numbers` option for formal letters.
  - Include a short Markdown example.

## Files Likely Affected

- `src/md2/cli.py`
- `src/md2/conversion.py`
- `src/md2/scripts/md2html.sh`
- `src/md2/scripts/letter_preprocess.py` new
- `src/md2/scripts/html_body_classes.py` new
- `src/md2/styles/default.css`
- `src/md2/styles/default.toc.css`
- `src/tests/md2/test_conversion.py`
- `src/tests/md2/test_letter_preprocess.py` new
- `src/tests/md2/test_html_body_classes.py` new
- `README.md`

## CLI/API Behavior

- `md2html --letter file.md`
  - Produces `file.html` with generated letter header HTML and `body` classes containing `letter` and `no-toc`.
  - Automatically disables TOC regardless of the default behavior.
  - Fails if `--fno-html` or `--fno-html-blocks` is also provided.
- `md2pdf --letter file.md`
  - Produces `file.html` and `file.pdf` through the existing pipeline.
  - Automatically disables TOC.
  - Page numbers remain controlled by the existing `--no-page-numbers` option.
- Python API:
  - `md2html([...], letter=True)` and `md2pdf([...], letter=True)`.
  - Default remains `letter=False`.
  - Invalid letter-mode flag combinations raise a clear exception before container execution.
- `html2pdf` remains unchanged because it receives already-rendered HTML and has no Markdown tags to parse.
- `md2docx` remains unchanged for this feature.

## Parsing and Generated HTML

- Generated HTML sketch:

```html
<div class="md2-letter-header">
  <div class="md2-letter-sender-line">Ralf Schneider - Verschaffeltstraße 14 - 68723 Schwetzingen</div>
  <div class="md2-letter-receiver">Netze BW GmbH<br>Schelmenwasenstraße 15<br>70567 Stuttgart</div>
  <dl class="md2-letter-meta">
    <div class="md2-letter-meta-email"><dt>E-Mail</dt><dd>...</dd></div>
    <div class="md2-letter-meta-phone"><dt>Telefon</dt><dd>...</dd></div>
    <div class="md2-letter-meta-reference"><dt>Referenz</dt><dd>...</dd></div>
    <div class="md2-letter-meta-date"><dt>Datum</dt><dd>26.06.2026</dd></div>
  </dl>
</div>
```

- Sender behavior:
  - Multiline `<sender>` is parsed as address lines.
  - The small repeated sender line defaults to all non-empty sender lines joined with ` - `.
  - `<senderline>` overrides the derived repeated sender line.
- Recipient behavior:
  - Exactly one `<receiver>` block is required.
  - `<reciver>` and any other unsupported XML-like letter metadata tag fail loudly.
- Date behavior:
  - If `<date>` is provided, render it in the right metadata column.
  - Do not parse dates from normal Markdown prose.
- Optional metadata:
  - Render optional `email`, `phone`, and `reference` only when present.
  - Use labels `E-Mail`, `Telefon`, `Referenz`, and `Datum`.

## Test Plan

- Unit tests for `letter_preprocess.py`.
  - Required sender and `<receiver>` produce the generated header and remove source tags.
  - `<reciver>` spelling fails loudly as an unknown tag.
  - Unknown XML-like tags in the letter metadata block fail loudly.
  - Missing `<sender>` fails loudly.
  - Missing recipient fails loudly.
  - Duplicate required tags fail loudly.
  - Duplicate optional tags fail loudly.
  - Unclosed and nested tags fail loudly.
  - Empty required tags fail loudly.
  - Multiline sender and receiver preserve intended line breaks.
  - `<senderline>` overrides the derived repeated sender line.
  - Optional `<date>`, `<email>`, `<phone>`, and `<reference>` render only when present.
  - Tag-like text inside fenced code blocks is left untouched and does not count as metadata.
  - Special characters such as `&`, `<`, and `>` are HTML-escaped in generated output.
  - The remaining Markdown body order is preserved.
- Unit tests for `html_body_classes.py`.
  - Adds `letter` and `no-toc` to a plain `<body>`.
  - Preserves existing body classes.
  - Does not duplicate classes.
  - Fails clearly if no body tag is present.
- Conversion command tests in `test_conversion.py`.
  - `md2html(..., letter=True)` passes `--letter` to `md2html.sh`.
  - `md2html(..., letter=True)` does not pass `--toc` or `--toc-depth`.
  - `md2html(..., letter=True, markdown_flags=["--fno-html"])` fails before container execution.
  - `md2html(..., letter=True, markdown_flags=["--fno-html-blocks"])` fails before container execution.
  - `md2pdf(..., letter=True)` passes letter mode into the first HTML-generation command.
  - Existing non-letter conversion behavior remains unchanged.
- CLI parsing tests.
  - `main_md2html(["--letter", file])` passes `letter=True` to the conversion function.
  - `main_md2pdf(["--letter", file])` passes `letter=True` to the conversion function.
  - CLI rejects incompatible letter-mode HTML suppression flags with clear errors.
- Fixture strategy.
  - Prefer inline test strings for parser tests.
  - If file fixtures are needed, create them under test-managed temporary directories or `src/tests/md2/tmp_test_data/` and keep them independent from external desktop paths.
  - Do not read or assert against production default files, default values, or mutable constants in tests.
- Existing full test command:
  - Run `uv run pytest`.
  - If `./test.sh` exists at implementation time, run it too.

## Verification Plan

- Automated checks:
  - `uv run pytest`
  - `uv run md2html --letter <repo-local-sample>.md`
  - `uv run md2pdf --letter <repo-local-sample>.md`
- Manual visual PDF check:
  - Use a temporary copy of the provided document or a repo-local sample with `<sender>`, `<receiver>`, `<date>`, `<email>`, `<phone>`, and optionally `<senderline>`.
  - Inspect the generated HTML enough to ensure the letter header exists and `body` includes `letter` and `no-toc`.
  - Inspect the rendered PDF first page against the reference screenshot:
    - sender line is small and above the recipient window,
    - receiver block starts in the visible-window area,
    - metadata column aligns professionally on the right,
    - title/body starts below the letter head with enough whitespace,
    - no TOC page or cover-page layout is present.
  - Fine-tune only CSS custom property values after visual inspection.
- Final acceptance check:
  - The generated PDF from the target letter document is suitable for a DIN windowed envelope with a professional first-page layout.

## Dependencies/Prerequisites

- Local container runtime: Podman or Docker, as already required by md2.
- Container image `md2:latest` may rebuild if scripts or styles change.
- Existing Puppeteer/Chrome PDF pipeline remains the rendering backend.
- Manual placement verification needs a rendered PDF or screenshot of the first page.

## Risks

- DIN envelope window exact placement varies by envelope type and printer scaling.
  - Mitigation: expose important offsets as CSS variables.
- Existing print CSS has strong title and TOC cover-page rules.
  - Mitigation: key letter overrides on `body.letter` and force TOC off.
- Pandoc raw HTML handling conflicts with HTML-suppression flags.
  - Mitigation: reject incompatible flags in letter mode before container execution.
- Generated HTML can become invalid if user content is inserted unescaped.
  - Mitigation: HTML-escape all tag content and test special characters.
- Default CSS files are partially duplicated.
  - Mitigation: add matching letter variables and rules to both default files; defer CSS deduplication to a separate refactor.
- Page footer numbers may visually conflict with formal letters.
  - Mitigation: keep existing behavior initially and document `--no-page-numbers` for letters where appropriate.
