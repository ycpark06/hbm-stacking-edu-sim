import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {runStack,summarizeStack} from '../stack.js';
const params=JSON.parse(readFileSync(new URL('../params.json',import.meta.url),'utf8'));

// Record outcomes; no pass/fail judgement is locked to an expected result.
function validTree(node,path='result') {
  if(typeof node==='number') {
    assert.ok(Number.isFinite(node),`${path}: finite`);
    if(/(?:_s|_m|thickness_um|gap_um)$/.test(path))assert.ok(node>=0,`${path}: nonnegative thickness/time/length`);
  } else if(node&&typeof node==='object')for(const [k,v] of Object.entries(node))validTree(v,`${path}.${k}`);
}
function run(mode,recipe,p=params) {
  const full=runStack(mode,recipe,p);validTree(full);return summarizeStack(full);
}
const signature=r=>({warpage:r.warpage.judgement,defect:r.defect_judgement,contact:r.contact_judgement,alignment:r.alignment.judgement});

test('16 stack scenarios, representative cases and assumption endpoint sensitivity (record only)',()=>{
  const results=[];
  for(const mode of ['TC-NCF','MR-MUF'])for(const layers of [2,4,8,12])for(const thickness_um of [100,50])
    results.push(run(mode,{layers,thickness_um}));
  assert.equal(results.length,16);
  const cases=[
    {id:'A',mode:'TC-NCF',recipe:{layers:12,thickness_um:50},expected:'휨 불량 예상'},
    {id:'B',mode:'MR-MUF',recipe:{gap_um:7},expected:'결함 주의 또는 불량 예상'},
    {id:'C',mode:'TC-NCF',recipe:{layers:12,thickness_um:100},expected:'기본 비교'},
    {id:'D',mode:'MR-MUF',recipe:{layers:12,thickness_um:100},expected:'기본 비교'},
  ].map(c=>({...c,baseline:run(c.mode,c.recipe)}));
  const paths=['thermal_stack.tool_contact_R_area','thermal_stack.chuck_contact_R_area',
    'muf.viscosity_at_fill','solder.molten_height_for_alignment','muf.cure_time','ncf.gel_time_at_250C',
    'alignment.damping','alignment.resist_force','muf.applied_pressure'];
  const sensitivity=[];
  for(const path of paths) {
    const [group,key]=path.split('.'),param=params[group][key];
    assert.equal(param.kind,'assumption');
    // Existing range first; C1 contacts have no range field, but their source
    // explicitly proposes one decade each side. Record this choice with data.
    const range=param.range??[param.value/10,param.value*10];
    const rows=[];
    for(const value of range) {
      const p=structuredClone(params);p[group][key].value=value;
      for(const c of cases) {
        const r=run(c.mode,c.recipe,p),before=signature(c.baseline),after=signature(r);
        rows.push({case:c.id,value,judgements:after,changed:Object.keys(before).filter(k=>before[k]!==after[k]),
          max_warp_um:r.warpage.max_um,defect_area_pct:r.defect_area_pct,
          max_adjacent_3sigma_um:Math.max(...r.alignment.adjacent_3sigma_um),
          contact_layers:r.ncf?.filter(l=>l.contact_time_s!==null&&!l.gel_before_contact).length??null,
          cycle:{bonder_s:r.cycle.bonder_s,batch_post_s:r.cycle.batch_post_s}});
      }
    }
    sensitivity.push({path,range,unit:param.unit,source:param.source,
      range_basis:param.range?'params의 기존 range 양끝':'C1 source의 실측 부재에 따른 한 차수 아래·위',
      changed_cells:rows.reduce((s,r)=>s+r.changed.length,0),rows});
  }
  writeFileSync(new URL('scenario_results.json',import.meta.url),JSON.stringify({results,cases,
    sensitivity:sensitivity.sort((a,b)=>b.changed_cells-a.changed_cells)},null,2)+'\n');
});
