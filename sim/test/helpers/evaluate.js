import * as n from '../../ncf.js';import * as w from '../../warpage.js';import * as m from '../../muf.js';
import * as th from '../../thermal.js';import * as p from '../../plant.js';import * as a from '../../alignment.js';
import * as c from '../../cycle.js';import {tcncfProfile} from '../../recipe.js';import {render,measure,subpixelPeak,affineFit} from '../../vision.js';
const cache=new Map();
export async function evaluate(id,q,load) {
  const has=s=>id.startsWith(s);
  if(has('ncf.squeeze_blt')) return {h:n.squeezeBlt(q.F,q.a,q.t,{mu:q.mu,h0:q.h0,hmin:q.h_min})};
  if(has('ncf.squeeze_time')) return {t:n.squeezeTimeTo(q.hT,q.F,q.a,{mu:q.mu,h0:q.h0})};
  if(has('ncf.squeeze_dhdt')) return {dhdt:n.squeezeDhdt(q.h,q.F,q.a,q.mu)};
  if(has('epoxy.fillet')) {const f=n.filletHeight(q.V,q.a,q.BLT);return {h_f:f.h_f_mm,V_f:f.V_f_mm3,fillet_pct:n.filletPct(q.V,q.a,q.BLT,q.t_die)};}
  if(has('epoxy.dispense')) return {V:n.dispenseVolume(q.a,q.BLT,q.fillet_frac,q.t_die)};
  if(has('cure.arrhenius')) {const opts={Tref_C:q.T_ref,tref_s:q.t_ref,alpha_ref:q.alpha_ref};return {k:n.cureRate(q.T,q.Ea,opts),t95:n.cureTimeTo(q.alpha_ref,q.T,q.Ea,opts)};}
  if(has('cure.conversion')) return {alpha:n.cureConversion(q.t,q.T,q.Ea)};
  if(has('warpage.')) {const k=w.timoshenkoCurvature(q.h1,q.E1,q.a1,q.h2,q.E2,q.a2,q.dT);return {kappa:k,warp:w.warpSagitta(k,q.L)};}
  if(has('epoxy.tilt')) return {dBLT:n.tiltBltDiff(q.die,q.parallelism)};
  if(has('epoxy.doe')) return n.doePredict(q.T,q.F,q.t,q.V,q.a,q.t_die);
  if(has('muf.washburn_front')) return {L:m.washburnFront(q.mu,q.t,q.gap,{gamma:q.gamma,theta_deg:q.theta})};
  if(has('muf.washburn.')) return {t_fill:m.washburnFillTime(q.mu,q.L,q.gap,{gamma:q.gamma,theta_deg:q.theta})};
  if(has('recipe.force_limit')) return Object.fromEntries(['epoxy','epoxy_thin','tcb'].map(mode=>[mode,n.forceLimit(q.a,mode)]));
  if(has('thermal.tip_capacity')) return {C_tip:th.heaterTipCapacity(q.heater,q.collet)};
  if(has('thermal.chuck_conduction')) return {Q:th.conductionQ(q.k,q.A,q.t,q.dT)};
  if(has('thermal.coolplate')) return th.coolplateRise(q.Q,{flow_L_min:q.flow,h_W_m2K:q.h,A_m2:q.A,cp:q.cp});
  if(has('thermal.offset')) return {offset:th.thermalOffsetUmPerK(q.alpha,q.L)};
  if(has('thermal.drift_rate')) return {drift:th.driftUmPerS(q.dTdt,q.alpha,q.L)};
  if(has('thermal.head_sim.drift')) {
    const r=cache.get(q.source_run);if(!r) throw new Error('missing source run');
    const md=th.macorDriftMetrics(r,th.headHeatupMetrics(r).t_to_400_s,{lim_K_s:q.lim});
    return {wait_after_setpoint:md.wait_after_setpoint_s,...Object.fromEntries(Object.entries(md.drift_um_per_s_at).map(([k,v])=>[`drift_rate_at_${k}s`,v])),macor_tau:md.macor_tau_s};
  }
  if(has('thermal.head_sim')) {
    const r=th.headSim(q);cache.set(id,r);
    if(has('thermal.head_sim.heatup')) return {...Object.fromEntries([1,5,10,60].map(t=>[`T_at_${t.toFixed(1)}s`,th.interp(t,r.t,r.T)])),...Object.fromEntries([10,60,300].map(t=>[`Tm_at_${t.toFixed(1)}s`,th.interp(t,r.t,r.Tm)])),...th.headHeatupMetrics(r)};
    if(has('thermal.head_sim.cool')) return {t_400_to_100:th.headCoolingTime(r,q.cool_at)};
    return {T_at_5s:th.interp(5,r.t,r.T),T_at_12s:th.interp(12,r.t,r.T),T_final:r.T.at(-1),P_final:r.P.at(-1),Qj_final:r.Qj.at(-1)};
  }
  if(has('control.force_gains')) return p.forceGains(q.k_spring,q.f_c,q.f_i);
  if(has('control.force_sim')||has('control.contact_peak')) {
    const r=p.forceSim(await load(),q);
    return has('control.contact_peak')?{peak_over_sp_0p3s:p.contactPeak(r),t_contact:r.t_contact}:{t_contact:r.t_contact,overshoot:r.overshoot,ss_err:r.ss_err,F_at_t_contact_plus_1s:th.interp(r.t_contact+1,r.t,r.F)};
  }
  if(has('control.temp_sim')) {const r=p.tempSim(await load(),q);return {...p.tempMetrics(r),T_at_50s:th.interp(50,r.t,r.T)};}
  if(has('control.tcncf_profile')) return {sp:tcncfProfile(q.t)};
  if(has('alignment.subpixel')) return {offset_gauss:subpixelPeak(q.a,q.b,q.c),offset_para:subpixelPeak(q.a,q.b,q.c,'para')};
  if(has('alignment.render')) {const im=render(q.dx,q.dy,{...q,blur:0});return {sum:im.flat().reduce((s,v)=>s+v,0),px_64_64:im[64][64],px_67_64:im[67][64],px_64_94:im[64][94],px_61_64:im[61][64]};}
  if(has('alignment.measure')) {const [cx,cy]=measure(render(q.dx,q.dy,{blur:q.blur}),q.method);return {cx,cy,err_x:cx-q.dx,err_y:cy-q.dy};}
  if(has('alignment.affine')) {
    // 원본 vision.py:5,61-74: original calibration experiment and 5x5 grid.
    const px=1.725,angle=q.rot*Math.PI/180,sc=px*(1+q.scale_err),A=[[sc*Math.cos(angle),-sc*Math.sin(angle)+q.shear*px],[sc*Math.sin(angle),sc*Math.cos(angle)]],det=A[0][0]*A[1][1]-A[0][1]*A[1][0];
    const solve=([x,y])=>{x-=q.b[0];y-=q.b[1];return [(A[1][1]*x-A[0][1]*y)/det,(-A[1][0]*x+A[0][0]*y)/det];};
    const S=[];for(let x=-1500;x<=1500;x+=750) for(let y=-1200;y<=1200;y+=600) S.push([x,y]);
    const f=affineFit(S.map(solve),S),p1=solve([1000,0]);
    return {fit_rot:f.rot_deg,fit_scale:f.scale_um_px,A:f.A,b:f.b,nominal_err_at_x1000:Math.hypot(p1[0]*px-(1000-q.b[0]),p1[1]*px+q.b[1])};
  }
  if(has('alignment.angle')) return {sigma:a.angleSigmaDeg(q.per_mark_sigma,q.L,q.n_marks)};
  if(has('alignment.rss')) {const s=a.rssSigma(q.terms);return {rss_sigma:s,rss_3s:3*s};}
  if(has('cycle.ballscrew')) return c.ballscrew(q);
  if(has('control.leaf_flexure')) return c.leafFlexure(q.k,q.Fmax,q.E,q.b,q.L);
  throw new Error(`unimplemented ${id}`);
}
