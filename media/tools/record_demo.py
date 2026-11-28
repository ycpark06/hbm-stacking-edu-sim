#!/usr/bin/env python3
"""배포 HMI 무음 시연. 브라우저 실행은 녹화 담당 환경에서만 수행한다."""
from __future__ import annotations

import argparse
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
import math
import re
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'media/out'
DEFAULT_URL = 'https://ycpark06.github.io/hbm-stacking-edu-sim/web/'

# 아래 숫자는 영상 편집 시간·표시 설정이다. 공정 입력·계산 결과가 아니다.
@dataclass(frozen=True)
class Scene:
    number: int
    slug: str
    title: str
    seconds: int
    summary: str

SCENES = (
    Scene(1, '3d', '장비 3D · 적층 진행', 40, 'GLB 확인, OrbitControls 회전, 계산 후 단계 재생'),
    Scene(2, 's1', 'S1 · 접합 온도 미달과 헤드 보정', 60, 'TC-NCF 기본 1·2층 BOND_TEMP_LOW와 보정 층별 접합 최고·헤드 설정 비교'),
    Scene(3, 's2_vision', 'S2 · 정렬과 비전 보정 반복', 55, '누적 정렬 비교 후 비전 층·보정 단계·모서리 전환, 검출 십자선과 반복 표'),
    Scene(4, 's3', 'S3 · 박형 다이와 모델 한계', 45, '두 모드 두께 절반의 휨 증가 배율·판정·모델 한계'),
    Scene(5, 's5', 'S5 · 가압 충전', 45, '간격 × 입구 압력 표, 충전 시간·미충전·필러·겔 경고'),
    Scene(6, 's4', 'S4 · 처리량 분해', 40, '본더 점유·배치 후공정과 사이클 시간 분해; 라인 UPH 아님'),
    Scene(7, 'faults', '고장 주입 · 래치와 수동 복구', 55, '원인 유지 중 리셋 거부 → 원인 해제 → 수동 리셋, 두 히터 동시 통전 차단'),
    Scene(8, 'closing', '근거와 관찰 항목', 20, '가정값 근거 검색, 업체 주장 관찰 항목·판정 없음, 모델 한계'),
)

# check_selectors.py도 이 계약을 읽는다. 동적 DOM은 지정 JS 생성 근거를 확인한다.
SELECTORS = {
    'ready': ('body[data-hmi-ready="true"]', 'web/js/hmi.js', 'hmiReady'),
    'run': ('#run', 'web/index.html', 'run'),
    'viewer': ('#viewer canvas', 'web/js/viewer.js', 'renderer.domElement'),
    'model': ('#model-state', 'web/index.html', 'model-state'),
    'status': ('#status', 'web/index.html', 'status'),
    'results': ('#results', 'web/index.html', 'results'),
    'description': ('#description', 'web/index.html', 'description'),
    'alarms': ('#model-alarms', 'web/index.html', 'model-alarms'),
    'matrix': ('#s5', 'web/index.html', 's5'),
    'firmware': ('#firmware-status', 'web/index.html', 'firmware-status'),
    'search': ('#search', 'web/index.html', 'search'),
    'sources': ('#sources', 'web/index.html', 'sources'),
    'claims': ('#claims', 'web/index.html', 'claims'),
    'layer': ('#layer', 'web/vision.html', 'layer'),
    'iteration': ('#iteration', 'web/vision.html', 'iteration'),
    'mark': ('#mark', 'web/vision.html', 'mark'),
    'upper': ('#upper', 'web/vision.html', 'upper'),
    'history': ('#history', 'web/vision.html', 'history'),
}
PRESETS = {'S1': '열 이력', 'S2': '정렬', 'S3': '박형 다이', 'S4': '처리량', 'S5': '가압 충전'}
ACTIONS = {
    'hardware': '하드웨어 고장', 'clear': '고장 원인 해제',
    'reset': '수동 래치 리셋', 'heaters': '헤드 통전 중 척 히터 요청',
}


class Recorder:
    def __init__(self, page, scene, captions, started):
        self.page, self.scene, self.captions = page, scene, captions
        self.started = started
        self.deadline = started + scene.seconds
        self.samples = []

    def budget(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f'{self.scene.title}: 계획 길이 초과')
        # 페이지 이동마다 기본 timeout도 새로 적용한다.
        self.page.set_default_timeout(remaining * 1000)
        self.page.set_default_navigation_timeout(remaining * 1000)
        return remaining

    def loc(self, key):
        self.budget()
        return self.page.locator(SELECTORS[key][0])

    def hold(self, seconds):
        if seconds >= self.budget():
            raise TimeoutError(f'{self.scene.title}: 읽기 시간 부족')
        self.page.wait_for_timeout(seconds * 1000)

    def visit(self, url, vision=False):
        self.budget()
        response = self.page.goto(url, wait_until='domcontentloaded')
        if response is None or not response.ok:
            raise RuntimeError(f'페이지 HTTP 오류: {url}')
        if vision:
            self.wait_vision()
        else:
            self.loc('ready').wait_for()
        if self.captions:
            self.page.evaluate('''title => {
                const el = document.createElement('div');
                el.id = 'demo-caption'; el.textContent = title;
                el.style.cssText = 'position:fixed;bottom:18px;left:50%;transform:translateX(-50%);z-index:2147483647;background:#07111feb;color:white;padding:12px 28px;border:1px solid #60e0c0;border-radius:10px;font:24px system-ui;pointer-events:none;max-width:90vw';
                document.body.append(el);
            }''', self.scene.title)

    def wait_vision(self):
        self.budget()
        self.page.wait_for_function('''() => !document.querySelector('#run').disabled &&
            document.querySelector('#history tr') && !document.querySelector('#error').textContent''')

    def focus(self, target):
        self.budget()
        target.scroll_into_view_if_needed()
        target.evaluate('''el => {
            document.querySelectorAll('[data-demo-focus]').forEach(old => {
                old.style.outline = old.dataset.demoOutline;
                delete old.dataset.demoFocus; delete old.dataset.demoOutline;
            });
            el.dataset.demoOutline = el.style.outline;
            el.dataset.demoFocus = 'true'; el.style.outline = '3px solid #ffe084';
            el.scrollIntoView({block:'center', behavior:'instant'});
        }''')

    def sample(self, label):
        self.budget()
        # 텍스트 노드별 Range로 배지 앞 숫자·단위도 읽는다.
        # 닫힌 details나 화면 밖 텍스트는 관측값에서 제외한다.
        visible = self.page.evaluate('''() => {
            const rows = [], walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            let node;
            while ((node = walker.nextNode())) {
                const el = node.parentElement, text = node.textContent.trim();
                if (!el || !text || el.closest('script,style,option')) continue;
                const s = getComputedStyle(el), range = document.createRange();
                range.selectNodeContents(node);
                const rects = Array.from(range.getClientRects());
                if (s.visibility === 'hidden' || s.display === 'none' || s.opacity === '0' ||
                    !rects.length || !rects.every(r => r.width && r.height && r.top >= 0 &&
                        r.bottom <= innerHeight && r.left >= 0 && r.right <= innerWidth)) continue;
                const container = el.closest('dd,td,th,p,label,h1,h2,h3,dt,caption');
                const term = container && container.tagName === 'DD' ? container.previousElementSibling : null;
                rows.push({text, tag:el.tagName, label:term ? term.innerText : null,
                    badges: container ? Array.from(container.querySelectorAll('.badge')).map(b=>b.innerText) : []});
            }
            return rows;
        }''')
        self.samples.append({'label': label, 'scene_s': round(time.monotonic()-self.started, 3),
                             'url': self.page.url, 'visible_text': visible,
                             'numeric_text': [v['text'] for v in visible if any(c.isdigit() for c in v['text'])]})

    def preset(self, code):
        self.budget()
        self.page.get_by_role('button', name=f'{code} {PRESETS[code]}', exact=True).click()
        self.budget()
        self.page.wait_for_function('''() => document.body.dataset.hmiState === 'done' ||
            document.body.dataset.hmiState === 'error' ''')
        if self.page.locator('body').get_attribute('data-hmi-state') != 'done':
            raise RuntimeError(self.page.locator('#recipe-error').inner_text())
        if not self.loc('run').is_enabled():
            raise RuntimeError('계산 완료 후 실행 버튼이 비활성 상태')

    def action(self, action):
        self.budget()
        self.page.locator(f'#fault-buttons button[data-action="{action}"]').click()
        self.focus(self.loc('firmware'))

    def firmware_state(self):
        # 화면 문자열의 래치·히터 표시를 검증하며 펌웨어 내부를 읽지 않는다.
        text = self.loc('firmware').inner_text()
        latch = re.search(r'래치\s+(\d+)', text)
        head = re.search(r'헤드\s+([\d.]+)\s*W', text)
        chuck = re.search(r'척\s+([\d.]+)\s*W', text)
        if not all((latch, head, chuck)):
            raise RuntimeError(f'펌웨어 상태 형식 변경: {text}')
        return int(latch[1]), float(head[1]), float(chuck[1])

    def perform(self, base):
        self.visit(base)
        n = self.scene.number
        if n == 1:
            self.loc('model').filter(has_text='GLB 모델').wait_for()
            self.focus(self.loc('viewer'))
            self.budget()
            self.page.get_by_role('button', name='S2 정렬', exact=True).click()
            box = self.loc('viewer').bounding_box()
            if not box:
                raise RuntimeError('3D 캔버스 없음')
            x, y = box['x']+box['width']*.5, box['y']+box['height']*.5
            self.page.mouse.move(x, y)
            self.page.mouse.down()
            try:
                for step in range(100):
                    self.budget()
                    self.page.mouse.move(x + step*2, y + 20*math.sin(step/20))
                    self.hold(.1)
            finally:
                self.page.mouse.up()
            self.budget()
            self.page.wait_for_function("() => ['done','error'].includes(document.body.dataset.hmiState)")
            if self.page.locator('body').get_attribute('data-hmi-state') != 'done':
                raise RuntimeError('3D 단계 재생 실패')
            self.sample('GLB·적층 진행')
        elif n == 2:
            self.preset('S1')
            cards = self.loc('results').locator('article')
            if cards.count() != 3:
                raise RuntimeError('S1 기본·보정·MR 결과 3개 필요')
            for i, label in ((0, '기본: 1·2층 미달'), (1, '헤드 보정 결과')):
                detail = cards.nth(i).locator('details').first
                detail.locator('summary').click()
                self.focus(detail)
                if i == 0 and detail.get_by_text('BOND_TEMP_LOW', exact=False).count() < 2:
                    raise RuntimeError('S1 기본 미달 알람 2개를 찾지 못함')
                if i == 1 and detail.get_by_text('BOND_TEMP_LOW', exact=False).count():
                    raise RuntimeError('S1 보정 결과에 접합 온도 미달')
                self.sample(label)
                self.hold(8)
                detail.locator('summary').click()
            self.focus(self.loc('alarms')); self.sample('알람·보정 비교'); self.hold(5)
        elif n == 3:
            self.preset('S2'); self.focus(self.loc('results'))
            self.sample('S2 누적 정렬 계산 결과'); self.hold(6)
            self.visit(urljoin(base, 'vision.html'), vision=True)
            options = self.loc('layer').locator('option').evaluate_all('(els)=>els.map(e=>e.value)')
            for layer in (options[0], options[-1]):
                self.loc('layer').select_option(layer); self.wait_vision()
                iterations = self.loc('iteration').locator('option').evaluate_all('(els)=>els.map(e=>e.value)')
                for iteration in (iterations[0], iterations[-1]):
                    self.loc('iteration').select_option(iteration)
                    self.focus(self.loc('upper')); self.sample(f'{layer}층 {iteration}회 십자선'); self.hold(3)
                self.loc('mark').select_option('2')
                self.focus(self.loc('history')); self.sample(f'{layer}층 보정 반복'); self.hold(3)
        elif n == 4:
            self.preset('S3')
            for card in self.loc('results').locator('article').all():
                self.focus(card); self.sample('두께별 휨·배율·모델 한계'); self.hold(4)
        elif n == 5:
            self.preset('S5'); self.focus(self.loc('matrix'))
            self.sample('간격 × 입구 압력 미충전 표'); self.hold(9)
            cards = self.loc('results').locator('article')
            # S5 순서는 sim/scenarios.js: 간격별 capillary/default/lower/upper.
            for i in (0, 1, 5):
                self.focus(cards.nth(i)); self.sample('충전 시간·필러·겔 경고'); self.hold(3)
        elif n == 6:
            self.preset('S4'); self.focus(self.loc('results'))
            self.sample('본더·배치 후공정'); self.hold(6)
            for card in self.loc('results').locator('article').all():
                detail = card.locator('details').nth(1)
                detail.locator('summary').click(); self.focus(detail)
                self.sample('사이클 시간 분해'); self.hold(5)
        elif n == 7:
            self.page.locator('#fault-buttons button[data-action="hardware"]').wait_for()
            self.action('hardware')
            latched, head, chuck = self.firmware_state()
            if not latched or head != 0 or chuck != 0:
                raise RuntimeError('고장 래치·두 히터 차단 확인 실패')
            self.sample('하드웨어 고장 → 래치'); self.hold(6)
            self.action('reset')
            if self.firmware_state()[0] != latched:
                raise RuntimeError('원인 유지 중 리셋이 거부되지 않음')
            self.sample('원인 유지 중 리셋 거부'); self.hold(6)
            self.action('clear')
            if self.firmware_state()[0] != latched:
                raise RuntimeError('원인 해제만으로 래치가 풀림')
            self.sample('원인 해제 후 래치 유지'); self.hold(6)
            self.action('reset')
            if self.firmware_state()[0]:
                raise RuntimeError('수동 리셋 실패')
            self.sample('수동 리셋 완료'); self.hold(5)
            self.action('heaters')
            latch, head, chuck = self.firmware_state()
            if head <= 0 or chuck != 0 or '두 히터 동시 통전 금지 · 차단' not in self.loc('firmware').inner_text():
                raise RuntimeError('헤드 통전 중 척 요청 차단 확인 실패')
            self.sample('두 히터 동시 통전 차단'); self.hold(6)
        else:
            self.loc('search').fill('assumption'); self.focus(self.loc('sources'))
            self.sample('가정값·근거'); self.hold(5)
            self.focus(self.loc('claims').locator('..'))
            self.sample('업체 주장·판정 없음·모델 한계')
        self.budget()
        self.page.wait_for_timeout(max(0, self.deadline-time.monotonic())*1000)


def concatenate(out):
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        return {'status': 'skipped', 'reason': 'ffmpeg 없음; 설치하지 않음'}
    listing = out / 'concat.txt'
    listing.write_text(''.join(f"file 'scene_{s.number:02d}_{s.slug}.webm'\n" for s in SCENES), encoding='utf-8')
    subprocess.run([ffmpeg, '-nostdin', '-y', '-f', 'concat', '-safe', '1', '-i', str(listing),
                    '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                    str(out / 'demo_full.mp4')], check=True)
    return {'status': 'complete', 'file': 'demo_full.mp4'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default=DEFAULT_URL, help='web/ 디렉터리 URL (끝 / 권장)')
    parser.add_argument('--captions', action='store_true', help='하단 장면 제목 표시')
    parser.add_argument('--headed', action='store_true', help='브라우저 창 표시')
    parser.add_argument('--concat', action='store_true', help='ffmpeg가 있으면 무음 MP4 연결')
    parser.add_argument('--plan', action='store_true', help='브라우저 없이 계획 JSON 출력')
    args = parser.parse_args(argv)
    if args.plan:
        print(json.dumps({'total_s': sum(s.seconds for s in SCENES), 'scenes': [asdict(s) for s in SCENES]}, ensure_ascii=False, indent=2))
        return 0
    # import만으로 브라우저가 열리지 않는다. 정적 검사·--plan에는 Playwright도 불필요하다.
    from playwright.sync_api import sync_playwright
    OUT.mkdir(parents=True, exist_ok=True)
    if any(OUT.iterdir()):
        parser.error('media/out/이 비어 있지 않습니다. 기존 녹화물을 다른 곳으로 옮긴 뒤 실행하세요.')
    manifest = {'schema_version': 1, 'url': args.url, 'silent': True, 'captions': args.captions,
                'viewport': {'width': 1920, 'height': 1080}, 'planned_total_s': sum(s.seconds for s in SCENES),
                'timing': 'monotonic wall clock; scene bounds include page creation/navigation and exclude encoder finalization; media duration may differ slightly',
                'value_provenance': '화면 뷰포트의 DOM 텍스트 관측. 계산 결과·가정값 등의 화면 배지를 함께 보관. 숨긴 결과나 모델 내부 값은 읽지 않음.',
                'scenes': [], 'status': 'recording'}
    def save():
        (OUT / 'scenes.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    save()
    try:
        with sync_playwright() as pw:
            # 실행 실패 시 재시도·보안 옵션 변경·다른 브라우저 우회 없음.
            browser = pw.chromium.launch(headless=not args.headed)
            timeline = 0.0
            try:
                for scene in SCENES:
                    context = browser.new_context(viewport=manifest['viewport'], device_scale_factor=1,
                                                  record_video_dir=str(OUT / 'raw'),
                                                  record_video_size=manifest['viewport'], locale='ko-KR')
                    started = time.monotonic()
                    row = {**asdict(scene), 'planned_s': scene.seconds, 'start_s': timeline,
                           'started_utc': datetime.now(timezone.utc).isoformat(), 'status': 'recording'}
                    manifest['scenes'].append(row)
                    recorder = None
                    video = None
                    error = None
                    try:
                        page = context.new_page(); video = page.video
                        recorder = Recorder(page, scene, args.captions, started)
                        recorder.perform(args.url.rstrip('/') + '/')
                        row['status'] = 'complete'
                    except Exception as exc:
                        row['status'] = 'failed'; row['error'] = str(exc); error = exc
                    finally:
                        ended = time.monotonic()
                        row.update(duration_s=round(ended-started, 3),
                                   end_s=round(timeline+ended-started, 3),
                                   ended_utc=datetime.now(timezone.utc).isoformat(),
                                   samples=recorder.samples if recorder else [])
                        context.close()  # 비디오 flush 이후 save_as 가능
                        if video:
                            filename = f'scene_{scene.number:02d}_{scene.slug}.webm'
                            video.save_as(str(OUT / filename)); video.delete(); row['file'] = filename
                        save()
                    timeline = row['end_s']
                    if error:
                        raise error
            finally:
                browser.close()
        manifest['status'] = 'complete'
        manifest['actual_total_s'] = round(sum(r['duration_s'] for r in manifest['scenes']), 3)
        manifest['concat'] = concatenate(OUT) if args.concat else {'status': 'not_requested'}
        save()
        return 0
    except Exception as exc:
        manifest['status'] = 'failed'; manifest['error'] = str(exc); save()
        print(f'녹화 중단: {exc}\n우회하지 않았습니다. scenes.json과 녹화 담당 환경을 확인하세요.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
