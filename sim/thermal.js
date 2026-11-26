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

/* G1–G3: browser-safe, explicit params argument (no filesystem or hidden defaults).
 * One finite volume per die + underlying gap, ordered bottom→top. C adds both
 * volumes; series slab R is split equally at each equivalent volume centre.
 * Chuck is a prescribed-temperature reservoir, not a substrate mechanical layer.
 */
export function buildStack({layers, toolContact_R, chuck={}, params}) {
  if(!params || !layers?.length) throw new RangeError('nonempty layers and params required');
  const p=params, g=p.geometry, m=p.materials, a=g.die_size.value/1000, area=a*a;
  const gap=g.interlayer_gap.value*1e-6;
  const fraction=Math.PI/4*(g.bump_diameter.value/g.bump_pitch.value)**2;
  const cu=g.cu_pillar_height.value/(g.cu_pillar_height.value+g.solder_cap_height.value);
  const bumpCv=fraction*(cu*m.cu_rho.value*m.cu_cp.value+(1-cu)*m.snag_rho.value*m.snag_cp.value);
  const R=[],C=[],sideArea=[];
  for(const layer of layers) {
    const t=(layer.thickness_um??g.die_thickness.value)*1e-6;
    if(!(t>0)) throw new RangeError('positive die thickness');
    const fill=layer.mode==='TC-NCF'?p.ncf:layer.molded?p.muf:null;
    const k=fill?.thermal_conductivity.value??m.bump_layer_k_eff.value;
    const cv=fill?fill.density.value*fill.specific_heat.value:bumpCv;
    R.push(t/(m.si_k.value*area)+gap/(k*area));
    C.push(area*(t*m.si_rho.value*m.si_cp.value+gap*cv));
    sideArea.push(4*a*(t+gap));
  }
  const rt=toolContact_R??p.thermal_stack.tool_contact_R_area.value/area;
  const rc=chuck.R??p.thermal_stack.chuck_contact_R_area.value/area;
  if([rt,rc].some(r=>r<0)||C.some(c=>!(c>0))) throw new RangeError('thermal parameters');
  // G[0]=chuck, G[N]=tool. Infinity resistance gives an insulated boundary.
  const G=[1/(rc+R[0]/2)];
  for(let i=1;i<C.length;i++) G.push(1/((R[i-1]+R[i])/2));
  G.push(1/(rt+R.at(-1)/2));
  return {C,G,R,area,sideArea,layers,params:p,toolContact_R:rt,chuck:{...chuck,R:rc}};
}

/* Backward Euler solves the passive tridiagonal M-matrix; no stability dt limit.
 * Input P_W is deposited in top volume. T_head_C instead connects through G[N].
 * loss_J and input_J use END-step fluxes, exactly as the BE storage balance. */
export function stackStep(state,input,model,dt) {
  const n=model.C.length,T=state.T;
  if(!(dt>0)||T.length!==n||T.some(t=>!Number.isFinite(t))) throw new RangeError('state/dt');
  if(input.P_W!=null&&input.T_head_C!=null) throw new RangeError('choose power OR head boundary');
  const h=input.h_conv??0, ambient=input.T_amb_C??model.params.thermal_stack.ambient_temp.value;
  if(h<0) throw new RangeError('nonnegative convection');
  const gc=input.T_chuck_C==null?0:model.G[0],gh=input.T_head_C==null?0:model.G[n];
  const H=model.sideArea.map((a,i)=>h*(a+(i===n-1?model.area:0)));
  const lower=Array(n).fill(0),diag=[],upper=Array(n).fill(0),b=[];
  for(let i=0;i<n;i++) {
    const left=i>0?model.G[i]:gc,right=i<n-1?model.G[i+1]:gh;
    lower[i]=i>0?-left:0; upper[i]=i<n-1?-right:0;
    diag[i]=model.C[i]/dt+left+right+H[i];
    b[i]=model.C[i]/dt*T[i]+H[i]*ambient;
  }
  b[0]+=gc*(input.T_chuck_C??0);
  b[n-1]+=gh*(input.T_head_C??0)+(input.P_W??0);
  for(let i=1;i<n;i++) {const f=lower[i]/diag[i-1];diag[i]-=f*upper[i-1];b[i]-=f*b[i-1];}
  const next=Array(n);next[n-1]=b[n-1]/diag[n-1];
  for(let i=n-2;i>=0;i--) next[i]=(b[i]-upper[i]*next[i+1])/diag[i];
  const input_J=dt*((input.P_W??0)+gh*((input.T_head_C??0)-next[n-1]));
  const loss_J=dt*(gc*(next[0]-(input.T_chuck_C??0))+H.reduce((s,v,i)=>s+v*(next[i]-ambient),0));
  return {T:next,input_J,loss_J,stored_J:model.C.reduce((s,c,i)=>s+c*(next[i]-T[i]),0)};
}

/* Reheat count = EVERY below→above liquidus crossing, including first bonding.
 * subsequent_reheats excludes the first crossing. Linear crossing interpolation
 * gives time above liquidus; no latent heat or cure heat is included in C1. */
export function stackSim(model,schedule) {
  const p=model.params,tl=p.solder.liquidus_snag.value,N=model.C.length;
  const stats=Array.from({length:N},()=>({peak_C:-Infinity,time_above_s:0,reheat_count:0,subsequent_reheats:0,crossings_by_phase:{}}));
  let T=[],t=0;const history=[];
  for(const segment of schedule) {
    const n=segment.activeLayers??N;
    if(!Number.isInteger(n)||n<T.length||n>N||!(segment.duration_s>0)) throw new RangeError('schedule');
    const initial=p.thermal_stack.ambient_temp.value;
    while(T.length<n) T.push(initial);
    const active=buildStack({...model,layers:model.layers.slice(0,n)});
    for(let i=0;i<n;i++) stats[i].peak_C=Math.max(stats[i].peak_C,T[i]);
    history.push({t_s:t,T:[...T],phase:segment.phase,event:segment.startEvent??null});
    let elapsed=0;
    while(elapsed<segment.duration_s) {
      const dt=Math.min(segment.dt_s??p.thermal_stack.dt.value,segment.duration_s-elapsed);
      const input=typeof segment.input==='function'?segment.input(elapsed+dt):segment.input;
      const next=stackStep({T},input,active,dt).T;
      for(let i=0;i<n;i++) {
        const s=stats[i],a=T[i],b=next[i];s.peak_C=Math.max(s.peak_C,b);
        if(a<=tl&&b>tl) {s.reheat_count++;s.crossings_by_phase[segment.phase]=(s.crossings_by_phase[segment.phase]??0)+1;}
        const fraction=a>tl?(b>tl?1:(a-tl)/(a-b)):(b>tl?(b-tl)/(b-a):0);
        s.time_above_s+=dt*fraction;
      }
      elapsed+=dt;t+=dt;T=next;
      history.push({t_s:t,T:[...T],phase:segment.phase,event:elapsed>=segment.duration_s?(segment.endEvent??null):null});
    }
  }
  for(const s of stats) {s.subsequent_reheats=Math.max(0,s.reheat_count-1);if(s.peak_C===-Infinity) s.peak_C=null;}
  return {history,layers:stats};
}

export function tcncfSchedule(N,p) {
  const q=p.tcncf_process,s=p.thermal_stack,stage=q.stage_temp.value,head=q.head_setpoint.value;
  const ramp=(head-stage)/q.ramp_rate.equipment_value;
  if(!(ramp>0)) throw new RangeError('head above stage');
  const schedule=[];
  for(let n=1;n<=N;n++) {
    const base={activeLayers:n};
    const input=T=>({T_head_C:T,T_chuck_C:stage,h_conv:s.h_conv.value,T_amb_C:s.ambient_temp.value});
    schedule.push({...base,phase:'bond-ramp',duration_s:ramp,input:t=>input(stage+q.ramp_rate.equipment_value*t)});
    schedule.push({...base,phase:'bond-hold',duration_s:q.hold_time.value,input:input(head),endEvent:'bond'});
    schedule.push({...base,phase:'bond-cool',duration_s:q.cool_time.value,input:t=>input(head+(stage-head)*t/q.cool_time.value)});
  }
  return schedule;
}
export function mrmufSchedule(N,p) {
  const q=p.mrmuf_process,s=p.thermal_stack,r=p.reflow,ambient=s.ambient_temp.value;
  const schedule=[];
  for(let n=1;n<=N;n++) {
    schedule.push({activeLayers:n,phase:'tack',duration_s:q.tack_time.value,input:{T_head_C:q.tack_temp.value,T_chuck_C:ambient,h_conv:s.h_conv.value,T_amb_C:ambient},endEvent:'tack'});
    const rest=p.cycle.mrmuf_tack_cycle_per_die.value-q.tack_time.value;
    if(!(rest>0)) throw new RangeError('tack cycle must include cooling/handling');
    schedule.push({activeLayers:n,phase:'tack-cool',duration_s:rest,input:{T_chuck_C:ambient,h_conv:s.h_conv.value,T_amb_C:ambient}});
  }
  // Piecewise oven/chuck program: a shoulder dwell implements requested TL
  // duration without extending the near-peak hold. Actual die TL time is measured.
  const oven=T=>({T_chuck_C:T,T_amb_C:T,h_conv:s.h_oven.value});
  const add=(phase,from,to,time,event)=>schedule.push({activeLayers:N,phase,duration_s:time,input:t=>oven(from+(to-from)*t/time),endEvent:event});
  add('reflow-preheat',ambient,r.preheat_start.value,(r.preheat_start.value-ambient)/r.ramp_up.value);
  add('reflow-soak',r.preheat_start.value,r.preheat_end.value,r.soak_time.value);
  const shoulder=s.reflow_shoulder_temp.value;
  const dwell=r.time_above_liquidus.value-r.time_near_peak.value-
    (r.peak_temp.value-p.solder.liquidus_snag.value)*(1/r.ramp_up.value+1/r.ramp_down.value);
  if(!(shoulder>p.solder.liquidus_snag.value&&shoulder<r.peak_temp.value&&dwell>=0)) throw new RangeError('reflow envelope');
  add('reflow-ramp',r.preheat_end.value,shoulder,(shoulder-r.preheat_end.value)/r.ramp_up.value);
  if(dwell>0) add('reflow-shoulder',shoulder,shoulder,dwell);
  add('reflow-ramp',shoulder,r.peak_temp.value,(r.peak_temp.value-shoulder)/r.ramp_up.value);
  add('reflow-peak',r.peak_temp.value,r.peak_temp.value,r.time_near_peak.value,'reflow');
  add('reflow-cool',r.peak_temp.value,ambient,(r.peak_temp.value-ambient)/r.ramp_down.value);
  // Mold heat/cure is a separate mechanical stage in C1; thermal schedule can
  // also be built with molded:true to use MUF conductivity/capacity.
  return schedule;
}
