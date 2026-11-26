/* 원본 thermal.py:6-13, control_sim.py:46-49. Reference properties/geometry only. */
export function heaterTipCapacity(heaterMm=[20,20,5],colletMm=[10,10,10]) {
  const [hx,hy,hz]=heaterMm.map(v=>v/1000),[cx,cy,cz]=colletMm.map(v=>v/1000);
  return 3260*(hx*hy*hz)*740+7900*(cx*cy*cz)*500;
}
export const thermalPresets=Object.freeze({
  ch7_16node:Object.freeze({n_macor:16,A_rad:0.0017,C_tip:8.7748,Kp:1e6,Ki:0}),
  ch10_3node:Object.freeze({n_macor:3,A_rad:0.0011,C_tip:8.77,Kp:25,Ki:6})
});
export function createHeadModel({preset='ch7_16node',heater=[20,20,5],...overrides}={}) {
  if(!Object.hasOwn(thermalPresets,preset)) throw new RangeError(preset);
  const p={...thermalPresets[preset],...overrides};
  if(preset==='ch7_16node') {
    const [hx,hy,hz]=heater.map(v=>v/1000);
    p.C_tip=overrides.C_tip??heaterTipCapacity(heater);
    p.A_rad=overrides.A_rad??(2*(hx*hy)+2*(hx+hy)*hz+5e-4);
  }
  const n=p.n_macor;
  if(!Number.isInteger(n)||n<1||!(p.C_tip>0)||!(p.A_rad>=0)) throw new RangeError('head parameters');
  // Preserve each original multiplication order (thermal.py:17-20 / control_sim.py:48).
  const Cm=preset==='ch10_3node'?2.52e3*790*0.04*0.04*0.016/n:2520*(0.04*0.04)*(0.016/n)*790;
  return {...p,preset,Cm,Gm:1.46*(0.04*0.04)/(0.016/n),Tamb:20};
}
export function createHeadState(model) {return {T:model.Tamb,Tm:Array(model.n_macor).fill(model.Tamb)};}
/* 원본 thermal.py:32-39; control_sim.py:58-61. Shared explicit Euler plant.
 * All interface fluxes use OLD Tm. Subtract all forward fluxes before adding them. */
export function headStep(st,P,dt,m,air_h=0) {
  const {T,Tm}=st,{Tamb,A_rad:A,Gm,C_tip,Cm}=m,n=Tm.length;
  const qloss=(10+air_h)*A*(T-Tamb)+0.3*5.67e-8*A*((T+273)**4-(Tamb+273)**4);
  const q1=Gm*2*(T-Tm[0]),q=Array(n).fill(0),fl=[];
  st.T+=dt*(P-qloss-q1)/C_tip;q[0]+=q1;
  for(let j=0;j<n-1;j++) fl[j]=Gm*(Tm[j]-Tm[j+1]);
  for(let j=0;j<n-1;j++) q[j]-=fl[j];
  for(let j=0;j<n-1;j++) q[j+1]+=fl[j];
  const Qj=Gm*2*(Tm[n-1]-Tamb);q[n-1]-=Qj;
  for(let j=0;j<n;j++) Tm[j]+=dt*q[j]/Cm;
  return Qj;
}
/* 원본 thermal.py:9-41: ch7's original local PI/on-off thermal experiment.
 * SIL control_sim temperature controller is exclusively firmware wasm (plant.js). */
export function headSim(opts={}) {
  if(opts.preset==='ch10_3node') throw new RangeError('ch10 controller uses tempSim(fw, opts) from plant.js');
  const m=createHeadModel(opts);
  const {P_max=400,T_set=400,t_end=400,dt=0.005,cool_at=null,air_h=0,Kp=m.Kp,Ki=m.Ki,ramp=null}=opts;
  const st=createHeadState(m),r={t:[],T:[],Tm:[],P:[],Qj:[],C_tip:m.C_tip,G_mac:1.46*(0.04*0.04)/0.016};
  let t=0,I=0;const every=Math.trunc(0.1/dt);
  while(t<t_end) {
    let sp=ramp===null?T_set:Math.min(T_set,m.Tamb+ramp*t),P=0;
    const cooling=cool_at!==null&&t>=cool_at;
    if(!cooling) {const e=sp-st.T;I=Math.max(-50,Math.min(50,I+e*dt));P=Math.max(0,Math.min(P_max,Kp*e+Ki*I));}
    const Qj=headStep(st,P,dt,m,cooling?air_h:0);
    if(Math.round(t/dt)%every===0) {r.t.push(t);r.T.push(st.T);r.Tm.push(mean(st.Tm));r.P.push(P);r.Qj.push(Qj);}
    t+=dt;
  }
  return r;
}
export const mean=a=>a.reduce((s,v)=>s+v,0)/a.length;
export function interp(x,xs,ys) {
  if(x<=xs[0]) return ys[0];if(x>=xs.at(-1)) return ys.at(-1);
  let lo=0,hi=xs.length-1;while(hi-lo>1) {const k=(lo+hi)>>1;if(xs[k]>x) hi=k;else lo=k;}
  return ys[lo]+(ys[hi]-ys[lo])/(xs[hi]-xs[lo])*(x-xs[lo]);
}
/* 원본 thermal.py:44-59, np.gradient nonuniform 3-point, endpoints first order. */
export function headHeatupMetrics(r,{thr=399,target=400}={}) {
  const i=Math.max(0,r.T.findIndex(T=>T>=thr)),t=r.t[i];
  return {t_to_400_s:t,avg_ramp_K_per_s:(target-20)/t,P_hold_400_W:mean(r.P.slice(-200)),Q_jacket_steady_W:r.Qj.at(-1)};
}
export function headCoolingTime(r,cool_at,T_end=100) {
  const i=r.t.findIndex((t,i)=>t>=cool_at&&r.T[i]<=T_end);return i<0?null:r.t[i]-cool_at;
}
export function gradientNonUniform(y,x) {
  return y.map((v,i)=>{
    if(i===0) return (y[1]-v)/(x[1]-x[0]);
    if(i===y.length-1) return (v-y[i-1])/(x[i]-x[i-1]);
    const a=x[i]-x[i-1],b=x[i+1]-x[i];
    return -b/(a*(a+b))*y[i-1]+(b-a)/(a*b)*v+a/(b*(a+b))*y[i+1];
  });
}
export function macorDriftMetrics(r,t400,{lim_K_s=0.28,alpha=9.3e-6,L_m=0.020,waits=[0,10,30,60,120]}={}) {
  const g=gradientNonUniform(r.Tm,r.t).map(Math.abs),i=Math.max(0,r.t.findIndex((t,i)=>t>t400&&g[i]<lim_K_s));
  return {limit_K_per_s:lim_K_s,wait_after_setpoint_s:r.t[i]-t400,drift_um_per_s_at:Object.fromEntries(waits.map(w=>[w,interp(t400+w,r.t,g)*alpha*L_m*1e6])),macor_tau_s:2520*0.04*0.04*0.016*790/(2*r.G_mac)};
}
/* 원본 thermal.py:61-70. Water density 1 kg/L. */
export const conductionQ=(k,A,t,dT)=>k*A/t*dT;
export function coolplateRise(Q,{flow_L_min=1,h_W_m2K=3000,A_m2=0.006,cp=4180}={}) {
  const w=Q/(flow_L_min/60*cp),f=Q/(h_W_m2K*A_m2);
  return {water_rise_K:w,film_dT_K:f,plate_rise_open_loop_K:w/2+f};
}
export const thermalOffsetUmPerK=(alpha,L=0.020)=>alpha*L*1e6;
export const driftUmPerS=(rate,alpha=9.3e-6,L=0.020)=>rate*alpha*L*1e6;
