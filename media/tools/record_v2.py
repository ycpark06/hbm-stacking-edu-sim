#!/usr/bin/env python3
"""Record six narration-aligned v2 scenes. --plan never imports Playwright."""
import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[2]
TIMING = Path.home() / 'Desktop/MSE489/기말보고서/영상/v2/tts/timing.json'
TITLES = ['도입', '원리 비교', '장비 구성(CAD)', '공장 동작 · TC-NCF', '공장 동작 · MR-MUF', '정리']
ACTIONS = {'factory', 'card', 'cad', 'cad_click', 'cad_explode', 'cad_scroll', 'drag_rotate', 'wait'}


def load_plan(cues_path, timing_path, card_path):
    data = json.loads(cues_path.read_text(encoding='utf-8'))
    timing = json.loads(timing_path.read_text(encoding='utf-8'))
    if [s['scene'] for s in data['scenes']] != list(range(1, 7)) or [s['scene'] for s in timing] != list(range(1, 7)):
        raise ValueError('장면 번호·순서: 1..6 필요')
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
        for cue, (start, _) in zip(main, ts['timing']):
            if not 0 <= start-cue['t'] <= .201 or cue['sub'] != ts['subs'][cue['sentence']-sentence-1]:
                raise ValueError('문장 시작 시각·자막 대응 오류')
        previous = -1
        prep = scene['prepare']
        if prep['page'] not in ('factory', 'cad', 'card'):
            raise ValueError('준비 페이지 오류')
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
                        'cad_explode':'cad', 'cad_scroll':'cad', 'drag_rotate':'cad'}
            if cue['action'] in page_for and prep['page'] != page_for[cue['action']]:
                raise ValueError('cue 페이지 불일치')
            if a.get('target') not in data['targets']:
                raise ValueError('대상 참조 없음')
            if cue['action'] not in data['targets'][a['target']]['actions']:
                raise ValueError('대상·동작 불일치')
            if cue['action'] in ('factory', 'card', 'cad') and not isinstance(a.get('js'), str):
                raise ValueError('JS 문자열 필요')
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
    if sentence != 42:
        raise ValueError('전체 문장 수 42 필요')
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
            detail = a.get('js', data['targets'][a['target']]['label'])
            if 'motion' in a:
                detail += ' ' + json.dumps(a['motion'], ensure_ascii=False)
            print(f"| {s['scene']} · 문장 {c.get('sentence', '보조')} | {c['t']:.3f} | {c['action']} | {detail.replace('|', '/')} |")
    print(f"검증 통과: 6장면 / 42문장 / 전체 {sum(s['duration_s'] for s in data['scenes'])} s (준비 제외)")


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


def execute(page, cue, targets):
    a, action = cue['args'], cue['action']
    if action == 'factory':
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


def prepare(page, scene, args):
    suffix = '?theme=light' if args.theme == 'light' else ''
    prep = scene['prepare']
    if prep['page'] == 'card':
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
        page.evaluate('p=>{const f=window.factory;f.setViewOnly(true);f.setMode(p.mode);f.pause();f.setSpeed(1);f.setStage(p.stage,0);f.setCamera(p.camera);}', prep)
    if args.theme == 'light' and prep['page'] in ('factory', 'cad'):
        api = 'factory' if prep['page'] == 'factory' else 'cadPage'
        page.evaluate('(a)=>window[a.api].setTitle(a.title)', {'api':api,'title':TITLES[scene['scene']-1]})
    if args.captions and args.theme != 'light':
        page.evaluate('''title=>{const el=document.createElement('div');el.textContent=title;
        el.style.cssText='position:fixed;top:18px;left:24px;z-index:2147483647;background:#07111feb;color:white;padding:12px 28px;border:1px solid #60e0c0;border-radius:10px;font:24px system-ui;pointer-events:none;max-width:90vw';document.body.append(el);}''', TITLES[scene['scene']-1])
    page.evaluate('() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://localhost:8000/web/')
    parser.add_argument('--card', type=Path, default=Path(__file__).with_name('compare_card.html'))
    parser.add_argument('--timing', type=Path, default=TIMING)
    parser.add_argument('--cues', type=Path, default=Path(__file__).with_name('cues_v2.json'))
    parser.add_argument('--out', type=Path, default=ROOT/'media/out/v2')
    parser.add_argument('--scene', type=int, choices=range(1,7), action='append')
    parser.add_argument('--plan', action='store_true')
    parser.add_argument('--theme', choices=['light'])
    parser.add_argument('--captions', action='store_true')
    args = parser.parse_args()
    data = load_plan(args.cues, args.timing, args.card)
    selected = set(args.scene or range(1,7))
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
                    row={'scene':scene['scene'],'title':TITLES[scene['scene']-1], 'duration_s':scene['duration_s'],'status':'preparing','cues':[]}
                    manifest['scenes'].append(row);save()
                    video=None
                    try:
                        page=context.new_page();video=page.video;started=time.monotonic()
                        page_errors=[]
                        page.on('pageerror', lambda error: page_errors.append(str(error)))
                        page.set_default_timeout(180000);page.set_default_navigation_timeout(180000)
                        prepare(page,scene,args)
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
                                execute(page,cue,data['targets'])
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
