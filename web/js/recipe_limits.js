// Browser-independent validation. Limits and their provenance live in params.
export function validateRecipe(r,p) {
  const errors=[],e=p.equipment_limits;
  const check=(key,min,max,label)=>{
    const v=r[key];if(!Number.isFinite(v)||v<min||v>max)errors.push(`${label}: ${min} ~ ${max} 범위만 허용`);
  };
  if(!['TC-NCF','MR-MUF'].includes(r.mode))errors.push('공정 모드를 선택하세요');
  if(![2,4,8,12].includes(r.layers))errors.push('층 수: 2/4/8/12 선택만 허용'); // HANDOFF §D options
  if(![100,50].includes(r.thickness_um))errors.push('두께: 100/50 μm 선택만 허용');
  check('gap_um',...p.geometry.interlayer_gap.range,'간격 (μm)');
  check('bond_force_N',p.tcncf_process.bond_force.range[0],e.bond_force_max_N.value,'하중 (N), 원문 KPI');
  check('head_temp_C',p.tcncf_process.head_setpoint.range[0],e.head_max_temp_C.value,'헤드 온도 (℃), 원문 KPI');
  check('ramp_K_s',Number.MIN_VALUE,p.tcncf_process.ramp_rate.equipment_value,'승온 (K/s), 장비 설정');
  check('force_ramp_N_s',Number.MIN_VALUE,r.low_range?e.low_range_ramp_N_s.value:e.force_high_ramp_N_s.value,'하중 램프 (N/s), 레인지 설계 한계');
  if(r.inlet_pressure_MPa!==0)check('inlet_pressure_MPa',...p.muf.applied_pressure.range,'입구 압력 (MPa), 가정 범위 (0은 모세관 비교)');
  if(typeof r.head_temp_compensation!=='boolean')errors.push('헤드 보정 옵션은 참/거짓이어야 합니다');
  return errors;
}
export function recipeParams(r,p) {
  const errors=validateRecipe(r,p);if(errors.length)throw new RangeError(errors.join('\n'));
  const copy=structuredClone(p);
  copy.tcncf_process.head_setpoint.value=r.head_temp_C;
  copy.tcncf_process.ramp_rate.equipment_value=r.ramp_K_s;
  return copy;
}
