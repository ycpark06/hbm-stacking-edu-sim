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
