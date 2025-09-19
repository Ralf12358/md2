#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
# Default: external resources, embedded CSS unless --link-css
./md2html.sh examples/external-css.md
mv examples/external-css.html examples/external-css.external-default.html

# Linked CSS variant (resources still external)
./md2html.sh --link-css examples/external-css.md
mv examples/external-css.html examples/external-css.linked-external.html

# Fully internal (embed resources) with embedded CSS
./md2html.sh --internal-resources examples/external-css.md
mv examples/external-css.html examples/external-css.internal.html

# Fully internal with linked CSS
./md2html.sh --internal-resources --link-css examples/external-css.md
mv examples/external-css.html examples/external-css.internal-linked.html

echo "Created: external-css.external-default.html (external resources, embedded CSS)"
echo "Created: external-css.linked-external.html (external resources, linked CSS)"
echo "Created: external-css.internal.html (embedded resources, embedded CSS)"
echo "Created: external-css.internal-linked.html (embedded resources, linked CSS)"
