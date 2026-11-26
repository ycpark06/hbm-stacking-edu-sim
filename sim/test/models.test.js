import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {buildStack,stackStep,stackSim,tcncfSchedule,mrmufSchedule} from '../thermal.js';
import {laminateCurvature,timoshenkoCurvature,stackWarpHistory,thermalWarpSteps,judgeWarpage} from '../warpage.js';
import {headDrift} from '../head_drift.js';
const params=JSON.parse(readFileSync(new URL('../params.json',import.meta.url)));
const close=(a,b,rel=1e-9)=>assert.ok(Math.abs(a-b)<=rel*Math.max(Math.abs(b),1e-20),`${a} != ${b}`);
const model=(N,mode='TC-NCF',thickness_um=params.geometry.die_thickness.value,p=params)=>buildStack({params:p,layers:Array.from({length:N},()=>({mode,thickness_um}))});

test('two-layer CLT matches signed Timoshenko; uniform thermal strain has no curvature',()=>{
  const m=params.materials;
  for(const h of [50,100,725]) for(const dT of [-250,150]) {
    const a={t_m:h*1e-6,E_Pa:m.si_E.value*1e9,alpha:m.si_cte.value*1e-6,dT_K:dT};
    const b={t_m:params.geometry.interlayer_gap.value*1e-6,E_Pa:params.ncf.modulus_25C.value*1e9,alpha:params.ncf.cte1.value*1e-6,dT_K:dT};
    const result=laminateCurvature([a,b]);
    close(result.kappa,timoshenkoCurvature(a.t_m,a.E_Pa,a.alpha,b.t_m,b.E_Pa,b.alpha,dT));
    const biaxial=laminateCurvature([{...a,nu:m.si_nu.value},{...b,nu:m.si_nu.value}]);
    close(biaxial.kappa,result.kappa);
    assert.ok(Math.abs(laminateCurvature([a,{...b,alpha:a.alpha}]).kappa)<1e-10);
  }
});

test('backward Euler conserves energy with power, head boundary and losses; insulated limit',()=>{
  const m=model(4),ambient=params.thermal_stack.ambient_temp.value;
  const initial={T:m.C.map((_,i)=>ambient+i)};
  for(const input of [{P_W:1},{P_W:1,T_chuck_C:ambient,h_conv:10,T_amb_C:ambient},
    {T_head_C:300,T_chuck_C:100,h_conv:100,T_amb_C:ambient}]) {
    let state=initial,stored=0,net=0;
    for(let i=0;i<100;i++) {
      const next=stackStep(state,input,m,0.1);net+=next.input_J-next.loss_J;stored+=next.stored_J;state=next;
      close(next.input_J,next.stored_J+next.loss_J);
    }
    close(stored,net);
    if(input.T_chuck_C==null) close(stored,10);
  }
  const huge=stackStep(initial,{T_head_C:300,T_chuck_C:100},m,1e6);
  assert.ok(huge.T.every(t=>Number.isFinite(t)&&t>=100&&t<=300));
});

test('series resistance analytical steady state, N=1/2/8, power and temperature boundaries',()=>{
  for(const n of [1,2,8]) {
    const m=model(n),hot=300,cold=100,totalR=m.G.reduce((s,g)=>s+1/g,0),q=(hot-cold)/totalR;
    let R=0;
    const expected=m.C.map((_,i)=>{R+=1/m.G[i];return cold+q*R;});
    // Starting at exact steady state tests spatial assembly without time-error contamination.
    const result=stackStep({T:expected},{T_head_C:hot,T_chuck_C:cold},m,10);
    result.T.forEach((t,i)=>close(t,expected[i]));
    let state={T:m.C.map(()=>cold)};
    for(let i=0;i<100;i++) state=stackStep(state,{P_W:q,T_chuck_C:cold},m,10);
    state.T.forEach((t,i)=>close(t,expected[i]));
  }
});

test('thermal construction uses NCF, unfilled bump and molded MUF params',()=>{
  const ncf=model(2),bump=model(2,'MR-MUF');
  const muf=buildStack({params,layers:[{mode:'MR-MUF',molded:true},{mode:'MR-MUF',molded:true}]});
  assert.notEqual(ncf.C[0],bump.C[0]);assert.notEqual(muf.C[0],bump.C[0]);
  assert.ok(ncf.R[0]>muf.R[0]&&muf.R[0]>bump.R[0]);
  // A full gap is below the Si centre; only half the Si is above it.
  close(1/ncf.G[0],ncf.chuck.R+ncf.gapR[0]+ncf.dieR[0]/2);
  close(1/ncf.G.at(-1),ncf.toolContact_R+ncf.dieR.at(-1)/2);
  close(1/ncf.G[1],ncf.dieR[0]/2+ncf.gapR[1]+ncf.dieR[1]/2);
  assert.throws(()=>stackStep({T:[20,20]},{P_W:1,T_head_C:300},ncf,1));
});

function crossings(history,index,tl) {
  const byPhase={};let count=0;
  for(let j=1;j<history.length;j++) {
    const a=history[j-1].T[index],b=history[j].T[index];
    if(a!=null&&b!=null&&a<=tl&&b>tl) {count++;const phase=history[j].phase;byPhase[phase]=(byPhase[phase]??0)+1;}
  }
  return {count,byPhase};
}

test('2/4/8/12 layers: separate scheduled bonding/tack exposures from liquidus crossings',t=>{
  const results=[];
  for(const mode of ['TC-NCF','MR-MUF']) for(const N of [2,4,8,12]) for(const thickness_um of [100,50]) {
    const m=model(N,mode,thickness_um),schedule=(mode==='TC-NCF'?tcncfSchedule:mrmufSchedule)(N,params),r=stackSim(m,schedule);
    assert.ok(r.history.every(row=>row.T.every(Number.isFinite)));
    for(let i=0;i<N;i++) {
      const actual=crossings(r.history,i,params.solder.liquidus_snag.value);
      assert.equal(r.layers[i].remelt_count,actual.count);
      assert.deepEqual(r.layers[i].crossings_by_phase,actual.byPhase);
      assert.ok(r.layers[i].time_above_s>=0&&Number.isFinite(r.layers[i].peak_C));
    }
    // Independently group recorded samples by the upper layer being processed.
    // Include cooling samples: a lower node can reach its peak after tool release.
    for(let i=0;i<N;i++) {
      const expected=[];
      for(let n=i+2;n<=N;n++) expected.push(Math.max(...r.history.filter(row=>row.T.length===n&&
        (mode==='TC-NCF'?row.phase.startsWith('bond-'):row.phase.startsWith('tack'))).map(row=>row.T[i])));
      assert.deepEqual(mode==='TC-NCF'?r.layers[i].reheat_peaks_C:r.layers[i].tack_peaks_C,expected);
    }
    const bottom=r.layers[0],tack_crossings=r.layers.map(l=>l.crossings_by_phase.tack??0);
    if(mode==='TC-NCF') {
      assert.equal(bottom.reheat_count,N-1);
      assert.equal(bottom.reheat_peaks_C.length,N-1);
      assert.ok(bottom.reheat_peaks_C.every((peak,i,peaks)=>peak>params.tcncf_process.stage_temp.value&&(i===0||peak<peaks[i-1])));
      for(let i=0;i<N;i++) assert.equal(r.layers[i].reheat_count,N-i-1);
    } else {
      assert.ok(r.layers.every(l=>l.reflow_count===1&&l.reheat_count===0));
      assert.equal(bottom.tack_exposures,N-1);
      for(let i=0;i<N;i++) assert.equal(r.layers[i].tack_peaks_C.length,N-i-1);
    }
    if(mode==='MR-MUF') assert.equal(Object.entries(bottom.crossings_by_phase).filter(([k])=>k.startsWith('reflow')).reduce((s,[,v])=>s+v,0),1);
    const warp=stackWarpHistory(thermalWarpSteps(r,m));
    assert.ok(warp.every(row=>Number.isFinite(row.w_um)));
    const max_warp_um=Math.max(...warp.map(row=>Math.abs(row.w_um)));
    const warp_by_layer=Array.from({length:N},(_,i)=>({layer_count:i+1,max_um:Math.max(...warp.filter(row=>row.layer_count===i+1).map(row=>Math.abs(row.w_um)))}));
    const entry={mode,N,thickness_um,bottom,layers:r.layers,tack_crossings,max_warp_um,warp_by_layer,judgement:judgeWarpage(max_warp_um,params.geometry.interlayer_gap.value,params)};
    results.push(entry);
    t.diagnostic(`${mode} N=${N} t=${thickness_um}: bottom reheats=${bottom.reheat_count}, remelts=${bottom.remelt_count}, subsequent_remelts=${bottom.subsequent_remelts}, reflows=${bottom.reflow_count}, tack exposures=${bottom.tack_exposures}; tack all-layer crossings=${tack_crossings}`);
  }
  const fine=structuredClone(params);fine.thermal_stack.dt.value/=2;
  const convergence=[];
  for(const mode of ['TC-NCF','MR-MUF']) {
    const m=model(12,mode,50,fine),r=stackSim(m,(mode==='TC-NCF'?tcncfSchedule:mrmufSchedule)(12,fine));
    const coarse=results.find(r=>r.mode===mode&&r.N===12&&r.thickness_um===50);
    convergence.push({mode,coarse_dt_s:params.thermal_stack.dt.value,fine_dt_s:fine.thermal_stack.dt.value,bottom_peak_delta_C:r.layers[0].peak_C-coarse.bottom.peak_C,bottom_TAL_delta_s:r.layers[0].time_above_s-coarse.bottom.time_above_s,max_warp_delta_um:Math.max(...stackWarpHistory(thermalWarpSteps(r,m)).map(r=>Math.abs(r.w_um)))-coarse.max_warp_um});
  }
  const sensitivity=[];
  for(const mode of ['TC-NCF','MR-MUF']) for(const contact of ['tool_contact_R_area','chuck_contact_R_area']) for(const value of params.thermal_stack[contact].range) {
    const p=structuredClone(params);p.thermal_stack[contact].value=value;
    const m=model(12,mode,50,p),r=stackSim(m,(mode==='TC-NCF'?tcncfSchedule:mrmufSchedule)(12,p));
    const max_warp_um=Math.max(...stackWarpHistory(thermalWarpSteps(r,m)).map(row=>Math.abs(row.w_um)));
    sensitivity.push({mode,contact,value,bottom:r.layers[0],max_warp_um,judgement:judgeWarpage(max_warp_um,p.geometry.interlayer_gap.value,p)});
  }
  writeFileSync(new URL('c1_results.json',import.meta.url),JSON.stringify({results,convergence,sensitivity,head:headDrift(params)},null,2)+'\n');
});

test('mode schedules preserve equipment ramp and reflow envelope',()=>{
  const tc=tcncfSchedule(2,params),ramp=tc[0],rate=params.tcncf_process.ramp_rate.equipment_value;
  close((ramp.input(ramp.duration_s).T_head_C-ramp.input(0).T_head_C)/ramp.duration_s,rate);
  close(tc[1].duration_s,params.tcncf_process.hold_time.value);
  const mr=mrmufSchedule(2,params),segments=mr.filter(s=>s.phase.startsWith('reflow'));
  assert.equal(mr.filter(s=>s.phase==='tack').length,2);
  assert.equal(segments.filter(s=>s.endEvent==='reflow').length,1);
  const tl=params.solder.liquidus_snag.value;
  let above=0;
  for(const seg of segments) {
    const a=seg.input(0).T_amb_C,b=seg.input(seg.duration_s).T_amb_C;
    above+=seg.duration_s*(a>tl?(b>tl?1:(a-tl)/(a-b)):(b>tl?(b-tl)/(b-a):0));
  }
  close(above,params.reflow.time_above_liquidus.value);
});

test('crossing definition includes first bond and tack; interpolated liquidus time',()=>{
  const m=model(1),tl=params.solder.liquidus_snag.value;
  const seg=(T,phase)=>({duration_s:1,dt_s:1,phase,input:{T_head_C:T}});
  const r=stackSim(m,[seg(300,'tack'),seg(20,'cool'),seg(300,'reflow')]);
  assert.equal(r.layers[0].remelt_count,2);assert.equal(r.layers[0].subsequent_remelts,1);
  assert.equal(r.layers[0].crossings_by_phase.tack,1);
  let above=0;
  for(let i=1;i<r.history.length;i++) {
    const a=r.history[i-1],b=r.history[i],ta=a.T[0],tb=b.T[0],dt=b.t_s-a.t_s;
    if(ta>tl&&tb>tl) above+=dt;
    else if((ta>tl)!==(tb>tl)) above+=dt*(ta>tl?(ta-tl)/(ta-tb):(tb-tl)/(tb-ta));
  }
  close(r.layers[0].time_above_s,above);
});

test('repeated reflows count post-bond reheating independently of melting',()=>{
  const m=model(1,'MR-MUF'),first=mrmufSchedule(1,params);
  const second=first.filter(s=>s.phase.startsWith('reflow')).map(s=>({...s,
    exposure:{id:'reflow-2',kind:'reflow'},
    input:{T_chuck_C:params.thermal_stack.ambient_temp.value}}));
  const r=stackSim(m,[...first,...second]);
  assert.equal(r.layers[0].reflow_count,2);
  assert.equal(r.layers[0].reheat_count,1);
  assert.equal(r.layers[0].tack_exposures,0);
  assert.ok(r.layers[0].reheat_peaks_C[0]<params.solder.liquidus_snag.value);
});

test('warpage stress-free state, cooling, and strict judgement thresholds',()=>{
  const layers=[{t_m:1e-4,E_Pa:1e11,alpha:3e-6,T_C:200,stress_free_C:200},
    {t_m:2e-5,E_Pa:1e10,alpha:20e-6,T_C:200,stress_free_C:200}];
  const r=stackWarpHistory([{layers,die_size_m:0.005},{layers:layers.map(l=>({...l,T_C:20})),die_size_m:0.005}]);
  assert.equal(r[0].kappa,0);assert.notEqual(r[1].kappa,0);
  const gap=params.geometry.interlayer_gap.value,c=gap*params.judgement.warpage_caution_ratio.value,f=params.judgement.warpage_fail_um.value;
  assert.equal(judgeWarpage(c,gap,params),'양호');assert.equal(judgeWarpage(f,gap,params),'주의');assert.equal(judgeWarpage(-f-1,gap,params),'불량');
});

test('head drift uses CAD z lengths and all 16 MACOR rates, not original force-loop constant',()=>{
  const r=headDrift(params),cad=readFileSync(new URL('../../cad/midterm/spec.py',import.meta.url),'utf8');
  close(r.arrival_s,17.2);close(r.alignment_s-r.arrival_s,params.head_drift.alignment_wait.value);
  assert.equal(r.macor_nodes.length,16);
  for(const part of r.parts) {
    const line=cad.split('\n').find(s=>s.includes('"'+part.name+'"'));
    const dims=line.match(/\(([-\d.,\s]+)\)\)/)[1].split(',').map(Number);
    close(part.length_mm,line.includes('"box"')?dims[5]:dims[3]-dims[2]);
    close(part.drift_um_s,part.cte_ppm_K*part.length_mm/1000*part.rate_K_s);
  }
  const macor=r.parts.find(p=>p.name==='MACOR_Insulator');
  close(macor.rate_K_s,r.macor_nodes.reduce((s,n)=>s+n.rate_K_s,0)/r.macor_nodes.length);
  close(r.total_um_s,r.parts.reduce((s,n)=>s+n.drift_um_s,0));
  const changed=structuredClone(params);changed.head_drift.original_drift.value*=2;
  assert.equal(headDrift(changed).total_um_s,r.total_um_s);
});
