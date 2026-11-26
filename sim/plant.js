import createController from '../firmware/build/controller.js';
import {createHeadModel,createHeadState,headStep,mean} from './thermal.js';
import {tcncfProfile} from './recipe.js';
export const FW_MODE_REFERENCE=0;
/* 원본 control_sim.py:8-10,40; gain calculation only, NOT a JS controller. */
export const kEff=(spring,contact=2000)=>1/(1/spring+1/contact);
export function forceGains(spring,fc=20,fi=2) {const ke=kEff(spring);return {k_eff:ke,Kp:2*Math.PI*fc/ke,Ki:(2*Math.PI*fc)*(2*Math.PI*fi)/ke};}
// Browser uses the same relative ESM import and Emscripten's default wasm URL.
// Node tests inject wasmBinary, keeping fs and Node-specific loading outside sim modules.
export async function loadController(options={}) {const fw=await createController(options);fw._fw_init();return fw;}
function configure(fw,k,target,ramp,approach,Ts) {
  const period=Math.round(Ts*1000);
  if(period<1||Math.abs(period/1000-Ts)>Number.EPSILON) throw new RangeError('firmware period: integer milliseconds');
  if(fw._fw_wasm_set_recipe(k,target,ramp,approach,period,FW_MODE_REFERENCE)!==1) throw new Error('firmware recipe rejected');
}
/* 원본 control_sim.py:6-35: mm/N/s, dt=10 us, servo tau=0.8 ms,
 * initial gap 0.02 mm, contact stiffness 2000 N/mm, ADC 50-entry FIFO.
 * Each integration step appends before removing; head expansion therm*t is original G6. */
export function forceSim(fw,{k_spring=50,F_target=20,Ts=0.001,ramp=5,t_end=9,dt=1e-5,delay=0.5e-3,tau_servo=0.8e-3,approach=0.02,therm=0,noise=0,rng=null,Kp,Ki}={}) {
  const gains=forceGains(k_spring);
  if((Kp!==undefined&&Math.abs(Kp-gains.Kp)>1e-12)||(Ki!==undefined&&Math.abs(Ki-gains.Ki)>1e-12)) throw new RangeError('REFERENCE wasm has fixed original force gains');
  configure(fw,k_spring,F_target,ramp,approach,Ts);
  const ke=kEff(k_spring),buf=Array(Math.max(1,Math.round(delay/dt))).fill(0),tick=Math.round(0.001/dt);
  if(tick<1||Math.abs(tick*dt-0.001)>1e-12) throw new RangeError('dt must divide firmware tick');
  let zcmd=-0.02,z=-0.02,t=0,v=approach,t_contact=null,sp=0;
  const r={t:[],F:[],sp:[]};
  for(let i=0;i<Math.trunc(t_end/dt);i++) {
    const F=Math.max(0,ke*(z+therm*t));buf.push(F);const Fd=buf.shift();
    if(i%tick===0) {
      fw._fw_step_1ms(Fd+(rng&&i%Math.round(Ts/dt)===0?rng.normal(0,noise):0),20);
      v=fw._fw_get_z_velocity();sp=fw._fw_get_force_setpoint();
      if(t_contact===null&&sp>0) t_contact=t;
    }
    zcmd+=v*dt;z+=(zcmd-z)*dt/tau_servo;
    if(i%100===0) {r.t.push(t);r.F.push(F);r.sp.push(sp);}
    t+=dt;
  }
  const hold=r.F.filter((_,i)=>r.t[i]>t_contact+F_target/ramp+0.5);
  return {...r,t_contact,overshoot:Math.max(...r.F)-F_target,ss_err:hold.length?Math.max(...hold.map(f=>Math.abs(f-F_target))):null};
}
/* 원본 contact_speed_study.py:7-8: strict window bounds and 1 ms recording. */
export function contactPeak(r,window_s=0.3) {
  let peak=-Infinity;
  for(let i=0;i<r.t.length;i++) if(r.t[i]>r.t_contact&&r.t[i]<r.t_contact+window_s) peak=Math.max(peak,r.F[i]-r.sp[i]);
  return peak;
}
/* 원본 control_sim.py:45-64: 3-node plant, thermocouple lag, 50 ms recording. */
export function tempSim(fw,{Ts=0.01,t_end=120,dt=0.001,tc_tau=0.005,noise=0,rng=null,...thermal}={}) {
  if(dt!==0.001) throw new RangeError('temperature SIL uses 1 ms firmware tick');
  // 원본 control_sim.py:45,54-56: firmware's compiled PI constants.
  if((thermal.Kp!==undefined&&thermal.Kp!==25)||(thermal.Ki!==undefined&&thermal.Ki!==6)||(thermal.Kd!==undefined&&thermal.Kd!==0)||(thermal.P_max!==undefined&&thermal.P_max!==400)) throw new RangeError('REFERENCE wasm has fixed original temperature gains/power');
  if(!Number.isInteger(Ts*1000)||Ts<=0) throw new RangeError('temperature period: integer milliseconds');
  configure(fw,50,20,5,0.02,0.001);
  if(fw._fw_set_temp_period_ms(Math.round(Ts*1000))!==1) throw new RangeError('temperature period');
  const m=createHeadModel({preset:'ch10_3node',...thermal}),st=createHeadState(m),r={t:[],T:[],sp:[],P:[]};
  let Ttc=m.Tamb;
  for(let i=0;i<Math.trunc(t_end/dt);i++) {
    const t=i*dt;fw._fw_step_1ms(0,Ttc+(rng&&i%Math.round(Ts/dt)===0?rng.normal(0,noise):0));
    const P=fw._fw_get_heater_power();headStep(st,P,dt,m);Ttc+=dt*(st.T-Ttc)/tc_tau;
    if(i%50===0) {r.t.push(t);r.T.push(st.T);r.sp.push(tcncfProfile(t));r.P.push(P);}
  }
  return r;
}
/* 원본 control_sim.py:69-72: same strict masks and least-squares slope. */
export function tempMetrics({t,T,P}) {
  const select=(a,lo,hi)=>a.filter((_,i)=>t[i]>lo&&t[i]<hi),x=select(t,41,47),y=select(T,41,47),xm=mean(x),ym=mean(y);
  return {overshoot:Math.max(...T.filter((_,i)=>t[i]>45))-300,stab_150:Math.max(...select(T,25,40).map(v=>Math.abs(v-150))),stab_300:Math.max(...select(T,65,120).map(v=>Math.abs(v-300))),ramp:x.reduce((s,v,i)=>s+(v-xm)*(y[i]-ym),0)/x.reduce((s,v)=>s+(v-xm)**2,0),P_hold:mean(select(P,65,120))};
}
