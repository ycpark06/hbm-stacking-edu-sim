/* 원본 education_calc.py:25-31: reference underfill assumptions. */
export const washburnFillTime=(mu,L,gap,{gamma=0.03,theta_deg=40}={})=>3*mu*L**2/(gamma*gap*Math.cos(theta_deg*Math.PI/180));
export const washburnFront=(mu,t,gap,{gamma=0.03,theta_deg=40}={})=>Math.sqrt(gamma*gap*Math.cos(theta_deg*Math.PI/180)*t/(3*mu));

/** SI parallel plates: x²=h²(ΔPapp+2γ cosθ/h)t/(6μ).
 * Constant net pressure and Newtonian viscosity; one entire die edge is fed.
 * At inlet=0: 6μL²/(h²·2γcosθ/h) = 3μL²/(γhcosθ), exactly Washburn.
 * No bump-density/permeability correction, filler filtration, or trapped voids.
 */
export function pressureFillTime(mu,L,gap,{gamma,theta_deg,dP_app_Pa}) {
  if(![mu,gap].every(v=>Number.isFinite(v)&&v>0)||!Number.isFinite(L)||L<0||
    ![gamma,theta_deg,dP_app_Pa].every(Number.isFinite)||gamma<0||dP_app_Pa<0)
    throw new RangeError('fill inputs (SI)');
  if(L===0)return 0;
  const pressure=dP_app_Pa+2*gamma*Math.cos(theta_deg*Math.PI/180)/gap;
  return pressure>0?6*mu*L**2/(gap**2*pressure):Infinity;
}
/** Fraction of projected resin-accessible area, excluding trapped gas.
 * Straight front across full width: A_unfilled/A = 1-min(1,sqrt(t_allow/t_fill)).
 * Infinity denotes no advancing front, rather than a numerical failure.
 */
export function unfilledFraction(fill_time_s,mold_fill_time_s) {
  if(!(fill_time_s>=0)||!(Number.isFinite(mold_fill_time_s)&&mold_fill_time_s>=0))throw new RangeError('fill times');
  return fill_time_s===0?0:Math.max(0,1-Math.sqrt(mold_fill_time_s/fill_time_s));
}
/** gaps: SI {gap_m, mu_Pa_s?, L_m?, area_m2?}[]; numeric entries mean gap_m.
 * Independent parallel feeds; completion=max_i, area fraction=area-weighted mean.
 * Default square die, flow length=one die side, constant viscosity_at_fill.
 */
export function stackFillTime(gaps,opts) {
  if(!gaps?.length)throw new RangeError('nonempty gaps');
  const p=opts.params,side=p.geometry.die_size.value*1e-3;
  const pressure={gamma:p.muf.surface_tension.value,theta_deg:p.muf.contact_angle.value,
    dP_app_Pa:p.muf.applied_pressure.value*1e6,...opts};
  const allowed=opts.mold_fill_time_s??p.cycle.mold_fill_time.value;
  const layers=gaps.map((entry,i)=>{
    const g=typeof entry==='number'?{gap_m:entry}:entry;
    const mu=g.mu_Pa_s??p.muf.viscosity_at_fill.value,L=g.L_m??side,area=g.area_m2??side**2;
    if(!(Number.isFinite(area)&&area>0))throw new RangeError('fill area');
    const fill_time_s=pressureFillTime(mu,L,g.gap_m,pressure);
    const capillary_fill_time_s=pressureFillTime(mu,L,g.gap_m,{...pressure,dP_app_Pa:0});
    const filler=checkFiller(g.gap_m,p);
    return {capillary_fill_time_s,capillary_unfilled_fraction:unfilledFraction(capillary_fill_time_s,allowed),
      filler,gel_warning:fill_time_s>p.muf.gel_time.value,
      capillary_gel_warning:capillary_fill_time_s>p.muf.gel_time.value,layer:i+1,gap_m:g.gap_m,mu_Pa_s:mu,L_m:L,area_m2:area,fill_time_s,
      unfilled_fraction:unfilledFraction(fill_time_s,allowed)};
  });
  return {layers,inlet_pressure_Pa:pressure.dP_app_Pa,
    filler_warning:layers.some(l=>l.filler.warning),filler_blocked:layers.some(l=>l.filler.blocked),
    gel_warning:layers.some(l=>l.gel_warning),gel_time_s:p.muf.gel_time.value,
    warnings:[...(layers.some(l=>l.filler.warning)?['필러 막힘 위험']:[]),
      ...(layers.some(l=>l.gel_warning)?['충전 시간 > 겔 시간']:[])],
    capillary_only:{fill_time_s:Math.max(...layers.map(l=>l.capillary_fill_time_s)),
      unfilled_fraction:layers.reduce((s,l)=>s+l.area_m2*l.capillary_unfilled_fraction,0)/layers.reduce((s,l)=>s+l.area_m2,0),
      gel_warning:layers.some(l=>l.capillary_gel_warning)},
    fill_time_s:Math.max(...layers.map(l=>l.fill_time_s)),mold_fill_time_s:allowed,
    unfilled_fraction:layers.reduce((s,l)=>s+l.area_m2*l.unfilled_fraction,0)/layers.reduce((s,l)=>s+l.area_m2,0),
    geometry:'one-edge straight front; no bump permeability correction',quantitative_void_model:false};
}

/** Advisory ratio and strict blocking lower bound both come from research2 params. */
export function checkFiller(gap_m,params) {
  if(!(Number.isFinite(gap_m)&&gap_m>0))throw new RangeError('positive gap');
  const p=params.muf,ratio=gap_m/(p.filler_max_size.value*1e-6);
  return {ratio,warning:ratio<p.gap_to_filler_min_ratio.value,
    blocked:ratio<p.gap_to_filler_min_ratio.range[0]};
}
