import {createHeadModel,createHeadState,headStep} from './thermal.js';

// Positive rate means growth along the head's serial z path (tool moves downward
// if the upper mount is fixed). CAD envelope lengths are proxies, not measured
// effective expansion lengths. Above-jacket temperatures are fixed by assumption.
export function headDrift(params) {
  const p=params.head_drift,dt=p.dt.value,m=createHeadModel({preset:'ch7_16node'}),st=createHeadState(m);
  const every=Math.round(p.sample_period.value/dt),samples=[];
  let arrival=null,I=0,step=0;
  while(true) {
    const t=step*dt,e=p.target_temp.value-st.T;
    // Original ch7 integral clamp ±50, thermal.py:29 (Ki=0 in this preset).
    I=Math.max(-50,Math.min(50,I+e*dt));
    const power=Math.max(0,Math.min(p.power.value,m.Kp*e+m.Ki*I));
    headStep(st,power,dt,m);
    if(step%every===0) {
      if(arrival===null&&st.T>=p.arrival_threshold.value) arrival=t;
      samples.push({t,tip:st.T,macor:st.Tm.slice(),cold:m.Tamb});
      if(arrival!==null&&t>=arrival+p.alignment_wait.value+p.fit_window.value/2) break;
    }
    step++;
    if(t>params.reflow.total_time_25_to_peak_max.value) throw new RangeError('head did not reach alignment');
  }
  const alignment=arrival+p.alignment_wait.value;
  const window=samples.filter(s=>Math.abs(s.t-alignment)<=p.fit_window.value/2+Number.EPSILON*alignment);
  const avg=a=>a.reduce((s,v)=>s+v,0)/a.length;
  const mt=avg(window.map(s=>s.t)),den=window.reduce((s,v)=>s+(v.t-mt)**2,0);
  const fit=fn=>{const values=window.map(fn),mean=avg(values);return {T_C:mean,rate_K_s:window.reduce((s,v,i)=>s+(v.t-mt)*(values[i]-mean),0)/den};};
  const tip=fit(s=>s.tip),macor_nodes=st.Tm.map((_,j)=>fit(s=>s.macor[j])),macor=fit(s=>avg(s.macor));
  const cold=fit(s=>s.cold);
  const specs=[['Collet_Tool','steel',tip],['AlN_Heater','aln',tip],['MACOR_Insulator','macor',macor],
    ['Cooling_Jacket','al',cold],['Gimbal_Lockable','steel',cold],['Load_Cell_100N','steel',cold],
    ['Flexure_Leaf_Spring','steel',cold],['Theta_Stage','steel',cold],['Z_Carriage','al',cold]];
  const parts=specs.map(([name,material,temp])=>{
    const length_mm=p[name+'_length'].value,cte_ppm_K=p[material+'_cte'].value;
    return {name,length_mm,length_kind:'assumption (CAD z envelope)',cte_ppm_K,...temp,
      drift_um_s:cte_ppm_K*length_mm/1000*temp.rate_K_s};
  });
  const total_um_s=parts.reduce((s,r)=>s+r.drift_um_s,0);
  return {arrival_s:arrival,alignment_s:alignment,fit_window_s:p.fit_window.value,macor_nodes,parts,total_um_s,
    original_um_s:p.original_drift.value,ratio_to_original:total_um_s/p.original_drift.value};
}
