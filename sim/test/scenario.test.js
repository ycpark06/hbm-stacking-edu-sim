import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {runStack,summarizeStack} from '../stack.js';
import {scenarios,runScenario} from '../scenarios.js';
const params=JSON.parse(readFileSync(new URL('../params.json',import.meta.url),'utf8'));

// Signed temperature, position and curvature may be negative. Physical sizes,
// durations, fractions, counts and absolute maxima must be nonnegative.
function validTree(node,path='result') {
  if(typeof node==='number') {
    assert.ok(Number.isFinite(node),`${path}: finite`);
    if(/(?:_s|_m|thickness_um|gap_um|fraction|_pct|count|exposures|max_um|pressure_MPa)$/.test(path))
      assert.ok(node>=0,`${path}: nonnegative`);
  } else if(node&&typeof node==='object')for(const [k,v] of Object.entries(node))validTree(v,`${path}.${k}`);
}
function run(mode,recipe,p=params) {
  const full=runStack(mode,recipe,p);validTree(full);return summarizeStack(full);
}
const signature=r=>({warpage:r.warpage.judgement,defect:r.defect_judgement,contact:r.contact_judgement,alignment:r.alignment.judgement});

test('16 stacks, S1–S5 and endpoint sensitivity: record outcomes without fixing judgements',()=>{
  const results=[];
  for(const mode of ['TC-NCF','MR-MUF'])for(const layers of [2,4,8,12])for(const thickness_um of [100,50])
    results.push(run(mode,{layers,thickness_um}));
  assert.equal(results.length,16);
  const representative=scenarios.map(s=>runScenario(s.id,params));
  representative.forEach(valid=>validTree(valid));
  assert.equal(representative.find(s=>s.id==='S5').results.length,12);
  const alignment=representative.find(s=>s.id==='S2').results;
  assert.deepEqual(alignment[0].initial_alignment,alignment[1].initial_alignment);
  assert.throws(()=>runScenario('unknown',params));
  const cases=[
    {id:'A',mode:'TC-NCF',recipe:{layers:12,thickness_um:50}},
    {id:'B',mode:'MR-MUF',recipe:{gap_um:7}},
    {id:'C',mode:'TC-NCF',recipe:{layers:12,thickness_um:100}},
    {id:'D',mode:'MR-MUF',recipe:{layers:12,thickness_um:100}},
  ].map(c=>({...c,baseline:run(c.mode,c.recipe)}));
  const paths=[];const unswept=[];
  for(const [group,entries] of Object.entries(params)) {
    if(group==='_meta')continue;
    for(const [key,param] of Object.entries(entries)) {
      if(!['assumption','estimate'].includes(param.kind))continue;
      if(typeof param.value==='number'&&param.range)paths.push(`${group}.${key}`);
      else unswept.push({path:`${group}.${key}`,reason:'수치 range 없음; 새 범위를 가정하지 않음'});
    }
  }
  // Literature transfer time is explicitly requested in addition to assumptions.
  paths.push('cycle.mold_fill_time');
  const sensitivity=[];
  for(const path of paths) {
    const [group,key]=path.split('.'),param=params[group][key],rows=[];
    for(const value of [...new Set(param.range)]) {
      const p=structuredClone(params);p[group][key].value=value;
      for(const c of cases) {
        // Existing schedule requires cooling/handling time strictly after tack.
        // Record the incompatible endpoint, rather than changing another input.
        if(c.mode==='MR-MUF'&&p.cycle.mrmuf_tack_cycle_per_die.value<=p.mrmuf_process.tack_time.value) {
          rows.push({case:c.id,value,input_conflict:'tack cycle must include cooling/handling',changed:[]});continue;
        }
        const r=run(c.mode,c.recipe,p),before=signature(c.baseline),after=signature(r);
        rows.push({case:c.id,value,judgements:after,changed:Object.keys(before).filter(k=>before[k]!==after[k]),
          max_warp_um:r.warpage.max_um,defect_area_pct:r.defect_area_pct,
          max_adjacent_3sigma_um:Math.max(...r.alignment.adjacent_3sigma_um),
          contact_layers:r.ncf?.filter(l=>l.contact_time_s!==null&&!l.gel_before_contact).length??null,
          thermal_layers:r.thermal_layers,cycle:{bonder_s:r.cycle.bonder_s,batch_post_s:r.cycle.batch_post_s}});
      }
    }
    sensitivity.push({path,kind:param.kind,range:param.range,unit:param.unit,source:param.source,
      changed_cells:rows.reduce((s,r)=>s+r.changed.length,0),rows});
  }
  const baseline=JSON.parse(readFileSync(new URL('stage3_baseline_results.json',import.meta.url),'utf8'));
  const changed_cells=results.flatMap((r,i)=>{
    const before=signature(baseline.results[i]),after=signature(r);
    return Object.keys(before).filter(key=>before[key]!==after[key]).map(key=>({
      recipe:r.recipe,field:key,before:before[key],after:after[key]}));
  });
  const data={results,cases,changed_cells,sensitivity:sensitivity.sort((a,b)=>b.changed_cells-a.changed_cells),unswept};
  validTree(data);
  writeFileSync(new URL('scenario_results.json',import.meta.url),JSON.stringify(data,null,2)+'\n');
  writeFileSync(new URL('stage4_results.json',import.meta.url),JSON.stringify({representative},null,2)+'\n');
});
