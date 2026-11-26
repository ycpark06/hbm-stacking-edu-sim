"""Run unchanged midterm copies with each script's original working directory.

Each case gets a fresh temporary {calc,fig} layout so generated JSON never
replaces repository originals or affects the following case. No dependencies
are installed. Missing imports are reported and remaining cases still run.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

PARENT_CWD = {'process_physics', 'education_calc', 'error_budget', 'integration', 'drive_calc'}
SCRIPTS = ['process_physics', 'education_calc', 'thermal', 'control_sim',
           'contact_speed_study', 'vision', 'vision_robust', 'error_budget',
           'integration', 'drive_calc']
CASES = [(name, []) for name in SCRIPTS] + [
    ('fea_struct', ['10', 'static', 'v5', '0']),
    ('fea_struct', ['10', 'modal', 'v5', '0']),
    ('fea_struct', ['5', 'static', 'v5', '0']),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout', type=float, default=600, help='maximum seconds per script')
    args = parser.parse_args()
    source = Path(__file__).resolve().parent / 'midterm'
    failures = 0
    print('script / arguments | cwd | status | seconds | detail', flush=True)
    print('--- | --- | --- | ---: | ---', flush=True)
    for name, argv in CASES:
        with tempfile.TemporaryDirectory(prefix='mse-midterm-') as temp:
            root = Path(temp)
            shutil.copytree(source, root / 'calc')
            (root / 'fig').mkdir()
            (root / 'mplconfig').mkdir()
            cwd = root if name in PARENT_CWD else root / 'calc'
            env = dict(os.environ, MPLCONFIGDIR=str(root / 'mplconfig'), MPLBACKEND='Agg')
            script = root / 'calc' / f'{name}.py'
            start = time.monotonic()
            try:
                run = subprocess.run([sys.executable, '-I', str(script), *argv],
                                     cwd=cwd, env=env, text=True, capture_output=True,
                                     timeout=args.timeout)
                if run.returncode == 0:
                    status, detail = 'OK', 'completed in isolated copy'
                else:
                    failures += 1
                    lines = run.stderr.strip().splitlines()
                    detail = lines[-1] if lines else f'exit {run.returncode}'
                    status = 'MISSING DEPENDENCY' if 'ModuleNotFoundError' in run.stderr else 'FAIL'
                    if name == 'fea_struct' and argv[:2] == ['10', 'static'] and 'ZeroDivisionError' in run.stderr:
                        detail += '; original fea_struct.py:93-94: no load nodes on z=175 mm at h=10; unchanged'
            except subprocess.TimeoutExpired:
                failures += 1
                status, detail = 'TIMEOUT', f'exceeded {args.timeout:g} s'
            if name == 'fea_struct' and argv[:2] == ['10', 'static'] and status == 'MISSING DEPENDENCY':
                detail += '; known original defect: z=175 mm has no load nodes, lines 93-94 (not reached)'
            elapsed = time.monotonic() - start
            print(f'{name}.py {" ".join(argv)} | {"parent" if cwd == root else "calc"} | {status} | {elapsed:.2f} | {detail}', flush=True)
    print(f'SUMMARY cases={len(CASES)} successful={len(CASES)-failures} unsuccessful={failures}', flush=True)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
