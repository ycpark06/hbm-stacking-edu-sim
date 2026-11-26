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

// C2: numerical consistency, statistical validation, and recorded scenarios.
import {ncfViscosity,ncfCureRate,cureStep,squeezeIntegrate,squeezeTimeTo,squeezeBlt,stackNcf,ncfVoidTendency} from '../ncf.js';
import {stackOffset,stackOffsetExpected,stackOffsetMonteCarlo} from '../alignment.js';
import {makeRng} from '../rng.js';
import {trapezoidMoveTime,bondStepTimes,stackCycleTime} from '../cycle.js';

test('Issue #20: NCF initial film is gap plus excess in μm (default 19 μm)',()=>{
  assert.equal(params.geometry.interlayer_gap.unit,'um');
  assert.equal(params.ncf.film_thickness_over_gap.unit,'um');
  const thermal=stackSim(model(1),tcncfSchedule(1,params));
  const [layer]=stackNcf(thermal,params);
  close(layer.history[0].h_m*1e6,19);
  close((layer.history[0].h_m-layer.contact_gap_m)*1e6,4);
  close(layer.contact_gap_m,layer.bump_height_m);
});

test('NCF viscosity matches Arrhenius at zero cure, diverges monotonically; onset and gel reference',()=>{
  const p=params.ncf,g=p.gel_conversion.value;
  for(const T of [100,138,200,250]) {
    const expected=p.min_melt_viscosity.value*Math.exp(p.viscosity_activation_energy.value*1000/8.314*(1/(T+273.15)-1/(p.min_viscosity_temp.value+273.15)));
    close(ncfViscosity(T,0,params),expected);
    let previous=0;
    for(const a of [0,g/2,g*0.9,g*0.99,g*0.999]) {const v=ncfViscosity(T,a,params);assert.ok(v>previous);previous=v;}
    assert.equal(ncfViscosity(T,g,params),Infinity);
  }
  assert.equal(ncfCureRate(p.cure_onset_temp.value-1,params),0);
  close(cureStep(0,p.gel_reference_temp.value,p.gel_time_at_250C.value,params),g);
});

test('RK4 Stefan: analytic thickness/contact, doubled force halves time, time-varying fourth-order convergence',()=>{
  const base={a_mm:5,h0_m:60e-6,h_stop_m:15e-6,dt_s:0.1,t_end_s:100,mu_of_t:()=>1727,F_of_t:()=>40};
  const analytic=squeezeTimeTo(base.h_stop_m,40,5,{mu:1727,h0:base.h0_m});
  const a=squeezeIntegrate(base),b=squeezeIntegrate({...base,F_of_t:()=>80});
  close(a.contact_time_s,analytic,1e-10);close(b.contact_time_s,a.contact_time_s/2,1e-6);
  for(const row of a.history)close(row.h_m,squeezeBlt(40,5,row.t_s,{mu:1727,h0:base.h0_m,hmin:base.h_stop_m}),1e-10);
  // Smooth varying fluidity with exact integral, contact outside this interval.
  const varying={...base,h_stop_m:1e-6,t_end_s:1,mu_of_t:t=>1727*Math.exp(t)};
  const target=1/Math.sqrt(1/base.h0_m**2+(1/base.h_stop_m**2-1/base.h0_m**2)/analytic*(1-Math.exp(-1)));
  const coarse=squeezeIntegrate({...varying,dt_s:0.2}),fine=squeezeIntegrate({...varying,dt_s:0.1});
  const ec=Math.abs(coarse.remaining_thickness_m-target),ef=Math.abs(fine.remaining_thickness_m-target);
  assert.ok(ec/ef>15&&ec/ef<17);
  const gel=squeezeIntegrate({...base,F_of_t:()=>40,mu_of_t:()=>Infinity});
  assert.equal(gel.contact_time_s,null);assert.equal(gel.gel_before_contact,true);close(gel.remaining_thickness_m,base.h0_m);
  assert.throws(()=>squeezeIntegrate({...base,dt_s:0}));
});

test('seeded stack offsets: MC agrees within five sampling standard errors; reference covariance',()=>{
  const M=params.alignment.mc_samples.value,s=params.alignment.sigma_layer_um.value;
  for(const reference of ['previous','substrate'])for(const N of [2,4,8,12]) {
    const opts={N,reference,params,rng:makeRng(params.alignment.mc_seed.value)},r=stackOffsetMonteCarlo(opts);
    const expected=stackOffsetExpected(opts).cumulative_sigma_um;
    close(expected,s*(reference==='previous'?Math.sqrt(N):1));
    for(let j=0;j<2;j++) {
      assert.ok(Math.abs(r.mc_sigma_um[j]/expected-1)<5/Math.sqrt(2*(M-1)));
      assert.ok(Math.abs(r.mc_mean_um[j])<5*expected/Math.sqrt(M));
    }
    const one=stackOffset({...opts,rng:makeRng(123)}),two=stackOffset({...opts,rng:makeRng(123)});
    assert.deepEqual(one,two);assert.equal(one.self_alignment,false);
    for(let i=0;i<N;i++)for(let j=0;j<2;j++)close(one.positions_um[i][j]-(i?one.positions_um[i-1][j]:0),one.layer_errors_um[i][j]);
  }
});

test('cycle continuity; both bonder times scale with N, batch post is independent; C1 oven duration',()=>{
  const v=params.cycle.xy_speed.value,a=params.cycle.xy_acceleration.value,d=v*v/a;
  close(trapezoidMoveTime(d,v,a),2*v/a);
  close(trapezoidMoveTime(d*(1-1e-10),v,a),trapezoidMoveTime(d*(1+1e-10),v,a),1e-9);
  assert.equal(trapezoidMoveTime(0,v,a),0);assert.throws(()=>trapezoidMoveTime(-1,v,a));
  for(const mode of ['TC-NCF','MR-MUF']) {
    const recipe={params},step=bondStepTimes(mode,recipe),r2=stackCycleTime(mode,2,recipe),r4=stackCycleTime(mode,4,recipe);
    assert.deepEqual(Object.keys(r4),['bonder_s','batch_post_s','total_serial_s','breakdown']);
    close(r4.bonder_s,2*r2.bonder_s);
    close(r4.bonder_s,4*step.per_layer_s);
    assert.equal(r4.batch_post_s,r2.batch_post_s);
    close(r4.total_serial_s,r4.bonder_s+r4.batch_post_s);
    close(r4.total_serial_s-r2.total_serial_s,2*step.per_layer_s);
    close(r4.total_serial_s,4*step.per_layer_s+step.once_s);
    if(mode==='TC-NCF'){assert.equal(r4.batch_post_s,0);assert.equal(step.once_s,0);close(r4.total_serial_s,2*r2.total_serial_s);close(step.per_layer.ramp_s,10);}
    else {
      close(step.once.reflow_s,mrmufSchedule(2,params).filter(s=>s.phase.startsWith('reflow')).reduce((v,s)=>v+s.duration_s,0));
      close(stackCycleTime(mode,4,{params,mold_fill_s:123}).total_serial_s-r4.total_serial_s,123-params.cycle.mold_fill_time.value);
      const changed=stackCycleTime(mode,4,{params,mold_fill_s:123});
      assert.equal(changed.bonder_s,r4.bonder_s);
      assert.equal(r4.batch_post_s,step.once_s);
      assert.equal(step.once.mold_cure_s,params.muf.cure_time.value);
    }
    close(Object.values(r4.breakdown.layer_totals).reduce((s,v)=>s+v,0)+Object.values(r4.breakdown.once).reduce((s,v)=>s+v,0),r4.total_serial_s);
  }
});

test('C2 recorded 2/4/8/12 x 100/50 scenarios, gel/void rules, parameter sensitivity and coupled dt convergence',()=>{
  const results=[],alignment=[];
  for(const N of [2,4,8,12]) {
    for(const reference of ['previous','substrate'])alignment.push(stackOffsetMonteCarlo({N,reference,params,rng:makeRng(params.alignment.mc_seed.value)}));
    for(const thickness_um of [100,50]) {
      const thermal=stackSim(model(N,'TC-NCF',thickness_um),tcncfSchedule(N,params)),layers=stackNcf(thermal,params);
      for(const l of layers) {
        assert.ok(l.history.every(r=>Number.isFinite(r.h_m)&&r.h_m>=l.contact_gap_m*(1-1e-12)));
        assert.equal(l.tendency.quantitative,false);
        assert.ok(l.cure_history.every((r,i,arr)=>r.alpha>=0&&r.alpha<=1&&(i===0||r.alpha>=arr[i-1].alpha)));
      }
      results.push({N,thickness_um,layers:layers.map(({history,cure_history,...l})=>l),
        cycles:Object.fromEntries(['TC-NCF','MR-MUF'].map(mode=>[mode,stackCycleTime(mode,N,{params})]))});
    }
  }
  const sensitivity=[];
  for(const key of ['gel_time_at_250C','cure_activation_energy','castro_A'])for(const value of params.ncf[key].range) {
    const p=structuredClone(params);p.ncf[key].value=value;
    const thermal=stackSim(model(12,'TC-NCF',50,p),tcncfSchedule(12,p));
    sensitivity.push({key,value,layers:stackNcf(thermal,p).map(({history,cure_history,...l})=>l)});
  }
  const thermal=stackSim(model(12,'TC-NCF',50),tcncfSchedule(12,params)),coarse=stackNcf(thermal,params);
  const fineParams=structuredClone(params);fineParams.ncf.integration_dt.value/=2;
  const fine=stackNcf(thermal,fineParams);
  const convergence=fine.map((l,i)=>({layer:i+1,contact_delta_s:l.contact_time_s===null||coarse[i].contact_time_s===null?null:l.contact_time_s-coarse[i].contact_time_s,
    thickness_delta_um:(l.remaining_thickness_m-coarse[i].remaining_thickness_m)*1e6,conversion_delta:l.final_conversion-coarse[i].final_conversion}));
  for(const r of convergence){if(r.contact_delta_s!==null)assert.ok(Math.abs(r.contact_delta_s)<0.01);assert.ok(Math.abs(r.thickness_delta_um)<0.01);}
  const voidRule=ncfVoidTendency({gel_before_contact:true,contact_time_s:null,contact_viscosity_Pa_s:null,low_viscosity_time_s:0,ramp_rate_K_s:20},params);
  assert.equal(voidRule.quantitative,false);assert.equal(voidRule.grade,'미접합 위험');
  writeFileSync(new URL('c2_results.json',import.meta.url),JSON.stringify({correction_reason:'Issue #20: h0 = gap + film excess (um); separate bonder occupancy and batch post-processing.',results,alignment,sensitivity,convergence},null,2)+'\n');
});
