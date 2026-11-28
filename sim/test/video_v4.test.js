import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import vm from 'node:vm';
const root=new URL('../../',import.meta.url),read=p=>readFileSync(new URL(p,root),'utf8');
const cues=JSON.parse(read('media/tools/cues_v4.json'));
test('v4 cues cover narration, panel explanations and sentence-relative GitHub transitions',()=>{
  assert.deepEqual(cues.scenes.map(s=>s.cues.filter(c=>'sentence' in c).length),[5,10,7,9,9,1,6]);
  const factory=cues.scenes.flatMap(s=>s.cues).filter(c=>c.action==='factory');
  assert.deepEqual(factory.filter(c=>c.args.js.includes('showPanel(true)')).map(c=>c.sentence),[26,27,28,35,38,39]);
  assert.ok(factory.every(c=>c.panel_reason&&/showPanel\((true|false)\)/.test(c.args.js)));
  assert.ok(factory.find(c=>c.sentence===24).args.js.includes("label:'하부 카메라 · 칩 위치 확인'"));
  const last=cues.scenes.at(-1);
  assert.equal(last.prepare.pages.length,5);
  assert.deepEqual(last.cues.map(c=>c.args.page),['repo','prs','issue','folders','pages','pages']);
  assert.deepEqual(last.cues.map(c=>c.at_sentence),[1,2,3,4,5,6]);
  assert.equal(last.cues.at(-1).script_sentence,42);
  assert.equal(last.cues.at(-1).sentence,47);
});
test('recording mask removes absolute and relative dates without changing process values',()=>{
  const context={};vm.runInNewContext(read('media/tools/github_mask.js'),context);
  const mask=context.recordingMask.maskDateText;
  for(const date of ['2026-11-28','2026/11/28','2026.11.28','2026-11-28T09:30:00Z','Nov 28, 2026','28 November 2026','2 hours ago','an hour ago','yesterday','2026년 11월 28일','3시간 전']){
    const actual=mask(date);assert.ok(!/[0-9A-Za-z가-힣]/.test(actual),`${date}: ${actual}`);
  }
  for(const value of ['40 N','300 ℃','250 ℃','1 MPa','175 ℃','firmware cad wiring docs'])assert.equal(mask(value),value);
});
test('plan accepts measured arbitrary durations and rejects mismatched timing without Playwright',()=>{
  const folder=mkdtempSync(join(tmpdir(),'video-v4-test-'));
  try{
    const timing=cues.scenes.map(s=>{
      const main=s.cues.filter(c=>'sentence' in c),end=s.scene<=5?main.at(-1).t+8:main.length*8+1;
      return {scene:s.scene,video_s:end,sentences:main.length,subs:main.map(c=>c.sub),timing:main.map((c,i)=>[c.t??(.5+i*8),(c.t??(.5+i*8))+.25])};
    });
    // These are synthetic validation fixtures, never claimed to be SunHi measurements.
    const path=join(folder,'fixture.json');
    const run=()=>spawnSync('python',['media/tools/record_v2.py','--plan','--cues','media/tools/cues_v4.json','--card','media/tools/compare_card_light.html','--timing',path],{cwd:root,encoding:'utf8'});
    writeFileSync(path,JSON.stringify(timing));let result=run();assert.equal(result.status,0,result.stderr);assert.match(result.stdout,/7장면 \/ 47문장/);
    timing.at(-1).subs[0]='불일치';writeFileSync(path,JSON.stringify(timing));result=run();assert.notEqual(result.status,0);assert.match(result.stderr,/자막 대응 오류/);
    // The same validator handles any scene count read from a timing file.
    const subset=join(folder,'subset.json');writeFileSync(subset,JSON.stringify({...cues,scenes:cues.scenes.slice(0,1)}));writeFileSync(path,JSON.stringify(timing.slice(0,1)));
    result=spawnSync('python',['media/tools/record_v2.py','--plan','--cues',subset,'--card','media/tools/compare_card_light.html','--timing',path],{cwd:root,encoding:'utf8'});
    assert.equal(result.status,0,result.stderr);assert.match(result.stdout,/1장면 \/ 5문장/);
  }finally{rmSync(folder,{recursive:true,force:true});}
});
