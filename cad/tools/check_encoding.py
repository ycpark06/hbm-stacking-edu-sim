"""Check CAD text I/O and exercise Fusion-free code with ASCII defaults.

Run with Python 3.12 (numpy is needed by test_to_glb.py). No CAD outputs
are generated: conversion tests write only to TemporaryDirectory.
"""
import ast
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def argument(call, name, position, default=None):
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    return call.args[position] if len(call.args) > position else default


def missing_encodings(source, filename):
    """Inspect direct open/io.open/Path.open/read_text/write_text calls.

    Attribute calls are conservatively treated as file methods. Dynamic
    modes are treated as text unless a literal binary mode is visible.
    Aliases, indirect calls and third-party I/O APIs need manual review.
    """
    failures = []
    for call in ast.walk(ast.parse(source, filename=filename)):
        if not isinstance(call, ast.Call):
            continue
        func = call.func
        name = func.id if isinstance(func, ast.Name) else (
            func.attr if isinstance(func, ast.Attribute) else None)
        if name not in ('open', 'read_text', 'write_text'):
            continue
        if name == 'open':
            # builtins.open/io.open take a filename first; Path.open does not.
            file_first = isinstance(func, ast.Name) or (
                isinstance(func.value, ast.Name)
                and func.value.id in ('io', '_io', 'builtins'))
            mode = argument(call, 'mode', 1 if file_first else 0)
            if isinstance(mode, ast.Constant) and isinstance(mode.value, str) and 'b' in mode.value:
                continue
            position = 3 if file_first else 2
        else:
            position = 0 if name == 'read_text' else 1
        encoding = argument(call, 'encoding', position)
        if encoding is None or (isinstance(encoding, ast.Constant) and encoding.value is None):
            failures.append(f'{filename}:{call.lineno}: {name} missing encoding')
    return failures


def check_static():
    # Regression cases exercise modes, positional arguments and nested script loads.
    cases = (
        ("open('x')", 1), ("open('x', 'w')", 1),
        ("open('x', 'rb')", 0), ("open('x', mode='wb')", 0),
        ("open('x', 'r', -1, 'utf-8')", 0),
        ("open('x', encoding=None)", 1),
        ("io.open('x', encoding='utf-8')", 0),
        ("builtins.open('x')", 1),
        ("p.open('r', -1, 'utf-8')", 0), ("p.open('rb')", 0),
        ("p.open(mode='r')", 1), ("open('x', mode=mode)", 1),
        ("p.read_text('utf-8')", 0), ("p.read_text()", 1),
        ("p.write_text('text', 'utf-8')", 0), ("p.write_text('text')", 1),
        ("exec(open('script.py').read())", 1),
        ("json.dump({}, open('x', 'w'))", 1),
        ("csv.reader(open('x', encoding='utf-8'))", 0),
    )
    for source, expected in cases:
        actual = len(missing_encodings(source, '<regression>'))
        if actual != expected:
            raise AssertionError((source, expected, actual))
    files = sorted(path for folder in ('cad/stacker', 'cad/tools')
                   for path in (ROOT / folder).rglob('*.py'))
    failures = []
    for path in files:
        failures.extend(missing_encodings(path.read_text(encoding='utf-8'), str(path.relative_to(ROOT))))
    for failure in failures:
        print(failure)
    print(f'AST: {len(files)} Python files, {len(failures)} missing encodings; '
          f'{len(cases)} checker regression cases passed', flush=True)
    print('AST scope: direct calls only; aliases/indirect and third-party I/O require manual review.', flush=True)
    return not failures


# The macOS C locale can still use UTF-8. Enforce ASCII only when encoding
# is omitted, through the public builtins.open and io.open used by Path.
# Python source loading remains Python's own UTF-8-aware import machinery.
BOOTSTRAP = r'''
import builtins, io, json, locale, runpy, sys
target, action, policy = sys.argv[1:]
print(json.dumps(dict(locale_encoding=locale.getencoding(),
    utf8_mode=sys.flags.utf8_mode, stdout_encoding=sys.stdout.encoding,
    policy=policy)), flush=True)
if policy == 'forced-ascii':
    def ascii_default(original):
        def wrapped(file, mode='r', buffering=-1, encoding=None, *args, **kwargs):
            if 'b' not in mode and encoding is None:
                encoding = 'ascii'
            return original(file, mode, buffering, encoding, *args, **kwargs)
        return wrapped
    builtins.open = ascii_default(builtins.open)
    io.open = ascii_default(io.open)
sys.path.insert(0, str(__import__('pathlib').Path(target).parent))
sys.argv = [target]
if action == 'import':
    __import__('spec_stacker')
    print('spec_stacker import: PASS', flush=True)
else:
    runpy.run_path(target, run_name='__main__')
'''


def check_runtime():
    env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='0',
               LC_ALL='C', PYTHONCOERCECLOCALE='0', PYTHONDONTWRITEBYTECODE='1')
    print('Runtime env: PYTHONIOENCODING=utf-8 PYTHONUTF8=0 LC_ALL=C '
          'PYTHONCOERCECLOCALE=0 PYTHONDONTWRITEBYTECODE=1', flush=True)
    print('PYTHONIOENCODING controls console streams, not file defaults. '
          'Run native locale and forced ASCII open/io.open defaults separately. '
          'Fusion/adsk, OS locale installation and third-party native I/O are not emulated.', flush=True)
    passed = True
    for policy in ('native-locale', 'forced-ascii'):
        for target, action in (('cad/stacker/spec_stacker.py', 'import'),
                               ('cad/stacker/check_spec.py', 'run'),
                               ('cad/tools/test_to_glb.py', 'run')):
            print(f'RUN {policy}: {target} ({action})', flush=True)
            try:
                result = subprocess.run(
                    [sys.executable, '-B', '-c', BOOTSTRAP, str(ROOT / target), action, policy],
                    cwd=ROOT, env=env, capture_output=True, encoding='utf-8',
                    errors='backslashreplace', timeout=120)
            except subprocess.TimeoutExpired:
                print('FAIL: subprocess timed out after 120 seconds', flush=True)
                passed = False
                continue
            print(result.stdout, end='', flush=True)
            print(result.stderr, end='', flush=True)
            print(f'Exit status: {result.returncode}', flush=True)
            passed = passed and result.returncode == 0
    return passed


def main():
    static_ok = check_static()
    runtime_ok = check_runtime()
    print('Encoding checks: ' + ('PASS' if static_ok and runtime_ok else 'FAIL'))
    return 0 if static_ok and runtime_ok else 1


if __name__ == '__main__':
    sys.exit(main())
