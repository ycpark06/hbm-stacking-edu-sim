#!/usr/bin/env python3
"""Record narration-aligned scenes from the timing file. --plan never imports Playwright."""
import argparse
import base64
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import urljoin
from hmi_recording import prepare_hmi, execute_hmi

ROOT = Path(__file__).resolve().parents[2]
TIMING = Path.home() / 'Desktop/MSE489/기말보고서/영상/v2/tts/timing.json'
ACTIONS = {'factory', 'card', 'cad', 'cad_click', 'cad_explode', 'cad_scroll', 'drag_rotate', 'wait', 'external', 'hmi'}


def load_plan(cues_path, timing_path, card_path):
    data = json.loads(cues_path.read_text(encoding='utf-8'))
    timing = json.loads(timing_path.read_text(encoding='utf-8'))
    if not timing or [s['scene'] for s in data['scenes']] != [s['scene'] for s in timing] or [s['scene'] for s in timing] != list(range(1, len(timing)+1)):
        raise ValueError('장면 번호·순서: timing 파일과 일치해야 함')
    # Build actual stage IDs/durations from repository JS and original params/results.
    code = """import fs from 'node:fs';
import {readFactoryData,buildStages,MODES} from './web/js/factory_sequence.js';
const d=readFactoryData(JSON.parse(fs.readFileSync('sim/params.json')),JSON.parse(fs.readFileSync('sim/test/stage4_results.json')));
console.log(JSON.stringify(Object.fromEntries(MODES.map(m=>[m,buildStages(d,m)]))));"""
    stages = json.loads(subprocess.check_output(['node', '--input-type=module', '-e', code], cwd=ROOT, text=True))
    for key, spec in data['targets'].items():
        for proof in spec['evidence']:
            path = card_path if proof['file'] == 'media/tools/compare_card.html' else ROOT / proof['file']
            if proof['text'] not in path.read_text(encoding='utf-8'):
                raise ValueError(f'{key}: 근거 문자열 없음: {proof}')
    sentence = 0
    for scene, ts in zip(data['scenes'], timing):
        duration = ts['video_s']
        if not math.isfinite(duration) or duration <= 0 or not ts['sentences'] == len(ts['timing']) == len(ts['subs']):
            raise ValueError('문장 수·타이밍 불일치')
        previous_end = 0
        for start, end in ts['timing']:
            if not 0 <= previous_end <= start < end <= duration:
                raise ValueError('문장 시각·순서 오류')
            previous_end = end
        scene['duration_s'] = duration
        main = [c for c in scene['cues'] if 'sentence' in c]
        expected = list(range(sentence+1, sentence+ts['sentences']+1))
        if [c['sentence'] for c in main] != expected:
            raise ValueError('문장별 cue 1:1 대응 오류')
        for ordinal, (cue, (start, _)) in enumerate(zip(main, ts['timing']), 1):
            if 'at_sentence' in cue:
                if cue['at_sentence'] != ordinal or 't' in cue:
                    raise ValueError('상대 문장 순번 오류')
                cue['t'] = start
            if not 0 <= start-cue['t'] <= .201 or cue['sub'] != ts['subs'][cue['sentence']-sentence-1]:
                raise ValueError('문장 시작 시각·자막 대응 오류')
        previous = -1
        prep = scene['prepare']
        if prep['page'] not in ('factory', 'cad', 'card', 'external', 'hmi'):
            raise ValueError('준비 페이지 오류')
        if prep['page'] == 'external':
            pages = prep['pages']
            if len({p['id'] for p in pages}) != len(pages) or any(not p['url'].startswith('https://') for p in pages):
                raise ValueError('외부 페이지 ID·URL 오류')
        if prep['page'] == 'hmi':
            if prep['url'] != 'https://ycpark06.github.io/hbm-stacking-edu-sim/web/index.html?theme=light' or prep['cache_modes'] != ['TC-NCF', 'MR-MUF'] or prep['layers'] != 12:
                raise ValueError('HMI 실제 Pages URL·12단 캐시 조건 오류')
        mode = prep.get('mode')
        if prep['page'] == 'factory' and (mode not in stages or
                prep['stage'] not in {s['id'] for s in stages[mode]} or prep['camera'] not in (1, 2, 3, 4)):
            raise ValueError('준비 모드·단계·카메라 오류')
        for cue in scene['cues']:
            if cue['action'] not in ACTIONS or not math.isfinite(cue['t']) or not 0 <= cue['t'] < duration or cue['t'] <= previous:
                raise ValueError(f'cue 동작·시각 오류: {cue}')
            previous = cue['t']
            a = cue['args']
            required = {'cad_explode': ('from', 'to', 'duration_s'),
                        'drag_rotate': ('duration_s',)}
            if any(k not in a for k in required.get(cue['action'], ())):
                raise ValueError('cue 인자 누락')
            page_for = {'factory':'factory', 'card':'card', 'cad':'cad', 'cad_click':'cad',
                        'cad_explode':'cad', 'cad_scroll':'cad', 'drag_rotate':'cad', 'external':'external', 'hmi':'hmi'}
            if cue['action'] in page_for and prep['page'] != page_for[cue['action']]:
                raise ValueError('cue 페이지 불일치')
            if a.get('target') not in data['targets']:
                raise ValueError('대상 참조 없음')
            if cue['action'] not in data['targets'][a['target']]['actions']:
                raise ValueError('대상·동작 불일치')
            if cue['action'] in ('factory', 'card', 'cad') and not isinstance(a.get('js'), str):
                raise ValueError('JS 문자열 필요')
            if cue['action'] == 'external' and a.get('page') not in {p['id'] for p in prep['pages']}:
                raise ValueError('사전 로드 페이지 참조 없음')
            if cue['action'] == 'hmi' and a.get('step') not in ('home','run','charts','alarms','compare','fault','normal'):
                raise ValueError('HMI 단계 오류')
            if cue['action'] == 'factory':
                found = re.search(r"setMode\('([^']+)'\)", a['js'])
                if found:
                    mode = found[1]
                if any(int(k) not in (1, 2, 3, 4) for k in re.findall(r'setCamera\((\d+)\)', a['js'])):
                    raise ValueError('카메라 범위 오류')
                ids = {s['id']: s for s in stages[mode]}
                for stage_id in re.findall(r"setStage\('([^']+)'", a['js']):
                    if stage_id not in ids or stage_id == 'compare':
                        raise ValueError(f'공장 단계 오류: {stage_id}')
                if 'motion' in a:
                    m = a['motion']
                    start, end = m['start'], m['end']
                    if start[0] not in ids or end[0] not in ids or not all(0 <= p[1] <= 1 for p in (start,end)):
                        raise ValueError('motion 단계·진행률 오류')
                    lo, hi = ids[start[0]]['index'], ids[end[0]]['index']
                    span = sum(s['duration_s'] for s in stages[mode][lo:hi+1])-ids[start[0]]['duration_s']*start[1]-ids[end[0]]['duration_s']*(1-end[1])
                    if lo > hi or span <= 0 or end[0] == 'compare' or m['speed'] not in (.5, 1, 2):
                        raise ValueError('motion 순서·속도 오류')
                    if not m.get('scrub') and span/m['speed'] > m['duration_s']:
                        raise ValueError('문장 안에 재생을 마칠 수 없음')
            if 'duration_s' in a or 'motion' in a:
                seconds = a.get('duration_s', a.get('motion', {}).get('duration_s'))
                following = next((c['t'] for c in main if c['t'] > cue['t']), duration)
                if not 0 < seconds <= following-cue['t']:
                    raise ValueError('동작 지속 시간이 다음 문장을 침범함')
            if cue['action'] == 'cad_explode' and not 0 <= a['from'] < a['to'] <= 100:
                raise ValueError('분해 범위 오류')
            if cue['action'] == 'card' and not all(1 <= int(r) <= 3 for r in re.findall(r'(?:showRow|focus)\((\d)', a['js'])):
                raise ValueError('카드 행 오류')
        sentence += ts['sentences']
    return data


def print_plan(data, selected):
    print('| 장면 | 시각 (s) | 동작 | 대상 |')
    print('|---|---:|---|---|')
    for s in data['scenes']:
        if s['scene'] not in selected:
            continue
        print(f"| {s['scene']} 준비 | — | load / ready / GLB / 2 frames | {s['prepare']} |")
        for c in s['cues']:
            a = c['args']
            detail = a.get('js', a.get('page', data['targets'][a['target']]['label']))
            if 'panel_reason' in c:
                detail += ' · 패널 근거: '+c['panel_reason']
            if 'motion' in a:
                detail += ' ' + json.dumps(a['motion'], ensure_ascii=False)
            print(f"| {s['scene']} · 문장 {c.get('sentence', '보조')} | {c['t']:.3f} | {c['action']} | {detail.replace('|', '/')} |")
    print(f"검증 통과: {len(data['scenes'])}장면 / {sum('sentence' in c for s in data['scenes'] for c in s['cues'])}문장 / 전체 {sum(s['duration_s'] for s in data['scenes'])} s (준비 제외)")


# Per-frame guard clamps at the specified endpoint, including after a slow frame.
# Scrubbing is explicitly an editing display setting, never process time.
MOTION = """m => {
 const f=window.factory; const token=window.v2Token=(window.v2Token||0)+1;
 f.pause();f.setStage(...m.start);f.setSpeed(m.speed);
 const stages=f.stages(), offsets=[];let total=0;
 stages.forEach(s=>{offsets.push(total);total+=s.duration_s;});
 const pos=p=>{const s=stages.find(s=>s.id===p[0]);return offsets[s.index]+s.duration_s*p[1];};
 const start=pos(m.start),end=pos(m.end),began=performance.now();
 if(!m.scrub)f.play();
 function frame(now){if(window.v2Token!==token)return;
   const state=f.state(),current=offsets[state.stage]+state.elapsed_s;
   const u=Math.min(1,(now-began)/(m.duration_s*1000));
   if(u>=1||(!m.scrub&&current>=end)){f.pause();f.setStage(...m.end);return;}
   if(m.scrub){const x=start+(end-start)*u;const i=stages.findIndex((s,i)=>x<offsets[i]+s.duration_s);f.setStage(i,(x-offsets[i])/stages[i].duration_s);}
   requestAnimationFrame(frame);
 }requestAnimationFrame(frame);
}"""


def execute(page, cue, targets, samples=None):
    a, action = cue['args'], cue['action']
    if action == 'hmi':
        execute_hmi(page, cue, targets, samples)
    elif action == 'external':
        page.evaluate("id=>document.querySelectorAll('[data-page]').forEach(el=>el.hidden=el.dataset.page!==id)", a['page'])
    elif action == 'factory':
        page.evaluate('() => {window.v2Token=(window.v2Token||0)+1;window.factory.pause();}')
        page.evaluate('() => {const f=window.factory;'+a['js']+'}')
        if 'motion' in a:
            page.evaluate(MOTION, a['motion'])
    elif action == 'card':
        page.evaluate('() => {const c=window.card;'+a['js']+'}')
    elif action == 'cad':
        page.evaluate('() => {const c=window.cadPage;'+a['js']+'}')
    elif action == 'cad_click':
        spec = targets[a['target']]
        page.locator(spec['selector']).get_by_role('button', name=spec['name'], exact=True).click()
    elif action == 'cad_scroll':
        page.locator(targets[a['target']]['selector']).evaluate("el=>el.scrollIntoView({behavior:'smooth',block:'center'})")
    elif action == 'cad_explode':
        page.locator(targets[a['target']]['selector']).evaluate('''(el,a)=>new Promise(resolve=>{
          const began=performance.now();function frame(now){const u=Math.min(1,(now-began)/(a.duration_s*1000));
          el.value=a.from+(a.to-a.from)*(u*u*(3-2*u));el.dispatchEvent(new Event('input',{bubbles:true}));
          if(u<1)requestAnimationFrame(frame);else resolve();}requestAnimationFrame(frame);})''', a)
    elif action == 'drag_rotate':
        loc = page.locator(targets[a['target']]['selector'])
        loc.scroll_into_view_if_needed()
        box = loc.bounding_box()
        if not box:
            raise RuntimeError('캔버스 없음')
        x,y = box['x']+box['width']/2,box['y']+box['height']/2
        page.mouse.move(x,y);page.mouse.down()
        began = time.monotonic()
        try:
            while True:
                u=min(1,(time.monotonic()-began)/a['duration_s'])
                page.mouse.move(x+box['width']*.2*u,y+20*math.sin(u*math.pi))
                if u>=1:
                    break
                page.wait_for_timeout(20)
        finally:
            page.mouse.up()
    elif action != 'wait':
        raise ValueError(action)


def prepare_external(page, prep):
    """Preload actual external pages, mask, then cache frames on ONE video surface.

    Playwright records each tab separately: switching tabs alone cannot produce
    one scene video. Screenshots captured before clock0 avoid that discontinuity
    and all network waits during narration. The Pages frame stays unchanged.
    """
    mask = Path(__file__).with_name('github_mask.js').read_text(encoding='utf-8')
    frames = []
    for spec in prep['pages']:
        tab = page.context.new_page()
        try:
            tab.set_default_timeout(180000)
            tab.set_default_navigation_timeout(180000)
            tab.add_init_script(script=mask)
            failure = None
            for attempt in range(3):
                try:
                    response = tab.goto(spec['url'], wait_until='load')
                    if not response or not response.ok:
                        raise RuntimeError(f"외부 페이지 HTTP 오류: {spec['url']}")
                    tab.locator('main').wait_for(state='visible')
                    if spec['id'] == 'issue':
                        tab.locator('.markdown-body').first.wait_for(state='visible')
                        # The new GitHub issue UI shows the closed state as an icon/aria label,
                        # not visible text; the loaded issue body is the readiness signal.
                    elif spec['id'] == 'pages':
                        tab.wait_for_function("() => document.querySelector('#fields')?.children.length > 0 && document.querySelector('#viewer canvas') && !document.querySelector('#model-state').textContent.includes('초기화 중')")
                    elif spec['id'] in ('repo', 'folders'):
                        # The first /tree/ link can be a hidden branch-menu item; wait for a visible folder row.
                        tab.locator('a:visible', has_text='firmware').first.wait_for(state='visible')
                    elif spec['id'] == 'prs':
                        tab.locator('a[href*="/pull/"]').first.wait_for(state='visible')
                    break
                except Exception as exc:
                    failure = exc
                    if attempt == 2:
                        raise RuntimeError(f"사전 로드 실패: {spec['id']}") from failure
            tab.evaluate('() => document.fonts.ready')
            tab.add_style_tag(content='html{color-scheme:light!important} body{background:white!important} footer{display:none!important}')
            if spec.get('folders'):
                tab.evaluate('''folders=>{
                  const rows=folders.map(name=>{
                    const link=[...document.querySelectorAll('a[href*="/tree/"]')].find(a=>a.textContent.trim()===name);
                    if(!link)throw Error('폴더 행 없음: '+name);
                    const row=link.closest('tr,[role="row"]')||link.parentElement;
                    row.style.outline='4px solid #14365A';row.style.outlineOffset='-4px';return row;
                  });
                  const bounds=rows.map(row=>row.getBoundingClientRect());
                  const top=Math.min(...bounds.map(b=>b.top)),bottom=Math.max(...bounds.map(b=>b.bottom));
                  if(bottom-top>734)throw Error('폴더 행이 자막 제외 영역을 넘음');
                  window.scrollTo(0,Math.max(0,scrollY+top-40));
                }''', spec['folders'])
            elif spec['id'] == 'issue':
                tab.locator('.markdown-body').first.evaluate("el=>window.scrollTo(0,Math.max(0,el.getBoundingClientRect().top+scrollY-260))")
            else:
                tab.evaluate('window.scrollTo(0,0)')
            tab.evaluate('() => {window.recordingMask.maskDates();document.activeElement?.blur();}')
            tab.mouse.move(1910, 1070)
            tab.evaluate('() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
            # CSS crops the captured viewport below the subtitle-safe content area.
            encoded = base64.b64encode(tab.screenshot()).decode('ascii')
            frames.append({'id':spec['id'], 'src':'data:image/png;base64,'+encoded})
        finally:
            video = tab.video
            tab.close()
            if video:
                video.delete()
    page.set_content('''<!doctype html><html lang="ko"><meta charset="utf-8">
      <style>*{box-sizing:border-box}body{margin:0;background:white;overflow:hidden}
      img{position:absolute;top:76px;left:0;width:100%;height:calc(100vh - 306px);object-fit:cover;object-position:top center}
      img[hidden]{display:none}header{position:fixed;top:18px;left:24px;background:#14365A;color:white;padding:12px 28px;font:32px system-ui;z-index:5}
      </style><header>GitHub 저장소</header><main></main></html>''')
    page.evaluate('''frames=>{for(const frame of frames){const img=document.createElement('img');
      img.dataset.page=frame.id;img.src=frame.src;img.hidden=frame.id!==frames[0].id;
      document.querySelector('main').append(img);}}''', frames)
    page.wait_for_function('() => [...document.images].every(i=>i.complete&&i.naturalWidth>0)')


def prepare(page, scene, args, samples=None):
    suffix = '?theme=light' if args.theme == 'light' else ''
    prep = scene['prepare']
    if prep['page'] == 'hmi':
        prepare_hmi(page, prep, samples)
    elif prep['page'] == 'external':
        prepare_external(page, prep)
    elif prep['page'] == 'card':
        page.goto(args.card.resolve().as_uri()+suffix)
        page.wait_for_function('() => !!window.card')
        page.evaluate('window.card.reset()')
    elif prep['page'] == 'cad':
        page.goto(urljoin(args.url.rstrip('/')+'/', 'cad.html')+suffix)
        page.wait_for_function("() => document.querySelector('#cad-status').textContent.startsWith('GLB 연결')")
        page.locator('#explode').evaluate("el=>{el.value='0';el.dispatchEvent(new Event('input',{bubbles:true}));}")
        if args.theme == 'light':
            page.wait_for_function('() => !!window.cadPage')
            page.evaluate("() => {window.cadPage.setViewOnly(true);document.querySelectorAll('#comparison img').forEach(i=>i.loading='eager');}")
            # Keep the existing composition comparison above the subtitle reserve.
            page.add_style_tag(content="""
              body.cad-comparison #comparison{display:block;position:fixed;inset:100px 24px 230px;z-index:5;overflow:hidden;background:white;padding:16px}
              body.cad-comparison #comparison>:not(.comparison){display:none}
              body.cad-comparison .comparison{display:grid;grid-template-columns:1fr 1fr;height:100%;gap:24px}
              body.cad-comparison figure{margin:0;min-height:0}
              body.cad-comparison figure img{width:100%;height:450px;object-fit:contain}
              body.cad-comparison figcaption{font-size:28px}
              body.cad-comparison figcaption p{font-size:24px}
            """)
        else:
            # Load lazy comparison images before clock0, preserving v2 framing.
            page.locator('#comparison').evaluate('el=>el.scrollIntoView()')
        page.wait_for_function("() => [...document.querySelectorAll('#comparison img')].every(i=>i.complete&&i.naturalWidth>0)")
        if args.theme != 'light':
            page.locator('#comparison').evaluate("el=>el.scrollIntoView({block:'center'})")
    else:
        page.goto(urljoin(args.url.rstrip('/')+'/', 'factory.html')+suffix)
        page.wait_for_function('() => window.factory?.state().ready === true')
        page.evaluate('p=>{const f=window.factory;f.setViewOnly(true);f.setMode(p.mode);f.pause();f.setSpeed(1);f.setStage(p.stage,0);f.setCamera(p.camera);if("panel" in p)f.showPanel(p.panel);}', prep)
    if args.theme == 'light' and prep['page'] in ('factory', 'cad'):
        api = 'factory' if prep['page'] == 'factory' else 'cadPage'
        page.evaluate('(a)=>window[a.api].setTitle(a.title)', {'api':api,'title':scene.get('title', f"장면 {scene['scene']}")})
    if args.captions and args.theme != 'light' and prep['page'] != 'external':
        page.evaluate('''title=>{const el=document.createElement('div');el.textContent=title;
        el.style.cssText='position:fixed;top:18px;left:24px;z-index:2147483647;background:#07111feb;color:white;padding:12px 28px;border:1px solid #60e0c0;border-radius:10px;font:24px system-ui;pointer-events:none;max-width:90vw';document.body.append(el);}''', scene.get('title', f"장면 {scene['scene']}"))
    page.evaluate('() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://localhost:8000/web/')
    parser.add_argument('--card', type=Path, default=Path(__file__).with_name('compare_card.html'))
    parser.add_argument('--timing', type=Path, help='실측 timing JSON (cues_v5 기본: 영상/v5/tts/timing_v6.json)')
    parser.add_argument('--cues', type=Path, default=Path(__file__).with_name('cues_v2.json'))
    parser.add_argument('--out', type=Path, default=ROOT/'media/out/v2')
    parser.add_argument('--scene', type=int, action='append')
    parser.add_argument('--plan', action='store_true')
    parser.add_argument('--theme', choices=['light'])
    parser.add_argument('--captions', action='store_true')
    args = parser.parse_args()
    if args.timing is None:
        args.timing = (ROOT.parent/'영상/v5/tts/timing_v6.json') if args.cues.name == 'cues_v5.json' else TIMING
    data = load_plan(args.cues, args.timing, args.card)
    available = {s['scene'] for s in data['scenes']}
    selected = set(args.scene or available)
    if not selected <= available:
        parser.error('timing 파일에 없는 장면 번호')
    if args.plan:
        print_plan(data, selected)
        return 0
    from playwright.sync_api import sync_playwright
    args.out.mkdir(parents=True,exist_ok=True)
    if any(args.out.iterdir()):
        parser.error('출력 폴더가 비어 있지 않습니다. 기존 영상을 보관한 뒤 새 폴더를 지정하세요.')
    manifest = {'schema_version':4,'status':'recording','viewport':{'width':1920,'height':1080},
                'timing_file':str(args.timing),'cue_file':str(args.cues),'scenes':[],
                'timing':'clock0_video_s is a monotonic estimate only. 트리밍은 영상에서 플래시가 끝난 프레임을 찾아 그 시각을 clock0으로 쓴다 (마지막 흰 프레임 다음 프레임).' }
    def save():
        (args.out/'scenes.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    save()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader'])
            try:
                for scene in data['scenes']:
                    if scene['scene'] not in selected:
                        continue
                    context = browser.new_context(viewport=manifest['viewport'],device_scale_factor=1,
                        record_video_dir=str(args.out/'raw'),record_video_size=manifest['viewport'],locale='ko-KR')
                    row={'scene':scene['scene'],'title':scene.get('title', f"장면 {scene['scene']}"), 'duration_s':scene['duration_s'],'status':'preparing','cues':[],'samples':[]}
                    manifest['scenes'].append(row);save()
                    video=None
                    try:
                        page=context.new_page();video=page.video;started=time.monotonic()
                        page_errors=[]
                        page.on('pageerror', lambda error: page_errors.append(str(error)))
                        page.set_default_timeout(180000);page.set_default_navigation_timeout(180000)
                        prepare(page,scene,args,row['samples'])
                        # Fast pages (file:// card) can reach this point while the
                        # screencast still paints a partial surface; let it settle so
                        # the flash covers the whole 1920x1080 frame.
                        page.wait_for_timeout(1000)
                        # Editing sync marker. Browser timestamps keep the 0.3 s
                        # interval independent of Python/Playwright round trips.
                        # A white page (theme=light) hides a white flash; use black there.
                        flash_color='#000000' if args.theme=='light' else '#ffffff'
                        marker=page.evaluate("""(color) => new Promise(resolve=>{
                          const el=document.createElement('div');el.id='v2-sync-flash';
                          el.style.cssText='position:fixed;inset:0;background:'+color+';z-index:2147483647;pointer-events:none';
                          requestAnimationFrame(()=>{
                            document.documentElement.append(el);
                            const shown=performance.now();
                            setTimeout(()=>{
                              el.remove();const removed=performance.now();
                              requestAnimationFrame(()=>requestAnimationFrame(()=>
                                resolve({shown,removed,clock0:performance.now()})));
                            },300);
                          });
                        })""", flash_color)
                        clock0=time.monotonic();deadline=clock0+scene['duration_s']
                        # Map browser intervals onto the started-relative monotonic
                        # clock; video timestamps are measured later by trim_v2.py.
                        row['sync_flash']={key+'_s':clock0-started-(marker['clock0']-marker[key])/1000
                                           for key in ('shown','removed')}
                        row['sync_flash']['color']=flash_color
                        row.update(clock0_video_s=clock0-started,status='recording');save()
                        for cue in scene['cues']:
                            page.wait_for_timeout(max(0,clock0+cue['t']-time.monotonic())*1000)
                            actual=time.monotonic()-clock0
                            event={**cue,'actual_s':actual,'late_s':max(0,actual-cue['t']),'status':'running'}
                            row['cues'].append(event);save()
                            try:
                                remaining=deadline-time.monotonic()
                                if remaining<=0:
                                    raise TimeoutError('장면 길이 초과')
                                page.set_default_timeout(remaining*1000)
                                execute(page,cue,data['targets'],row['samples'])
                                if page_errors:
                                    raise RuntimeError('페이지 JS 오류: '+ '; '.join(page_errors))
                                event['status']='complete'
                            except Exception as exc:
                                event.update(status='failed',error=str(exc));raise
                            finally:
                                event['ended_s']=time.monotonic()-clock0;save()
                        if time.monotonic()>deadline:
                            raise TimeoutError('cue가 장면 길이를 초과함')
                        page.wait_for_timeout(max(0,deadline-time.monotonic())*1000)
                        if page_errors:
                            raise RuntimeError('페이지 JS 오류: '+ '; '.join(page_errors))
                        row.update(status='complete',cue_elapsed_s=time.monotonic()-clock0)
                    except Exception as exc:
                        row.update(status='failed',error=str(exc));raise
                    finally:
                        context.close()
                        if video:
                            filename=f"scene{scene['scene']:02d}.webm"
                            video.save_as(str(args.out/filename));video.delete();row['file']=filename
                        save()
            finally:
                browser.close()
        manifest['status']='complete';save();return 0
    except Exception as exc:
        manifest.update(status='failed',error=str(exc));save()
        print(f'녹화 중단: {exc}',file=sys.stderr);return 1


if __name__ == '__main__':
    raise SystemExit(main())
