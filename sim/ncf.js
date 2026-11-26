import {timoshenkoCurvature,warpSagitta} from './warpage.js';
/* 원본 process_physics.py:10-19: epoxy reference constants, not NCF material data. */
const epoxy={mu:20,h0:150e-6,hmin:15e-6};
const radius=a=>a*1e-3/Math.sqrt(Math.PI);
export function squeezeBlt(F,a,t,{mu=epoxy.mu,h0=epoxy.h0,hmin=epoxy.hmin}={}) {
  return Math.max(1/Math.sqrt(1/h0**2+4*F*t/(3*Math.PI*mu*radius(a)**4)),hmin);
}
export function squeezeTimeTo(h,F,a,{mu=epoxy.mu,h0=epoxy.h0}={}) {
  return (1/h**2-1/h0**2)*3*Math.PI*mu*radius(a)**4/(4*F);
}
export const squeezeDhdt=(h,F,a,mu=epoxy.mu)=>-2*F*h**3/(3*Math.PI*mu*radius(a)**4);
/* 원본 process_physics.py:33-37; education_calc.py:8-9. */
export function filletHeight(V,a,blt) {const V_f_mm3=V-a*a*blt*1e-3; return {h_f_mm:Math.sqrt(Math.max(V_f_mm3,0)/(2*a)),V_f_mm3};}
export const filletPct=(V,a,blt,tdie=0.3)=>100*filletHeight(V,a,blt).h_f_mm/tdie;
export const dispenseVolume=(a,blt,frac,tdie)=>a*a*blt*1e-3+2*a*(frac*tdie)**2;
/* 원본 process_physics.py:42-46,85: epoxy reference cure point and gas constant. */
export function cureRate(T,Ea,{Tref_C=180,tref_s=1800,alpha_ref=0.95}={}) {
  return -Math.log(1-alpha_ref)/tref_s*Math.exp(-Ea/8.314*(1/(T+273.15)-1/(Tref_C+273.15)));
}
export const cureTimeTo=(alpha,T,Ea,p)=>-Math.log(1-alpha)/cureRate(T,Ea,p);
export const cureConversion=(t,T,Ea,p)=>1-Math.exp(-cureRate(T,Ea,p)*t);
/* 원본 process_physics.py:64. */
export const tiltBltDiff=(die,parallel=2)=>parallel/10*die;
/* 원본 education_calc.py:35-37: MPa design pressure limits, maximum 50 N. */
export function forceLimit(a,mode) {
  const pressure={epoxy:1,epoxy_thin:0.5,tcb:2}[mode];
  if (pressure===undefined) throw new RangeError(mode);
  return mode==='tcb' && a>=5 ? 50 : Math.round(Math.min(pressure*a*a,50)*10)/10;
}
/* 원본 education_calc.py:20-22: fixed Si/FR4 geometry and properties. */
export function doePredict(T,F,t,V,a=5,tdie=0.3) {
  const BLT=squeezeBlt(F,a,t)*1e6;
  return {BLT,fillet_pct:filletPct(V,a,BLT,tdie),warp_5mm:warpSagitta(timoshenkoCurvature(0.3e-3,130e9,2.6e-6,0.4e-3,22e9,16e-6,T-25),5e-3)*1e6};
}

// C2: material defaults are supplied explicitly by params, never file-loaded.
const ncfParams=p=>p.ncf??p;
export function ncfViscosity(T_C,alpha,params) {
  const p=ncfParams(params),gel=p.gel_conversion.value;
  if(!(T_C> -273.15)||!(alpha>=0&&alpha<=1)) throw new RangeError('NCF temperature/conversion');
  if(alpha>=gel) return Infinity; // gelled film no longer flows
  // R=8.314 J/mol/K, Celsius->Kelvin and kJ->J are physical/unit constants.
  const thermal=p.min_melt_viscosity.value*Math.exp(p.viscosity_activation_energy.value*1000/8.314*
    (1/(T_C+273.15)-1/(p.min_viscosity_temp.value+273.15)));
  return thermal*(gel/(gel-alpha))**(p.castro_A.value+p.castro_B.value*alpha);
}
export function ncfCureRate(T_C,params) {
  const p=ncfParams(params);
  return T_C<p.cure_onset_temp.value?0:cureRate(T_C,p.cure_activation_energy.value*1000,
    {Tref_C:p.gel_reference_temp.value,tref_s:p.gel_time_at_250C.value,alpha_ref:p.gel_conversion.value});
}
// Exact step for the original first-order cure law at constant temperature.
export function cureStep(alpha,T_C,dt_s,params) {
  if(!(dt_s>=0)||!(alpha>=0&&alpha<=1)) throw new RangeError('cure step');
  return 1-(1-alpha)*Math.exp(-ncfCureRate(T_C,params)*dt_s);
}

/** RK4 Stefan integration in y=1/h²: dy/dt=-2 h^-3 squeezeDhdt.
 * This algebraic change removes the h³ stiffness without changing the law.
 * Contact freezes h at h_stop; bump deformation/load sharing is excluded.
 * mu_of_t may return Infinity to indicate gelation (zero flow).
 */
export function squeezeIntegrate({F_of_t,mu_of_t,a_mm,h0_m,h_stop_m,dt_s,t_end_s,gel_time_s=null}) {
  if(![a_mm,h0_m,h_stop_m,dt_s].every(x=>Number.isFinite(x)&&x>0)||h_stop_m>h0_m||!Number.isFinite(t_end_s)||t_end_s<0)
    throw new RangeError('squeeze geometry/time');
  let observedGel=gel_time_s;
  const derivative=t=>{
    const F=F_of_t(t),mu=mu_of_t(t);
    if(!(Number.isFinite(F)&&F>=0)||!(mu>0)) throw new RangeError('squeeze force/viscosity');
    if(mu===Infinity)observedGel=observedGel===null?t:Math.min(observedGel,t);
    return -2*squeezeDhdt(1,F,a_mm,mu);
  };
  const increment=(t,dt)=>dt*(derivative(t)+4*derivative(t+dt/2)+derivative(t+dt))/6; // RK4 for y'=f(t)
  let t=0,y=1/h0_m**2,contact_time_s=h0_m===h_stop_m?0:null;
  const target=1/h_stop_m**2,history=[{t_s:0,h_m:h0_m}];
  while(t<t_end_s) {
    const dt=Math.min(dt_s,t_end_s-t);
    if(contact_time_s===null) {
      if(y+increment(t,dt)>=target) {
        // Root of the RK4 continuous partial step, numerical bisection to machine precision.
        let lo=0,hi=dt;
        for(let j=0;j<52;j++) {const mid=(lo+hi)/2;if(y+increment(t,mid)<target)lo=mid;else hi=mid;}
        contact_time_s=t+(lo+hi)/2;y=target;
        history.push({t_s:contact_time_s,h_m:h_stop_m});
      } else y+=increment(t,dt);
    }
    t+=dt;history.push({t_s:t,h_m:1/Math.sqrt(y)});
  }
  return {history,contact_time_s,remaining_thickness_m:1/Math.sqrt(y),gel_time_s:observedGel,
    gel_before_contact:observedGel!==null&&observedGel<=t_end_s&&(contact_time_s===null||observedGel<contact_time_s)};
}

/** Qualitative rules only: 정량 모델 아님. No defect area percentage is predicted. */
export function ncfVoidTendency({gel_before_contact,contact_time_s,contact_viscosity_Pa_s,low_viscosity_time_s,ramp_rate_K_s},params) {
  const p=params.ncf,reasons=[];
  if(gel_before_contact) reasons.push('접촉 전 겔화: 미접합 위험');
  if(contact_time_s===null) reasons.push('공정 종료까지 범프 미접촉');
  if(low_viscosity_time_s<p.low_viscosity_window.value) reasons.push('접촉 전 저점도 구간이 짧음: 갇힌 기포 위험');
  if(contact_viscosity_Pa_s!==null&&contact_viscosity_Pa_s>p.min_melt_viscosity.value*p.low_viscosity_factor.value)
    reasons.push('접촉 시 높은 점도: 기포 배출 제한');
  return {quantitative:false,grade:gel_before_contact||contact_time_s===null?'미접합 위험':reasons.length?'기포 주의':'낮은 경향',reasons,
    ramp_rate_K_s,literature_ramp_K_s:params.tcncf_process.ramp_rate.literature_value,
    ramp_ratio:ramp_rate_K_s/params.tcncf_process.ramp_rate.literature_value,
    ramp_note:'20 K/s 교육 장비는 80 ℃/s 문헌보다 승온이 느림: 저점도 체류와 경화가 함께 변하므로 속도만으로 결함률을 결정하지 않음'};
}

// Consume C1 history. Its filling layer shares the new die-centre temperature.
// Integrate each film through all later reheats; squeeze force exists only during
// its own ramp/hold (release at cooling). No reflow self-alignment is applied.
export function stackNcf(thermal,params) {
  const p=params.ncf,dt=p.integration_dt.value,N=thermal.layers.length,gelHazard=-Math.log(1-p.gel_conversion.value);
  return Array.from({length:N},(_,i)=>{
    const rows=thermal.history.filter(r=>r.T.length>i),start=rows[0].t_s,end=rows.at(-1).t_s;
    const own=rows.filter(r=>r.T.length===i+1&&!r.phase.includes('cool')),forceEnd=own.at(-1).t_s-start;
    let cursor=0;
    const temperature=t=>{
      const absolute=t+start;
      while(cursor+1<rows.length&&rows[cursor+1].t_s<=absolute)cursor++;
      while(cursor>0&&rows[cursor].t_s>absolute)cursor--;
      const a=rows[cursor],b=rows[Math.min(cursor+1,rows.length-1)];
      return b.t_s===a.t_s?a.T[i]:a.T[i]+(b.T[i]-a.T[i])*(absolute-a.t_s)/(b.t_s-a.t_s);
    };
    const states=[{t:0,H:0}],duration=end-start;let t=0,H=0,gel_time_s=null;
    while(t<duration) {
      const d=Math.min(dt,duration-t),Ta=temperature(t),Tb=temperature(t+d),on=p.cure_onset_temp.value;
      let left=t,right=t+d;
      if(Ta<on&&Tb>=on)left=t+d*(on-Ta)/(Tb-Ta);
      if(Ta>=on&&Tb<on)right=t+d*(on-Ta)/(Tb-Ta);
      // Integrate only the active side of the onset crossing. Clamp endpoint
      // roundoff to onset so inclusive/exclusive sampling cannot add a cure pulse.
      const rate=t=>ncfCureRate(Math.max(on,temperature(t)),params);
      const delta=Math.max(Ta,Tb)<on?0:(right-left)*(rate(left)+4*rate((left+right)/2)+rate(right))/6;
      if(gel_time_s===null&&H+delta>=gelHazard)gel_time_s=left+(right-left)*(gelHazard-H)/delta;
      H+=delta;t+=d;states.push({t,H});
    }
    const hazard=t=>{
      const k=Math.min(Math.floor(t/dt),states.length-2),a=states[Math.max(0,k)],b=states[Math.max(0,k)+1];
      return a.H+(b.H-a.H)*(t-a.t)/(b.t-a.t);
    };
    const mu=t=>ncfViscosity(temperature(t),-Math.expm1(-hazard(t)),params);
    const gap=params.geometry.interlayer_gap.value*1e-6;
    // Issue #20: both gap and film_thickness_over_gap are in μm; h0 = gap + excess.
    const h0=(params.geometry.interlayer_gap.value+p.film_thickness_over_gap.value)*1e-6;
    const flow=squeezeIntegrate({F_of_t:t=>t<=forceEnd?params.tcncf_process.bond_force.value:0,mu_of_t:mu,
      a_mm:params.geometry.die_size.value,h0_m:h0,h_stop_m:gap,dt_s:dt,t_end_s:duration,gel_time_s});
    let low_viscosity_time_s=0;
    const limit=flow.contact_time_s??forceEnd;
    for(let k=1;k<states.length&&states[k-1].t<limit;k++) {
      const a=states[k-1].t,b=Math.min(states[k].t,limit);
      if(mu((a+b)/2)<=p.min_melt_viscosity.value*p.low_viscosity_factor.value)low_viscosity_time_s+=b-a;
    }
    const contact_viscosity_Pa_s=flow.contact_time_s===null?null:mu(flow.contact_time_s);
    const tendency=ncfVoidTendency({...flow,contact_viscosity_Pa_s,low_viscosity_time_s,ramp_rate_K_s:params.tcncf_process.ramp_rate.equipment_value},params);
    return {...flow,layer:i+1,contact_viscosity_Pa_s,low_viscosity_time_s,final_conversion:-Math.expm1(-H),tendency,
      contact_gap_m:gap,bump_height_m:(params.geometry.cu_pillar_height.value+params.geometry.solder_cap_height.value)*1e-6,
      contact_model:'h_stop=interlayer_gap (effective post-bond standoff); pillar+cap is reference geometry',
      cure_history:states.map(s=>({t_s:s.t,alpha:-Math.expm1(-s.H)}))};
  });
}
