"""Copy chapter 11 source PNGs without modifying CAD/drawing originals."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[4]
DEST = Path(__file__).resolve().parent
SOURCES = {
    'cad/stacker/out/view_iso.png': 'ch11_view_iso.png',
    'cad/stacker/out/view_front.png': 'ch11_view_front.png',
    'docs/drawings/stack_chuck.png': 'ch11_stack_chuck.png',
    'docs/drawings/reflow_chuck.png': 'ch11_reflow_chuck.png',
    'docs/drawings/mold_jig.png': 'ch11_mold_jig.png',
    'wiring/hbm_wiring.png': 'ch11_wiring.png',
}

if __name__ == '__main__':
    for source, target in SOURCES.items():
        shutil.copyfile(ROOT / source, DEST / target)
    print(f'Copied {len(SOURCES)} chapter 11 PNGs')
