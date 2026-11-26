import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {runStack,summarizeStack} from '../stack.js';
import {washburnFillTime,pressureFillTime,unfilledFraction} from '../muf.js';
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

// Analytic boundaries, not adopted process inputs. Gap choices follow HANDOFF §1
// (20 um test chip); all material/process values and judgement limits use params.
function mrmufDefectBoundaries() {
  const mu=params.muf.viscosity_at_fill,L=params.geometry.die_size.value*1e-3;
  const opts={gamma:params.muf.surface_tension.value,theta_deg:params.muf.contact_angle.value};
  const allowed=params.cycle.mold_fill_time.value,pressureRange=params.muf.applied_pressure.range;
  const rows=[...new Set([params.geometry.interlayer_gap.range[0],
    params.geometry.interlayer_gap.value,20,params.geometry.interlayer_gap.range[1]])].map(gap_um=>{
    const h=gap_um*1e-6,fill=washburnFillTime(mu.value,L,h,opts);
    const boundaries=[['fail_to_caution',params.judgement.defect_fail_above_pct.value],
      ['caution_to_good',params.judgement.defect_good_max_pct.value]].map(([transition,pct])=>{
      const u=pct/100,time=fill*(1-u)**2;
      // Invert pressureFillTime with t_fill=t_allow/(1-u)^2.
      const pressure=6*mu.value*L**2*(1-u)**2/(h**2*allowed)
        -2*opts.gamma*Math.cos(opts.theta_deg*Math.PI/180)/h;
      const forward=pressureFillTime(mu.value,L,h,{...opts,dP_app_Pa:pressure});
      assert.ok(Math.abs(unfilledFraction(fill,time)-u)<1e-12,'time inverse recovers target fraction');
      assert.ok(Math.abs(unfilledFraction(forward,allowed)-u)<1e-12,'pressure inverse recovers target fraction');
      // Check both sides of each transition; do not fix a scenario judgement.
      assert.ok(unfilledFraction(fill,time*(1-1e-6))>u);
      assert.ok(unfilledFraction(fill,time*(1+1e-6))<u);
      assert.ok(unfilledFraction(pressureFillTime(mu.value,L,h,{...opts,dP_app_Pa:pressure*(1-1e-6)}),allowed)>u);
      assert.ok(unfilledFraction(pressureFillTime(mu.value,L,h,{...opts,dP_app_Pa:pressure*(1+1e-6)}),allowed)<u);
      return {transition,unfilled_pct:pct,allowed_time_s:time,applied_pressure_Pa:pressure,
        pressure_range_status:pressure>=pressureRange[0]&&pressure<=pressureRange[1]?'범위 내':'범위 밖'};
    });
    return {gap_um,capillary_fill_time_s:fill,boundaries,
      viscosity_endpoints:mu.range.map(mu_Pa_s=>({mu_Pa_s,capillary_fill_time_s:washburnFillTime(mu_Pa_s,L,h,opts)}))};
  });
  const result={basis:'Analytic inverses only; no new process assumption or params changes',
    flow_length_m:L,viscosity_Pa_s:mu.value,...opts,allowed_time_s:allowed,
    baseline_applied_pressure_Pa:params.muf.applied_pressure.value,pressure_range_Pa:pressureRange,rows};
  validTree(result);
  return result;
}

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
    'alignment.damping','alignment.resist_force','muf.applied_pressure','cycle.mold_fill_time'];
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
    sensitivity:sensitivity.sort((a,b)=>b.changed_cells-a.changed_cells),
    mrmuf_defect_boundaries:mrmufDefectBoundaries()},null,2)+'\n');
});
