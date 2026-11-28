#!/usr/bin/env python3
"""Chromium 없이 로컬 HTML·JS와 녹화 선택자 계약/계획을 대조한다."""
import ast
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

from record_demo import ACTIONS, PRESETS, ROOT, SCENES, SELECTORS, load_cues


class Elements(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = set()
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])


def check(root: Path):
    failures = []
    count = 0

    def require(condition, message):
        nonlocal count
        count += 1
        if not condition:
            failures.append(message)

    source_paths = ['web/index.html', 'web/vision.html']
    source_paths += [str(p.relative_to(root)) for p in sorted((root/'web/js').glob('*.js'))]
    sources = {p: (root/p).read_text(encoding='utf-8') for p in source_paths}
    ids = set().union(*(Elements(sources[p]).ids for p in ('web/index.html', 'web/vision.html')))
    recorder = (Path(__file__).with_name('record_demo.py')).read_text(encoding='utf-8')
    tree = ast.parse(recorder)
    for key, (selector, path, evidence) in SELECTORS.items():
        require(evidence in sources[path], f'{key}: 생성 근거 없음 ({path}: {evidence})')
        for ident in re.findall(r'#([\w-]+)', selector):
            require(ident in ids, f'{key}: HTML id 없음 #{ident}')
    # 계약에 등록하지 않은 직접 선택자의 정적 ID도 검출한다.
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.startswith('#'):
            for ident in re.findall(r'#([\w-]+)', node.value):
                require(ident in ids, f'직접 선택자 id 없음 #{ident}')
    hmi = sources['web/js/hmi.js']
    names = re.search(r"\$\('presets'\)\.innerHTML=\[(.*?)\]\.map", hmi)
    require(bool(names), '프리셋 생성 구조 변경')
    if names:
        require(re.findall(r"'([^']+)'", names[1]) == list(PRESETS.values()), 'S1~S5 버튼 이름·순서 변경')
    require('data-scenario="S${i+1}"' in hmi, '프리셋 번호 생성 구조 변경')
    for action, label in ACTIONS.items():
        require(f"['{action}','{label}']" in hmi, f'인터락 동작·버튼 이름 변경: {action}')
    require('data-action="${action}"' in hmi, '인터락 버튼 data-action 변경')
    for text in ('층별 접합·재가열·재용융', '사이클 시간 분해', 'BOND_TEMP_LOW',
                 '두 히터 동시 통전 금지 · 차단', '래치', '헤드', '척'):
        require(text in hmi, f'결과/상태 표시 문구 변경: {text}')
    require('GLB 모델 ·' in sources['web/js/viewer.js'], 'GLB 성공 상태 문구 변경')
    require("dataset.hmiState='done'" in hmi and "dataset.hmiState='error'" in hmi, '완료·오류 조건 변경')
    require("dataset.hmiReady='true'" in hmi, 'HMI 준비 조건 변경')
    vision = sources['web/js/vision_view.js']
    for token in ("$('layer').add", "$('iteration').replaceChildren", "$('history').replaceChildren",
                  "$('run').disabled=false", "$('layer').addEventListener('change',run)"):
        require(token in vision, f'비전 동적 DOM/동작 변경: {token}')
    # CSS는 브라우저에서 실행하지 않는다. 정적 id·문구와 동적 생성 근거를 대조한다.
    try:
        cues = load_cues(Path(__file__).with_name('cues.json'))
    except (ValueError, KeyError, TypeError) as exc:
        require(False, f'큐 계획 구조 오류: {exc}')
        cues = {'targets': {}, 'scenes': []}
    combined = '\n'.join(sources.values())
    for key, spec in cues['targets'].items():
        selector = spec['selector']
        require(bool(selector), f'큐 {key}: 빈 선택자')
        require(spec['source'] in sources, f'큐 {key}: 소스 파일 없음')
        require(spec['evidence'] in sources.get(spec['source'], ''), f'큐 {key}: 생성 근거 변경')
        for ident in re.findall(r'#([\w-]+)', selector):
            require(ident in ids, f'큐 {key}: id 없음 #{ident}')
        for text in re.findall(r':has-text\("([^"]+)"\)', selector):
            require(text in combined, f'큐 {key}: 텍스트 없음 {text}')
    buttons = set(ACTIONS.values()) | {f'{k} {v}' for k, v in PRESETS.items()}
    for row in cues['scenes']:
        for cue in row['cues']:
            if cue['action'] == 'click':
                require(cue['args']['name'] in buttons, f"큐 버튼 이름 없음: {cue['args']['name']}")
            if cue['action'] == 'goto':
                require(cue['args']['url'].split('?')[0] == 'vision.html', '큐 이동 URL 변경')
    # nth-child 행/열의 근거: 카드 순서와 S5 정렬된 압력 순서도 함께 검사한다.
    scenarios = (root/'sim/scenarios.js').read_text(encoding='utf-8')
    for token in ("recipes:[{mode:'TC-NCF',layers:12},{mode:'TC-NCF',layers:12,head_temp_compensation:true},{mode:'MR-MUF',layers:12}]",
                  "modes.flatMap(mode=>[100,50]", "recipes:[7,15,20].flatMap", "['capillary','default','lower','upper']"):
        require(token in scenarios, f'큐 카드 순서 생성 근거 변경: {token}')
    display = sources['web/js/hmi_display.js']
    require('inlet_pressure_MPa))].sort((a,b)=>a-b)' in display, 'S5 압력 열 정렬 변경')
    require(list(s.number for s in SCENES) == list(range(1, 9)), '장면 번호·개수 오류')
    require([s.slug for s in SCENES] == ['3d','s1','s2_vision','s3','s5','s4','faults','closing'], '시연 순서 오류')
    require(all(0 < s.seconds <= 60 for s in SCENES), '장면 고정 길이 범위 오류')
    require(300 <= sum(s.seconds for s in SCENES) <= 420, '총 길이 5~7분 범위 오류')
    require('media/out/' in (root/'.gitignore').read_text(encoding='utf-8').splitlines(), 'media/out/ ignore 누락')
    if failures:
        print('\n'.join('FAIL: '+msg for msg in failures), file=sys.stderr)
        return 1
    print(f'PASS: {count}개 정적 계약 확인, {len(SCENES)}장면 / {sum(s.seconds for s in SCENES)}초. 브라우저 미실행.')
    print('배포본 동기화·실제 DOM 가시성·실행 시간·WebGL·인코딩은 녹화 담당 환경에서 확인해야 합니다.')
    return 0


if __name__ == '__main__':
    raise SystemExit(check(ROOT))
