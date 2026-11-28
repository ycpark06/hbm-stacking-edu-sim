"""Actual Pages HMI recording; browser-independent numeric/firmware contracts."""
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def reference_values():
    reps = json.loads((ROOT/'sim/test/stage4_results.json').read_text())['representative']
    s1 = next(s for s in reps if s['id'] == 'S1')
    s4 = next(s for s in reps if s['id'] == 'S4')
    tc = next(r for r in s1['results'] if r['recipe']['mode'] == 'TC-NCF' and not r['recipe'].get('head_temp_compensation'))
    cycles = {r['recipe']['mode']: r['cycle']['bonder_s'] for r in s4['results']}
    return {'peaks': [l['bond_peak_C'] for l in tc['thermal_layers'][:2]], 'cycles': cycles}


def check_results(observed):
    """Compare rendered DOM numbers against 6-significant-digit hmi_display.fmt."""
    expected = reference_values()
    checks = []
    for mode in ('TC-NCF', 'MR-MUF'):
        checks.append((f'{mode}.bonder_s', observed['cycles'][mode], expected['cycles'][mode]))
    for i, peak in enumerate(expected['peaks']):
        checks.append((f'TC-NCF.layer{i+1}.bond_peak_C', observed['peaks'][i], peak))
    rows = [{'key':k, 'observed':v, 'reference':r, 'display_expected':float(format(r,'.6g')),
             'passed':math.isfinite(v) and v == float(format(r,'.6g'))} for k,v,r in checks]
    if observed['alarm_layers'] != [1,2]:
        rows.append({'key':'BOND_TEMP_LOW.layers', 'observed':observed['alarm_layers'], 'reference':[1,2], 'passed':False})
    else:
        rows.append({'key':'BOND_TEMP_LOW.layers', 'observed':[1,2], 'reference':[1,2], 'passed':True})
    return rows


READ_RESULTS = r"""() => {
 const number = text => {const n=Number(text.trim().match(/^[-+\d.eE]+/)?.[0]);
   if(!Number.isFinite(n))throw Error('숫자 DOM 형식: '+text);return n;};
 const cards=[...document.querySelectorAll('#results article.result')];
 if(cards.length!==2)throw Error('두 모드 결과 카드 필요');
 const cycles={},peaks=[];
 for(const card of cards){
   const title=card.querySelector('h3').textContent;
   const mode=title.startsWith('TC-NCF')?'TC-NCF':title.startsWith('MR-MUF')?'MR-MUF':null;
   if(!mode||mode in cycles)throw Error('모드 카드 오류');
   const dt=[...card.querySelectorAll('dt')].find(e=>e.textContent==='본더 점유');
   cycles[mode]=number(dt.nextElementSibling.textContent);
   if(mode==='TC-NCF')for(const row of [...card.querySelectorAll('table tbody tr')].slice(0,2))
     peaks.push(number(row.cells[1].textContent));
 }
 const alarm_layers=[...document.querySelectorAll('#model-alarms .alarm')]
   .filter(e=>e.textContent.includes('TC-NCF')&&e.textContent.includes('BOND_TEMP_LOW'))
   .map(e=>Number(e.textContent.match(/층\s+(\d+)/)?.[1]));
 return {cycles,peaks,alarm_layers};
}"""


def verify_results(page, samples, phase):
    sample = {'phase':phase, 'passed':False, 'url':page.url, 'reference':'sim/test/stage4_results.json: S1 / S4 representative'}
    samples.append(sample)
    sample['observed'] = page.evaluate(READ_RESULTS)
    sample['checks'] = check_results(sample['observed'])
    sample['passed'] = all(c['passed'] for c in sample['checks'])
    if not sample['passed']:
        raise RuntimeError('HMI 결과 DOM 수치 불일치: '+json.dumps(sample,ensure_ascii=False))


def firmware_state(text):
    patterns = [r'래치\s+(\d+)', r'헤드\s+([\d.]+)\s*W', r'척\s+([\d.]+)\s*W']
    values = [re.search(pattern,text) for pattern in patterns]
    if not all(values):
        raise RuntimeError('펌웨어 상태 DOM 형식 변경: '+text)
    return tuple(float(v[1]) for v in values)


def verify_firmware(page, samples, phase, latched):
    text = page.locator('#firmware-status').inner_text()
    latch, head, chuck = firmware_state(text)
    passed = bool(latch) == latched and (not latched or head == chuck == 0)
    samples.append({'phase':phase,'text':text,'latched':latch,'head_W':head,'chuck_W':chuck,'passed':passed})
    if not passed:
        raise RuntimeError('인터락 DOM 검증 실패: '+text)


def select_recipe(page, mode):
    page.locator('[name="mode"]').select_option(mode)
    page.locator('[name="layers"]').select_option('12')


def run_cached(page, mode):
    select_recipe(page, mode)
    before = page.evaluate('hmiRecording.hits')
    page.locator('#run').click()
    if page.evaluate('hmiRecording.hits') != before+1 or page.locator('body').get_attribute('data-hmi-state') != 'done':
        raise RuntimeError('즉시 HMI 캐시 재생 실패')


def prepare_hmi(page, prep, samples):
    page.add_init_script(path=str(Path(__file__).with_name('hmi_recording.js')))
    response = page.goto(prep['url'], wait_until='load')
    if not response or not response.ok:
        raise RuntimeError('Pages HMI HTTP 오류')
    page.locator('body[data-hmi-ready="true"]').wait_for()
    page.locator('#fault-buttons [data-action="hardware"]').wait_for()
    page.wait_for_function("() => document.querySelector('#viewer canvas') && !document.querySelector('#model-state').textContent.includes('초기화 중')")
    page.evaluate('() => document.fonts.ready')
    initial = page.evaluate("() => Object.fromEntries(['results','charts','model-alarms','description','result-choice','status'].map(id=>[id,document.getElementById(id).innerHTML]))")
    for mode in prep['cache_modes']:
        select_recipe(page, mode)
        page.locator('#run').click()
        page.wait_for_function("() => ['done','error'].includes(document.body.dataset.hmiState)")
        if page.locator('body').get_attribute('data-hmi-state') != 'done':
            raise RuntimeError(page.locator('#recipe-error').inner_text())
        verify_results(page, samples, 'prepare '+mode)
    if page.evaluate('hmiRecording.cache.size') != 2:
        raise RuntimeError('12단 두 모드 캐시 누락')
    # start() resets the actual viewer/SIL; replay only the cached done message
    # here so the initial screen has no stale last-layer 3D state or results.
    select_recipe(page, 'TC-NCF')
    page.evaluate('() => {hmiRecording.armed=true;hmiRecording.resetOnly=true;}')
    page.locator('#run').click()
    page.evaluate('hmiRecording.resetOnly=false')
    page.evaluate("initial=>{for(const [id,html]of Object.entries(initial))document.getElementById(id).innerHTML=html;delete document.body.dataset.hmiState;document.querySelector('#progress').value=0;}",initial)
    page.locator('[name="mode"]').select_option('TC-NCF')
    page.locator('[name="layers"]').select_option('8')
    page.add_style_tag(content='[data-v5-focus]{outline:4px solid #14365A!important;outline-offset:4px}html{scroll-padding-bottom:240px}body{padding-bottom:240px}')
    page.evaluate('window.scrollTo(0,0)')


def execute_hmi(page, cue, targets, samples):
    step = cue['args']['step']
    selector = targets[cue['args']['target']]['selector']
    focus = lambda selectors: page.evaluate('s=>hmiRecording.focus(s)',selectors)
    if step == 'home':
        focus([selector]);page.evaluate('window.scrollTo(0,0)')
    elif step == 'run':
        focus(['#recipe']);run_cached(page,'TC-NCF')
        verify_results(page,samples,'sentence 48 TC-NCF')
    elif step == 'charts':
        page.locator('#result-choice').select_option('0')
        focus(['#charts figure:nth-child(1)','#charts figure:nth-child(2)'])
    elif step == 'alarms':
        focus([selector]);verify_results(page,samples,'sentence 50 alarms')
    elif step == 'compare':
        focus(['#recipe']);run_cached(page,'MR-MUF')
        verify_results(page,samples,'sentence 51 MR-MUF comparison');focus([selector])
    elif step == 'fault':
        focus(['#fault-buttons','#firmware-status'])
        for action, label, latched in [('hardware','hardware fault',True),('reset','reset refused',True),('clear','cause cleared; still latched',True),('reset','manual reset',False)]:
            page.locator(f'#fault-buttons [data-action="{action}"]').click()
            verify_firmware(page,samples,label,latched)
            page.wait_for_timeout(750)
        # Actual recipe button after reset demonstrates available operation again.
        run_cached(page,'MR-MUF');focus(['#firmware-status'])
        verify_results(page,samples,'after reset restart')
    elif step == 'normal':
        focus([selector]);verify_firmware(page,samples,'closing normal',False)
    else:
        raise ValueError('HMI step: '+step)
    samples.append({'phase':step,'cache':page.evaluate('({hits:hmiRecording.hits,misses:hmiRecording.misses,entries:hmiRecording.cache.size})')})
