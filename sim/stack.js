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
/** Browser-safe, synchronous, pure calculation. recipe={mode?,layers?,
 * thickness_um?,gap_um?,bond_force_N?,seed?,alignment_reference?}.
 * Full thermal/warp histories returned; tests store compact summaries only.
 */
export function runStack(mode,recipe={},params) {
  if(!['TC-NCF','MR-MUF'].includes(mode)||recipe.mode&&recipe.mode!==mode)throw new RangeError('stack mode');
  const p=structuredClone(params),g=p.geometry;
  const r={mode,layers:recipe.layers??p.recipe.layers.value,thickness_um:recipe.thickness_um??g.die_thickness.value,
    gap_um:recipe.gap_um??g.interlayer_gap.value,bond_force_N:recipe.bond_force_N??p.tcncf_process.bond_force.value,
    seed:recipe.seed??p.alignment.mc_seed.value,alignment_reference:recipe.alignment_reference??p.recipe.alignment_reference.value};
  if(!Number.isInteger(r.layers)||!inRange(r.layers,p.recipe.layers)||!inRange(r.thickness_um,g.die_thickness)||
    !inRange(r.gap_um,g.interlayer_gap)||!inRange(r.bond_force_N,p.tcncf_process.bond_force)||!Number.isInteger(r.seed))throw new RangeError('stack recipe');
  g.interlayer_gap.value=r.gap_um;g.die_thickness.value=r.thickness_um;p.tcncf_process.bond_force.value=r.bond_force_N;
  const model=buildStack({layers:Array.from({length:r.layers},()=>({mode,thickness_um:r.thickness_um})),params:p});
  const thermal=stackSim(model,mode==='TC-NCF'?tcncfSchedule(r.layers,p):mrmufSchedule(r.layers,p));
  const warpHistory=stackWarpHistory(thermalWarpSteps(thermal,model));
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
  return {recipe:r,thermal,warpage:{max_um,judgement:judgeWarpage(max_um,r.gap_um,p),history:warpHistory},ncf,muf,alignment,
    defect_area_pct,defect_judgement:muf?judgeDefect(defect_area_pct,p):`정량 모델 없음 (경향: ${tendencies.join(', ')})`,
    contact_judgement:ncf?(ncf.every(l=>l.contact_time_s!==null&&!l.gel_before_contact)?'접촉':'미접촉/접촉 전 겔화'):'정량 접촉 모델 없음 (자기정렬은 젖음·접촉 가정)',
    cycle:stackCycleTime(mode,r.layers,{params:p}),
    observations:{layers:thermal.layers,vendor_claims:p.vendor_claims,
      void_model:'정량 보이드 모델 없음; MR 결함 면적률은 미충전만 포함',
      alignment_limit:'독립 층간 좌표·일정 강성·작은 변위; 스택 연성 운동·tack 재응고·회전은 미포함'}};
}

export function summarizeStack(result) {
  const {recipe,thermal,warpage,alignment,cycle,defect_area_pct,defect_judgement,contact_judgement,muf,ncf}=result;
  return {recipe,thermal_layers:thermal.layers,warpage:{max_um:warpage.max_um,judgement:warpage.judgement},
    defect_area_pct,defect_judgement,contact_judgement,
    alignment:{layer_errors_um:alignment.layer_errors_um,cumulative_um:alignment.cumulative_um,
      top_to_first_die_um:alignment.top_to_first_die_um,adjacent_3sigma_um:alignment.adjacent_3sigma_um,judgement:alignment.judgement},
    cycle,muf,ncf:ncf?.map(({history,cure_history,...l})=>l)??null};
}
