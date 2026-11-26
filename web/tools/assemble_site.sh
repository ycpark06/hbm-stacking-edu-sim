#!/bin/sh
# Assemble only public assets; never rebuild firmware.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
python3 - "$ROOT" <<'PY'
from pathlib import Path
import shutil
import sys

root = Path(sys.argv[1])
site = root / '_site'
# Refuse symlinks instead of following them outside the output directory.
if site.is_symlink():
    raise SystemExit('_site must not be a symlink')
if site.exists():
    shutil.rmtree(site)
site.mkdir()

def ignored(directory, names):
    excluded = {name for name in names if name.startswith('.') or name in ('node_modules', '__pycache__')}
    if Path(directory) == root / 'sim':
        excluded.add('test')
    if Path(directory) == root / 'web':
        excluded.add('tools')
    return excluded

for folder in ('web', 'sim'):
    shutil.copytree(root / folder, site / folder, ignore=ignored)
build = site / 'firmware' / 'build'
build.mkdir(parents=True)
for name in ('controller.js', 'controller.wasm'):
    shutil.copy2(root / 'firmware' / 'build' / name, build / name)
(site / '.nojekyll').touch()
(site / 'index.html').write_text('''<!doctype html>
<html lang="ko"><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=web/">
<title>웹 데모</title><a href="web/">웹 데모 열기</a></html>
''', encoding='utf-8')
print(f'Assembled: {site}')
PY
