import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import vm from 'node:vm';
const root=new URL('../../',import.meta.url),read=p=>readFileSync(new URL(p,root),'utf8');
const cues=JSON.parse(read('media/tools/cues_v5.json'));
const previous=JSON.parse(read('media/tools/cues_v4.json'));
test('v5 preserves first seven scenes and appends seven measured-relative live HMI cues',()=>{
  assert.deepEqual(cues.scenes.slice(0,6),previous.scenes.slice(0,6));
  assert.deepEqual(cues.scenes[6],{...previous.scenes[6],cues:previous.scenes[6].cues.slice(0,5)});
  assert.deepEqual(cues.scenes.map(s=>s.cues.filter(c=>'sentence'in c).length),[5,10,7,9,9,1,5,7]);
  const last=cues.scenes.at(-1);
  assert.equal(last.prepare.url,'https://ycpark06.github.io/hbm-stacking-edu-sim/web/index.html?theme=light');
  assert.deepEqual(last.cues.map(c=>c.at_sentence),[1,2,3,4,5,6,7]);
  assert.ok(last.cues.every(c=>c.action==='hmi'));
});
test('plan validates eight scenes without a browser and rejects missing cache mode or changed narration',()=>{
  const dir=mkdtempSync(join(tmpdir(),'video-v5-'));
  try{
    const timing=cues.scenes.map(s=>{
      const main=s.cues.filter(c=>'sentence'in c);
      const starts=main.map((c,i)=>c.t??(.5+i*8));
      return {scene:s.scene,video_s:starts.at(-1)+8,sentences:main.length,subs:main.map(c=>c.sub),timing:starts.map(t=>[t,t+.25])};
    });
    const tp=join(dir,'fixture.json'),cp=join(dir,'cues.json');
    writeFileSync(tp,JSON.stringify(timing));writeFileSync(cp,JSON.stringify(cues));
    const run=()=>spawnSync('python',['media/tools/record_v2.py','--plan','--cues',cp,'--timing',tp,'--card','media/tools/compare_card_light.html'],{cwd:root,encoding:'utf8'});
    let result=run();assert.equal(result.status,0,result.stderr);assert.match(result.stdout,/8장면 \/ 53문장/);
    const bad=structuredClone(cues);bad.scenes.at(-1).prepare.cache_modes.pop();writeFileSync(cp,JSON.stringify(bad));
    result=run();assert.notEqual(result.status,0);assert.match(result.stderr,/캐시 조건 오류/);
    writeFileSync(cp,JSON.stringify(cues));timing.at(-1).subs[0]='잘못된 자막';writeFileSync(tp,JSON.stringify(timing));
    result=run();assert.notEqual(result.status,0);assert.match(result.stderr,/자막 대응 오류/);
  }finally{rmSync(dir,{recursive:true,force:true});}
});
test('Worker cache retains real messages, rebinds request IDs and blocks uncached calculation during scene clock',()=>{
  let computations=0;
  class Worker {
    constructor(){this.listeners=[];}
    addEventListener(type,fn){if(type==='message')this.listeners.push(fn);}
    dispatchEvent(event){for(const fn of this.listeners)fn(event);this.onmessage?.(event);}
    postMessage(data){
      computations++;
      for(const message of [{type:'results',results:[{real:489}]},{type:'sil',sil:{F:[40]}},{type:'progress',layer:1},{type:'progress',layer:12},{type:'done'}])
        this.dispatchEvent({data:{...message,id:data.id}});
    }
  }
  const window={Worker},context={window,URL,location:{href:'https://test/web/'},MessageEvent:class {constructor(type,options){Object.assign(this,options);}}};
  vm.runInNewContext(read('media/tools/hmi_recording.js'),context);
  const w=new window.Worker('js/worker.js'),outputs=[];w.onmessage=e=>outputs.push(e.data);
  const tc={id:1,recipe:{mode:'TC-NCF',layers:12},params:{seed:489}};
  w.postMessage(tc);w.postMessage({...tc,id:2,recipe:{mode:'MR-MUF',layers:12}});
  assert.equal(computations,2);assert.equal(window.hmiRecording.cache.size,2);
  outputs.length=0;window.hmiRecording.armed=true;w.postMessage({...tc,id:3});
  assert.equal(computations,2);assert.equal(window.hmiRecording.hits,1);
  assert.deepEqual(outputs.map(o=>o.type),['results','sil','progress','done']);
  assert.ok(outputs.every(o=>o.id===3));assert.equal(outputs[0].results[0].real,489);assert.equal(outputs[2].layer,12);
  assert.throws(()=>w.postMessage({...tc,recipe:{mode:'TC-NCF',layers:8}}),/재계산 금지/);
  assert.equal(computations,2);
});
test('DOM number contract uses S1/S4 references and records failed checks before aborting',()=>{
  const script=`
import sys
sys.path.insert(0,'media/tools')
from hmi_recording import reference_values,check_results,verify_results,firmware_state
r=reference_values()
observed={'cycles':{k:float(format(v,'.6g')) for k,v in r['cycles'].items()},'peaks':[float(format(v,'.6g')) for v in r['peaks']],'alarm_layers':[1,2]}
assert all(x['passed'] for x in check_results(observed))
assert observed['peaks']==[208.54,215.848]
assert observed['cycles']=={'TC-NCF':239.886,'MR-MUF':40.686}
observed['cycles']['MR-MUF']=41
class Page:
 url='https://test/'
 def evaluate(self,js):return observed
samples=[]
try:verify_results(Page(),samples,'recorded cue')
except RuntimeError:pass
else:raise AssertionError('mismatch accepted')
assert samples and not samples[0]['passed']
assert firmware_state('경고 0 · 래치 1 · 헤드 0 W · 척 0 W')==(1,0,0)
try:firmware_state('invalid')
except RuntimeError:pass
else:raise AssertionError('bad firmware DOM accepted')
`;
  const result=spawnSync('python',['-c',script],{cwd:root,encoding:'utf8'});assert.equal(result.status,0,result.stderr);
});
