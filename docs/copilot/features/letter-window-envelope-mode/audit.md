# Letter Window Envelope Mode Plan Audit

## Findings

- The plan used absolute repository and desktop paths in documentation. This conflicts with repository documentation guidance and would make test guidance non-portable.
- Letter mode depends on generated raw HTML, but the plan did not handle incompatible Markdown flags such as `--fno-html` and `--fno-html-blocks`.
- The body-class update was under-specified and risked duplicating or overwriting existing body classes. It also implied permissive shell edits that could hide failures.
- The preprocessing order was left as an implementation choice instead of a deterministic sequence.
- The parser requirements did not explicitly require HTML escaping, duplicate optional-tag validation, or ignoring tags inside fenced code blocks.
- The test plan missed several edge cases: HTML escaping, duplicate tags, fenced-code tags, existing body class preservation, and incompatible CLI flags.
- The fixture guidance suggested copying an external desktop file into permanent tests. Permanent tests should use inline data or repo-local test data created by the tests.
- The default CSS section overstated a problem: `md2html.sh` already defaults to `default.css` when no CSS argument is passed. The implementation should only make letter behavior explicit where needed.
- Some shell integration guidance was too tolerant of failure. Letter preprocessing and postprocessing failures should terminate the command with clear errors.

## Suggestions Applied

- Rewrote paths as relative repository paths.
- Added deterministic preprocessing and postprocessing sequencing.
- Added fail-loud validation for required tags, duplicate optional tags, incompatible Markdown flags, and generated HTML handling.
- Added HTML escaping and fenced-code parsing requirements.
- Replaced fragile body-class guidance with a small strict postprocessing helper.
- Simplified default CSS guidance and removed redundant CSS-path assertions.
- Expanded tests to cover parser, CLI/conversion, shell postprocessing, and edge cases.
- Reworked fixture strategy to avoid depending on external desktop files in permanent tests.

## Improvement Todo

- [x] Keep open questions and assumptions at the top of the plan.
- [x] Remove non-portable paths from the plan.
- [x] Make implementation sequencing deterministic.
- [x] Add missing validation and fail-loud behavior.
- [x] Expand test coverage for edge cases and integration points.
- [x] Remove over-specific or redundant CSS command assertions.
