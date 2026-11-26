/* 원본 drive_calc.py:3-25: gravity, steel density/modulus, root diameter and supports. */
export function ballscrew({m,lead,d,L,eta,a,v,mu,Fext=0,vertical=false,Jm=0,Ca=null,support=3.927,eta2=10}) {
  const g=9.81,rho=7850,E=206e3;
  const Jscrew=Math.PI*rho*(L/1000)*(d/1000)**4/32;
  const alpha=2*Math.PI*a/(lead/1000), Ffr=vertical?0:mu*m*g,Fg=vertical?m*g:0;
  const F=m*a+Ffr+Fg+Fext,T_load=F*lead/1000/(2*Math.PI*eta),T_acc=(Jscrew+Jm)*alpha;
  const F_hold=Ffr+Fg+Fext,dr=d*0.83;
  return {F_peak:F,T_peak:T_load+T_acc,T_hold:F_hold*lead/1000/(2*Math.PI*eta),rpm_max:v/lead*60,
    n_crit:support**2*60/(2*Math.PI*(L/1000)**2)*Math.sqrt(E*1e6*Math.PI*(dr/1000)**4/64/(rho*Math.PI*(dr/1000)**2/4)),P_buckle:eta2*dr**4/L**2*1e4};
}
/* 원본 drive_calc.py:45-50. */
export function leafFlexure(k,F,E=200e3,b=20,L=25) {
  const t=(k*L**3/(4*E*b))**(1/3),defl=F/k;return {t,defl,stress:3*E*t*defl/L**2};
}

export function trapezoidMoveTime(d_mm,v_mm_s,a_mm_s2) {
  if(!(Number.isFinite(d_mm)&&d_mm>=0)||![v_mm_s,a_mm_s2].every(x=>Number.isFinite(x)&&x>0))
    throw new RangeError('move distance/speed/acceleration');
  return d_mm>=v_mm_s**2/a_mm_s2?d_mm/v_mm_s+v_mm_s/a_mm_s2:2*Math.sqrt(d_mm/a_mm_s2);
}
const sumTimes=o=>Object.values(o).reduce((s,x)=>s+x,0);
/** recipe={params, xy_distance_mm?, z_distance_mm?, mold_fill_s?}.
 * machine overrides cycle parameters by their existing key, in stated units.
 * Layer steps occupy the bonder; MR once steps are shared batch post-processing.
 * No batch size or startup preheat is assumed.
 */
export function bondStepTimes(mode,recipe,machine={}) {
  if(!['TC-NCF','MR-MUF'].includes(mode))throw new RangeError('bond mode');
  const p=recipe.params,c=p.cycle,get=k=>machine[k]??c[k].value;
  const per_layer={pickup_s:get('pickup_time'),
    xy_move_s:trapezoidMoveTime(recipe.xy_distance_mm??get('xy_distance'),get('xy_speed'),get('xy_acceleration')),
    z_move_s:trapezoidMoveTime(recipe.z_distance_mm??get('z_distance'),get('z_speed'),get('z_acceleration')),
    alignment_s:get('alignment_frame_time')*get('alignment_iterations')};
  const once={};
  if(mode==='TC-NCF') {
    const q=p.tcncf_process;
    Object.assign(per_layer,{approach_s:q.approach_time.value,ramp_s:(q.head_setpoint.value-q.stage_temp.value)/q.ramp_rate.equipment_value,
      hold_s:q.hold_time.value,cooling_s:q.cool_time.value});
  } else {
    per_layer.approach_s=get('mrmuf_approach_time');per_layer.tack_s=p.mrmuf_process.tack_time.value;
    // Full C1 oven program, not the independent 360 s literature comparator.
    const r=p.reflow,s=p.thermal_stack,ambient=s.ambient_temp.value;
    once.reflow_s=(r.preheat_start.value-ambient)/r.ramp_up.value+r.soak_time.value+
      (r.peak_temp.value-r.preheat_end.value)/r.ramp_up.value+r.time_above_liquidus.value-r.time_near_peak.value-
      (r.peak_temp.value-p.solder.liquidus_snag.value)*(1/r.ramp_up.value+1/r.ramp_down.value)+
      r.time_near_peak.value+(r.peak_temp.value-ambient)/r.ramp_down.value;
    once.mold_dispense_s=get('mold_dispense_time');once.mold_fill_s=recipe.mold_fill_s??get('mold_fill_time');once.mold_cure_s=p.muf.cure_time.value;
  }
  if(![...Object.values(per_layer),...Object.values(once)].every(x=>Number.isFinite(x)&&x>=0))throw new RangeError('nonnegative finite cycle times required');
  return {per_layer,once,per_layer_s:sumTimes(per_layer),once_s:sumTimes(once)};
}
export function stackCycleTime(mode,N,recipe,machine={}) {
  if(!Number.isInteger(N)||N<1)throw new RangeError('cycle layer count');
  const steps=bondStepTimes(mode,recipe,machine),p=recipe.params;
  // Issue #20: batch oven/molding duration is separate from bonder occupancy.
  const bonder_s=N*steps.per_layer_s,batch_post_s=steps.once_s;
  return {bonder_s,batch_post_s,total_serial_s:bonder_s+batch_post_s,
    breakdown:{per_layer:steps.per_layer,layer_totals:Object.fromEntries(Object.entries(steps.per_layer).map(([k,v])=>[k,N*v])),
      once:steps.once,per_layer_s:steps.per_layer_s,all_layers_s:bonder_s,once_s:batch_post_s,
      literature_comparison:{tcb_thermal_cycle_min_s:p.cycle.tcb_cycle_min.value,tcb_uph_current:p.cycle.tcb_uph_current.value,
        tcb_bond_time_per_layer_s:p.tcncf_process.bond_time_per_layer.value,mrmuf_tack_cycle_per_die_s:p.cycle.mrmuf_tack_cycle_per_die.value,
        mass_reflow_total_s:p.cycle.mass_reflow_total.value,
        note:'비교만: 본더 점유 스택/h=3600/bonder_s, 직렬 환산=3600/total_serial_s. 배치 크기 가정 없이 라인 UPH는 산출하지 않음'}}};
}
