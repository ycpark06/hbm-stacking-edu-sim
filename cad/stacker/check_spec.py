"""Fusion-free geometry/name/feature checks. No claim of interference verification."""
import json
from pathlib import Path
import sys
# Isolated Python (-I) omits the script directory from sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from spec_stacker import *
def check():
    assert len({p[1] for p in P})==len(P)
    assert set(p[2] for p in P)==set(NAMES)
    assert all(n in PART_SOURCES for n,_,_ in CUTS)
    for p in P:
        lo,hi=bounds(p); assert all(a<b for a,b in zip(lo,hi))
    size=bbox(); assert max(size[:2])<=LIMITS['footprint']
    assert MOLD['bore'] < MOLD['cavity_w']
    assert CHUCK['window'] > STACK['die']
    assert REFLOW['heater_w'] < REFLOW['w']
    print(json.dumps(dict(status='PASS',bbox_estimate_mm=size,parts=len(P),mesh_groups=NAMES,interference='Fusion 실행 후 확인',height='참고값'),ensure_ascii=False,indent=2))
if __name__=='__main__': check()
