"""Regenerate control.json's manually copied contact_transient_N (Issue #5).

Reuses contact_speed_study.py verbatim, executing copied sources in a temporary
calc/fig layout. No repository originals are executed in place or modified.
stdout is machine-readable JSON; per-entry comparisons go to stderr.
"""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


def regenerate():
    source = Path(__file__).resolve().parent / 'midterm'
    with tempfile.TemporaryDirectory(prefix='mse-contact-') as temp:
        root = Path(temp)
        calc = root / 'calc'
        shutil.copytree(source, calc)
        (root / 'fig').mkdir()
        (root / 'mplconfig').mkdir()
        previous = Path.cwd()
        old_mpl = os.environ.get('MPLCONFIGDIR')
        os.environ['MPLCONFIGDIR'] = str(root / 'mplconfig')
        stream = io.StringIO()
        try:
            os.chdir(calc)
            with contextlib.redirect_stdout(stream):
                exec(compile((calc / 'contact_speed_study.py').read_text(),
                             'contact_speed_study.py', 'exec'),
                     {'__name__': '__main__', '__file__': str(calc / 'contact_speed_study.py')})
        finally:
            os.chdir(previous)
            if old_mpl is None:
                os.environ.pop('MPLCONFIGDIR', None)
            else:
                os.environ['MPLCONFIGDIR'] = old_mpl
    result = {}
    for line in stream.getvalue().splitlines():
        period, speed = line.split()[:2]
        label = f'{float(period) * 1000:g} ms'
        approach = f'{float(speed) * 1000:g} μm/s'
        result.setdefault(label, {})[approach] = float(line.rsplit(':', 1)[1])
    if sum(map(len, result.values())) != 6:
        raise ValueError('Expected all six contact_speed_study output rows')
    return result


def main():
    try:
        actual = regenerate()
    except ModuleNotFoundError as error:
        print(f'DEPENDENCY MISSING: {error}', file=sys.stderr)
        return 1
    original = json.loads((Path(__file__).resolve().parent / 'midterm/control.json').read_text())['contact_transient_N']
    print(json.dumps({'contact_transient_N': actual}, ensure_ascii=False, indent=2))
    print('period | approach | original N | regenerated N | difference N', file=sys.stderr)
    for period, entries in original.items():
        for speed, value in entries.items():
            regenerated = actual[period][speed]
            print(f'{period} | {speed} | {value:.3f} | {regenerated:.3f} | {regenerated-value:+.9g}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
