#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PORT=${1:-8000}
case "$PORT" in ''|*[!0-9]*) echo 'Usage: web/serve_local.sh [port]' >&2; exit 2;; esac
"$ROOT/web/tools/assemble_site.sh"
printf 'Open: http://localhost:%s/web/\n' "$PORT"
exec python3 -m http.server "$PORT" -d "$ROOT/_site"
