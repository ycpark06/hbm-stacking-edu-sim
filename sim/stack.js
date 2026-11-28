import {buildStack,stackSim,tcncfSchedule,mrmufSchedule} from './thermal.js';
import {stackWarpHistory,thermalWarpSteps,judgeWarpage} from './warpage.js';
import {stackNcf} from './ncf.js';
import {stackFillTime} from './muf.js';
import {stackOffset,selfAlign,selfAlignCoefficients} from './alignment.js';
import {stackCycleTime} from './cycle.js';
import {makeRng} from './rng.js';

const inRange=(v,p)=>Number.isFinite(v)&&v>0&&(!p.range||(v>=p.range[0]&&v<=p.range[1]));
export function judgeDefect(pct,params) {
  if(!Number.isFinite(pct)||pct<0||pct>100)throw new RangeError('defect percentage');
  const j=params.judgement;
  return pct>j.defect_fail_above_pct.value?'불량':pct>j.defect_good_max_pct.value?'주의':'양호';
}
/** Strict boundary: equality to liquidus is acceptable; no rounding/tolerance. */
export function judgeBondTemperature(peak_C,params) {
  if(!Number.isFinite(peak_C))throw new RangeError('bond peak temperature');
  const liquidus_C=params.solder.liquidus_snag.value;
  return {bond_temp_ok:peak_C>=liquidus_C,bond_peak_C:peak_C,
    liquidus_C,shortfall_C:Math.max(0,liquidus_C-peak_C)};
}
// Own bond includes ramp/hold/cool and their endpoints; later reheat cannot
// rescue an under-temperature bond. MR uses only the reflow exposure.
function bondPeaks(thermal,mode,N) {
  const peaks=Array(N).fill(-Infinity);
  for(const row of thermal.history) {
    if(mode==='TC-NCF'&&row.phase.startsWith('bond-')) {
      const i=row.T.length-1;peaks[i]=Math.max(peaks[i],row.T[i]);
    } else if(mode==='MR-MUF'&&row.phase.startsWith('reflow-'))
      row.T.forEach((T,i)=>{peaks[i]=Math.max(peaks[i],T);});
  }
  return peaks;
}
/** Sequential prefix simulations keep all earlier settings fixed. Numerical
 * solver constants: head bracket <=0.05 C, at most 64 bracket expansions and
 * 64 bisections per layer. An infeasible setting is estimated for reporting
 * only; no above-KPI recipe is executed as an accepted result. */
function compensateHeads(model,N,p) {
  const target_C=p.solder.liquidus_snag.value+p.judgement.bond_temp_margin_C.value;
  const limit_C=p.equipment_limits.head_max_temp_C.value;
  const head_setpoints_C=[],layers=[];
  const metadata={enabled:true,target_C,limit_C,tolerance_C:0.05,max_iterations:64,
    head_setpoints_C,layers};
  for(let n=1;n<=N;n++) {
    // Rebuild capacity and conductances for this prefix, including tool contact.
    const active=buildStack({...model,layers:model.layers.slice(0,n),params:p});
    const peak=head=>bondPeaks(stackSim(active,tcncfSchedule(n,p,[...head_setpoints_C,head])),'TC-NCF',n)[n-1];
    let lo=p.tcncf_process.stage_temp.value,hi=limit_C;
    if(!(hi>lo))throw new RangeError('head limit above stage');
    let upperPeak=peak(hi);
    const overLimit=upperPeak<target_C;
    let expansions=0;
    while(upperPeak<target_C&&expansions<metadata.max_iterations) {
      hi=lo+2*(hi-lo);expansions++;upperPeak=peak(hi);
    }
    if(upperPeak<target_C)throw new RangeError('head compensation bracket did not converge');
    let iterations=0;
    while(hi-lo>metadata.tolerance_C&&iterations<metadata.max_iterations) {
      const mid=(lo+hi)/2;
      if(peak(mid)<target_C)lo=mid;else hi=mid;
      iterations++;
    }
    if(hi-lo>metadata.tolerance_C)throw new RangeError('head compensation bisection did not converge');
    // Use midpoint for feasible roots; keep <= limit when the exact root is
    // within the last bracket of the KPI. Exceedance is decided by peak(limit).
    const required_head_C=overLimit?hi:Math.min(limit_C,(lo+hi)/2);
    layers.push({layer:n,required_head_C,headroom_C:limit_C-required_head_C,iterations,expansions});
    if(overLimit)return {...metadata,rejection:{code:'HEAD_TEMP_LIMIT',
      reason:'층별 접합 목표에 필요한 헤드 온도가 원문 KPI 최고 온도를 초과함',
      layer:n,required_head_C,limit_C}};
    head_setpoints_C.push(required_head_C);
  }
  return metadata;
}
/** Browser-safe, synchronous, pure calculation. recipe={mode?,layers?,
 * thickness_um?,gap_um?,inlet_pressure_MPa? (0 enables capillary comparison),
 * bond_force_N?,seed?,alignment_reference?,head_temp_compensation? (default false)}.
 * Full thermal/warp histories returned; tests store compact summaries only.
 */
export function runStack(mode,recipe={},params) {
  if(!['TC-NCF','MR-MUF'].includes(mode)||recipe.mode&&recipe.mode!==mode)throw new RangeError('stack mode');
  const p=structuredClone(params),g=p.geometry;
  const r={mode,layers:recipe.layers??p.recipe.layers.value,thickness_um:recipe.thickness_um??g.die_thickness.value,
    gap_um:recipe.gap_um??g.interlayer_gap.value,inlet_pressure_MPa:recipe.inlet_pressure_MPa??p.muf.applied_pressure.value,bond_force_N:recipe.bond_force_N??p.tcncf_process.bond_force.value,
    head_temp_compensation:recipe.head_temp_compensation??false,seed:recipe.seed??p.alignment.mc_seed.value,alignment_reference:recipe.alignment_reference??p.recipe.alignment_reference.value};
  if(!Number.isInteger(r.layers)||!inRange(r.layers,p.recipe.layers)||!inRange(r.thickness_um,g.die_thickness)||
    !inRange(r.gap_um,g.interlayer_gap)||!inRange(r.bond_force_N,p.tcncf_process.bond_force)||!Number.isInteger(r.seed))throw new RangeError('stack recipe');
  if(typeof r.head_temp_compensation!=='boolean')throw new RangeError('head compensation boolean');
  if(!Number.isFinite(r.inlet_pressure_MPa)||r.inlet_pressure_MPa<0)throw new RangeError('inlet pressure');
  p.muf.applied_pressure.value=r.inlet_pressure_MPa;
  g.interlayer_gap.value=r.gap_um;g.die_thickness.value=r.thickness_um;p.tcncf_process.bond_force.value=r.bond_force_N;
  const model=buildStack({layers:Array.from({length:r.layers},()=>({mode,thickness_um:r.thickness_um})),params:p});
  const head_compensation=mode==='TC-NCF'&&r.head_temp_compensation?compensateHeads(model,r.layers,p):
    {enabled:false,requested:r.head_temp_compensation,note:mode==='MR-MUF'?'MR-MUF는 리플로우 피크 검사만 기록':'기본 레시피'};
  if(head_compensation.rejection)return {recipe:r,accepted:false,rejection:head_compensation.rejection,head_compensation,alarms:[]};
  const head_setpoints_C=mode==='TC-NCF'?(head_compensation.head_setpoints_C??Array(r.layers).fill(p.tcncf_process.head_setpoint.value)):null;
  const thermal=stackSim(model,mode==='TC-NCF'?tcncfSchedule(r.layers,p,head_setpoints_C):mrmufSchedule(r.layers,p));
  const peaks=bondPeaks(thermal,mode,r.layers),alarms=[];
  thermal.layers.forEach((layer,i)=>{
    Object.assign(layer,judgeBondTemperature(peaks[i],p),{head_setpoint_C:head_setpoints_C?.[i]??null});
    if(mode==='TC-NCF'&&!layer.bond_temp_ok)alarms.push({code:'BOND_TEMP_LOW',message:'접합 온도 미달',
      layer:i+1,peak_C:layer.bond_peak_C,shortfall_C:layer.shortfall_C,liquidus_C:layer.liquidus_C});
  });
  // Existing mechanical-stage API consumes seconds. params retains PMC hours.
  const mechanicalParams={...p,muf:{...p.muf,cure_time:{...p.muf.cure_time,value:p.muf.cure_time.value*3600}}};
  const warpHistory=stackWarpHistory(thermalWarpSteps(thermal,{...model,params:mechanicalParams}));
  const max_um=warpHistory.reduce((v,row)=>Math.max(v,Math.abs(row.w_um)),0);
  const ncf=mode==='TC-NCF'?stackNcf(thermal,p):null;
  const muf=mode==='MR-MUF'?stackFillTime(Array(r.layers).fill(r.gap_um*1e-6),{params:p}):null;
  const tack=stackOffset({N:r.layers,reference:r.alignment_reference,params:p,rng:makeRng(r.seed)});
  const coefficients=mode==='MR-MUF'?selfAlignCoefficients(r.thickness_um,p):null;
  const residual=errors=>errors.map((xy,i)=>xy.map(x0_um=>selfAlign({x0_um,...coefficients,t_liquid_s:thermal.layers[i].time_above_s}).x_um));
  const layer_errors_um=coefficients?residual(tack.layer_errors_um):tack.layer_errors_um;
  const positions_um=[];
  for(const xy of layer_errors_um)positions_um.push(xy.map((v,j)=>v+(positions_um.at(-1)?.[j]??0)));
  let adjacent_3sigma_um=tack.adjacent_sigma_um.map(s=>3*s),mc=null;
  if(coefficients) {
    // Nonlinear dry friction: estimate final adjacent distributions, preserving
    // substrate-reference neighbour covariance by drawing complete stacks.
    const rng=makeRng(p.alignment.mc_seed.value),samples=p.alignment.mc_samples.value;
    const mean=Array.from({length:r.layers},()=>[0,0]),M2=mean.map(()=>[0,0]);
    for(let n=1;n<=samples;n++) {
      const errors=residual(stackOffset({N:r.layers,reference:r.alignment_reference,params:p,rng}).layer_errors_um);
      errors.forEach((xy,i)=>xy.forEach((v,j)=>{const d=v-mean[i][j];mean[i][j]+=d/n;M2[i][j]+=d*(v-mean[i][j]);}));
    }
    const sigma=M2.map(xy=>xy.map(v=>Math.sqrt(v/(samples-1))));
    adjacent_3sigma_um=sigma.map(xy=>3*Math.max(...xy));mc={samples,seed:p.alignment.mc_seed.value,mean_um:mean,sigma_um:sigma};
  }
  const target=p.judgement.alignment_layer_3sigma_um.value;
  const alignment={tack,coefficients,layer_errors_um,positions_um,cumulative_um:positions_um.at(-1),
    top_to_first_die_um:positions_um.at(-1).map((v,j)=>v-positions_um[0][j]),adjacent_3sigma_um,
    judgement:adjacent_3sigma_um.every(x=>x<=target)?'양호':'불량',mc,
    note:'층간 축별 3σ 설계 목표; MR은 비정규 잔여의 MC 표준편차 지표(99.7% 보장 아님). 누적 표본은 관찰값.'};
  const defect_area_pct=muf?100*muf.unfilled_fraction:null;
  const tendencies=ncf?[...new Set(ncf.map(l=>l.tendency.grade))]:[];
  const cycle=stackCycleTime(mode,r.layers,{params:p});
  if(head_compensation.enabled) {
    // Same ramp rate and hold/cool durations: only ramp duration changes.
    const per_layer=head_setpoints_C.map(head=>stackCycleTime(mode,1,{params:{...p,
      tcncf_process:{...p.tcncf_process,head_setpoint:{...p.tcncf_process.head_setpoint,value:head}}}}));
    cycle.bonder_s=per_layer.reduce((sum,c)=>sum+c.bonder_s,0);
    cycle.total_serial_s=cycle.bonder_s+cycle.batch_post_s;
    cycle.breakdown.by_layer=per_layer.map((c,i)=>({layer:i+1,...c.breakdown.per_layer}));
    cycle.breakdown.per_layer_s=cycle.bonder_s/r.layers;
    cycle.breakdown.layer_totals=Object.fromEntries(Object.keys(per_layer[0].breakdown.layer_totals)
      .map(k=>[k,per_layer.reduce((sum,c)=>sum+c.breakdown.layer_totals[k],0)]));
    cycle.breakdown.per_layer=Object.fromEntries(Object.entries(cycle.breakdown.layer_totals).map(([k,v])=>[k,v/r.layers]));
    cycle.breakdown.per_layer_note='보정 레시피는 층 평균; 실제 층별 시간은 by_layer';
    cycle.breakdown.all_layers_s=cycle.bonder_s;
  }
  return {recipe:r,accepted:true,rejection:null,head_compensation,head_setpoints_C,alarms,thermal,warpage:{max_um,judgement:judgeWarpage(max_um,r.gap_um,p),history:warpHistory},ncf,muf,alignment,
    defect_area_pct,defect_judgement:muf?(muf.filler_blocked?'불량(필러 막힘)':judgeDefect(defect_area_pct,p)):`정량 모델 없음 (경향: ${tendencies.join(', ')})`,
    contact_judgement:ncf?(ncf.every(l=>l.contact_time_s!==null&&!l.gel_before_contact)?'접촉':'미접촉/접촉 전 겔화'):'정량 접촉 모델 없음 (자기정렬은 젖음·접촉 가정)',
    cycle,
    observations:{layers:thermal.layers,vendor_claims:p.vendor_claims,
      void_model:'정량 보이드 모델 없음; MR 결함 면적률은 미충전만 포함',
      alignment_limit:'독립 층간 좌표·일정 강성·작은 변위; 스택 연성 운동·tack 재응고·회전은 미포함'}};
}

export function summarizeStack(result) {
  if(result.accepted===false)return structuredClone(result);
  const {recipe,thermal,warpage,alignment,cycle,defect_area_pct,defect_judgement,contact_judgement,muf,ncf}=result;
  return {recipe,accepted:result.accepted,rejection:result.rejection,head_compensation:result.head_compensation,
    head_setpoints_C:result.head_setpoints_C,alarms:result.alarms,thermal_layers:thermal.layers,warpage:{max_um:warpage.max_um,judgement:warpage.judgement},
    defect_area_pct,defect_judgement,contact_judgement,
    alignment:{layer_errors_um:alignment.layer_errors_um,cumulative_um:alignment.cumulative_um,
      top_to_first_die_um:alignment.top_to_first_die_um,adjacent_3sigma_um:alignment.adjacent_3sigma_um,judgement:alignment.judgement},
    cycle,muf,ncf:ncf?.map(({history,cure_history,...l})=>l)??null};
}
