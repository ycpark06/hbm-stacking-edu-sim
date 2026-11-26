#!/bin/sh
# Usage: headless_check.sh [Pages base URL | web/ URL | wasm_check.html URL]
# No argument: assemble and serve locally on PORT (default 8000).
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
CHROME='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
if [ "$#" -gt 1 ]; then echo 'Usage: headless_check.sh [url]' >&2; exit 2; fi
"$ROOT/web/tools/assemble_site.sh"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/wasm-check.XXXXXX")
SERVER_PID=
cleanup() {
    if [ -n "$SERVER_PID" ]; then
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
    rm -rf "$WORK"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
if [ "$#" -eq 0 ]; then
    PORT=${PORT:-8000}
    case "$PORT" in ''|*[!0-9]*) echo 'PORT must be an integer' >&2; exit 2;; esac
    python3 -m http.server "$PORT" --bind 127.0.0.1 -d "$ROOT/_site" >"$WORK/server.log" 2>&1 &
    SERVER_PID=$!
    # Check both readiness and ownership so an occupied port cannot give a false PASS.
    if ! python3 - "$PORT" "$SERVER_PID" <<'PY'
import os
import sys
import time
import urllib.request
port, pid = map(int, sys.argv[1:])
for attempt in range(50):
    try:
        os.kill(pid, 0)
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/web/wasm_check.html', timeout=0.5) as response:
            if response.status == 200:
                time.sleep(0.1)
                os.kill(pid, 0)
                break
    except ProcessLookupError:
        raise SystemExit('Local server exited before readiness')
    except OSError:
        time.sleep(0.1)
else:
    raise SystemExit('Local server readiness timeout')
PY
    then
        cat "$WORK/server.log" >&2
        exit 1
    fi
    URL="http://127.0.0.1:$PORT/web/wasm_check.html"
else
    URL=$(python3 - "$1" <<'PY'
import sys
from urllib.parse import urlsplit, urlunsplit
url = urlsplit(sys.argv[1])
if url.scheme not in ('http', 'https') or not url.netloc:
    raise SystemExit('URL must be http:// or https://')
path = url.path.rstrip('/')
if not path.endswith('/wasm_check.html'):
    if not path.endswith('/web'):
        path += '/web'
    path += '/wasm_check.html'
print(urlunsplit(url._replace(path=path)))
PY
    )
fi
printf 'Checking: %s\n' "$URL"
# A fresh profile is confined to the temporary directory. Never disable Chrome sandboxing.
python3 - "$CHROME" "$WORK" "$URL" <<'PY'
from pathlib import Path
import subprocess
import sys
chrome, directory, url = sys.argv[1:]
with (Path(directory) / 'dom.html').open('w') as output:
    try:
        result = subprocess.run([
            chrome, '--headless=new', '--disable-gpu',
            '--virtual-time-budget=10000', '--dump-dom',
            f'--user-data-dir={directory}/chrome', url,
        ], stdout=output, timeout=45)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SystemExit(str(error))
if result.returncode:
    raise SystemExit(f'Chrome exited with status {result.returncode}')
PY
python3 - "$WORK/dom.html" "$WORK/browser.json" <<'PY'
from html.parser import HTMLParser
from pathlib import Path
import json
import sys

class ResultParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.status = None
        self.in_result = False
        self.result = ''
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'body':
            self.status = attrs.get('data-wasm-check')
        if tag == 'pre' and attrs.get('id') == 'result':
            self.in_result = True
    def handle_endtag(self, tag):
        if tag == 'pre':
            self.in_result = False
    def handle_data(self, data):
        if self.in_result:
            self.result += data

parser = ResultParser()
parser.feed(Path(sys.argv[1]).read_text(encoding='utf-8'))
if parser.status != 'ok':
    raise SystemExit(f'data-wasm-check={parser.status!r}\n{parser.result}')
result = json.loads(parser.result)
Path(sys.argv[2]).write_text(json.dumps(result), encoding='utf-8')
print('data-wasm-check="ok"')
print('Browser JSON: ' + json.dumps(result, ensure_ascii=False))
PY
node "$ROOT/web/tools/wasm_check_node.mjs" "$WORK/browser.json"
