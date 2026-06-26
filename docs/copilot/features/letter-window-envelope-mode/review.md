# Letter Window Envelope Mode Review

## Audit Findings

- CLI letter-mode validation was not a clean boundary error. `md2html --letter --fno-html ...` and `md2pdf --letter --fno-html-blocks ...` reached the conversion API and raised an uncaught `ValueError` instead of exiting with a clear CLI error before conversion.
- The parser rendered an explicitly present but empty `<senderline>` as an empty sender line. The plan says optional values should render only when non-empty, and sender line derivation should be the default unless a useful override is present.
- Permanent tests did not cover several plan-required cases: `--fno-html` API rejection, CLI rejection of incompatible letter flags, missing receiver specifically, duplicate optional tags, absent optional metadata, and body-order preservation.

## Fixes Applied

- Added CLI boundary validation for incompatible letter-mode Markdown flags in `src/md2/cli.py`, with a clear stderr message and `SystemExit(2)` before calling conversion.
- Updated `src/md2/scripts/letter_preprocess.py` so an empty `<senderline>` does not suppress the derived sender line.
- Expanded unit tests in `src/tests/md2/test_conversion.py` and `src/tests/md2/test_letter_preprocess.py` to cover the missing plan cases.

## Verification

- `uv run pytest` -> 39 passed.
- `./test.sh` was not run because it does not exist in this repository.
