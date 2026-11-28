#!/usr/bin/env python3
"""Decode v2 sync flashes and trim narration clips without input seeking."""
import argparse
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys


def ffmpeg_path():
    preferred = Path('/opt/homebrew/bin/ffmpeg')
    return str(preferred) if preferred.is_file() else shutil.which('ffmpeg')


def detect_clock0(ffmpeg, source, preparation_end_s=None):
    # signalstats uses limited-range luma: white is 235. Requiring YMIN too
    # excludes ordinary mostly-white slides. These are detection settings only.
    command = [ffmpeg, '-hide_banner', '-loglevel', 'error', '-i', str(source),
               '-vf', 'signalstats,metadata=mode=print:file=-', '-an', '-f', 'null', '-']
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    frames = []
    for line in result.stdout.splitlines():
        match = re.search(r'^frame:\s*\d+.*pts_time:([\d.eE+\-]+)', line)
        if match:
            frames.append({'t': float(match[1])})
        elif line.startswith('lavfi.signalstats.YAVG='):
            frames[-1]['avg'] = float(line.split('=', 1)[1])
        elif line.startswith('lavfi.signalstats.YMIN='):
            frames[-1]['min'] = float(line.split('=', 1)[1])
    candidates, start = [], None
    for index, frame in enumerate(frames):
        white = frame.get('avg', 0) >= 232 and frame.get('min', 0) >= 230
        if white and start is None:
            start = index
        elif not white and start is not None:
            duration = frame['t'] - frames[start]['t']
            if .15 <= duration <= 1:
                candidates.append({'frame': index, 'clock0_s': frame['t'],
                                   'flash_start_s': frames[start]['t'], 'flash_duration_s': duration})
            start = None
    if preparation_end_s is not None:
        # Initial about:blank can also be white. The sync marker is the LAST
        # white run in preparation. The monotonic estimate is only an upper
        # bound (+ frame/RPC tolerance), never the actual trim point.
        candidates = [c for c in candidates if c['clock0_s'] <= preparation_end_s + .1]
    if not candidates:
        raise ValueError(f'{source.name}: no sync flash found')
    if preparation_end_s is None and len(candidates) != 1:
        raise ValueError(f'{source.name}: ambiguous sync flash')
    return candidates[-1]


def trim_scene(ffmpeg, source, target, duration, detected):
    # A 30 fps stream has integer frames; round upward when duration is fractional.
    count = math.ceil(duration * 30 - 1e-8)
    # trim is a filter AFTER decoding. Never use input -ss: WebM seeks can land
    # before the flash. Pad at most one missing output frame with the final image.
    filters = (f"trim=start_frame={detected['frame']},setpts=PTS-STARTPTS,"
               'scale=1920:1080:force_original_aspect_ratio=decrease,'
               'pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,'
               'tpad=stop_mode=clone:stop=1')
    result = subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-nostats',
                    '-progress', 'pipe:1', '-n', '-i', str(source),
                    '-vf', filters, '-frames:v', str(count), '-an', '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(target)], check=True, capture_output=True, text=True)
    encoded = re.findall(r'^frame=(\d+)$', result.stdout, re.MULTILINE)
    if not encoded or int(encoded[-1]) != count:
        raise ValueError(f'{source.name}: too short even after padding one frame')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path, nargs='?', default=Path('media/out/v2'))
    parser.add_argument('--ffmpeg', default=ffmpeg_path())
    args = parser.parse_args()
    if not args.ffmpeg:
        parser.error('ffmpeg not found')
    manifest = json.loads((args.directory / 'scenes.json').read_text(encoding='utf-8'))
    out = args.directory / 'trim'
    out.mkdir(exist_ok=True)
    report = {'method': 'decoded full-white flash end; next frame is clock0', 'scenes': []}
    report_path = out / 'sync_report.json'
    try:
        for scene in manifest['scenes']:
            if scene['status'] != 'complete' or 'sync_flash' not in scene:
                raise ValueError(f"scene{scene['scene']:02d}: complete flash recording required")
            duration = float(scene['duration_s'])
            if not math.isfinite(duration) or duration <= 0:
                raise ValueError('invalid duration_s')
            source = args.directory / f"scene{scene['scene']:02d}.webm"
            target = out / f"scene{scene['scene']:02d}.mp4"
            if target.exists():
                raise FileExistsError(target)
            detected = detect_clock0(args.ffmpeg, source, scene['clock0_video_s'])
            row = {'scene': scene['scene'], **detected, 'duration_s': duration,
                   'manifest_clock0_s': scene['clock0_video_s'],
                   'delta_s': detected['clock0_s'] - scene['clock0_video_s'],
                   'manifest_sync_flash': scene['sync_flash'], 'file': str(target), 'status': 'trimming'}
            report['scenes'].append(row)
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
            trim_scene(args.ffmpeg, source, target, duration, detected)
            row['status'] = 'complete'
            print(f"{source.name}: clock0={detected['clock0_s']:.6f} s, "
                  f"manifest={scene['clock0_video_s']:.6f} s, delta={row['delta_s']:+.6f} s → {target}")
    except Exception as exc:
        report.update(status='failed', error=str(exc))
        print(f'트리밍 중단: {exc}', file=sys.stderr)
        return 1
    else:
        report['status'] = 'complete'
        return 0
    finally:
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    raise SystemExit(main())
