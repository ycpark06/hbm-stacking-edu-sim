import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {validateRecipe,recipeParams} from '../../web/js/recipe_limits.js';
import {VISION_DEFAULTS,visionOptions} from '../vision.js';
import {createAlarmDemo} from '../../web/js/alarms.js';
const p=JSON.parse(readFileSync(new URL('../params.json',import.meta.url)));
const recipe={mode:'TC-NCF',layers:12,thickness_um:100,gap_um:p.geometry.interlayer_gap.value,
  bond_force_N:p.tcncf_process.bond_force.value,head_temp_C:p.tcncf_process.head_setpoint.value,
  ramp_K_s:p.tcncf_process.ramp_rate.equipment_value,force_ramp_N_s:p.equipment_limits.force_high_ramp_N_s.value,
  inlet_pressure_MPa:p.muf.applied_pressure.value,head_temp_compensation:false,low_range:false};
test('HMI accepts device boundaries and capillary comparison, blocks each out-of-range setting',()=>{
  assert.deepEqual(validateRecipe(recipe,p),[]);
  for(const changes of [{bond_force_N:p.equipment_limits.bond_force_max_N.value,head_temp_C:p.equipment_limits.head_max_temp_C.value},
    {inlet_pressure_MPa:0},{gap_um:7},{gap_um:30},{gap_um:20},{low_range:true,force_ramp_N_s:p.equipment_limits.low_range_ramp_N_s.value}])assert.deepEqual(validateRecipe({...recipe,...changes},p),[]);
  for(const changes of [{bond_force_N:51},{head_temp_C:401},{head_temp_C:p.tcncf_process.stage_temp.value},{ramp_K_s:21},{low_range:true,force_ramp_N_s:2},{gap_um:6},{gap_um:31},{inlet_pressure_MPa:-1},{inlet_pressure_MPa:4},{inlet_pressure_MPa:.05},{layers:3},{thickness_um:75},{mode:'bad'},{head_temp_compensation:'true'},{gap_um:NaN},{ramp_K_s:0}])assert.ok(validateRecipe({...recipe,...changes},p).length,JSON.stringify(changes));
  const shifted=structuredClone(p);shifted.equipment_limits.bond_force_max_N.value=39;
  assert.ok(validateRecipe(recipe,shifted).length,'uses supplied params rather than literal 50');
});
test('HMI adapter applies accepted temperature/ramp without mutating shared params',()=>{
  const before=structuredClone(p),r={...recipe,head_temp_C:310,ramp_K_s:10};const adapted=recipeParams(r,p);
  assert.equal(adapted.tcncf_process.head_setpoint.value,310);assert.equal(adapted.tcncf_process.ramp_rate.equipment_value,10);assert.deepEqual(p,before);
  assert.throws(()=>recipeParams({...recipe,head_temp_C:500},p),RangeError);
});
test('24 vision params retain exact defaults/provenance; supplied params take precedence',()=>{
  assert.equal(Object.keys(VISION_DEFAULTS).length,24);
  for(const [key,entry]of Object.entries(VISION_DEFAULTS))assert.deepEqual(p.alignment[key],entry,key);
  assert.equal(Object.values(VISION_DEFAULTS).filter(v=>v.kind==='midterm').length,21);
  assert.equal(visionOptions({alignment:{pixel_um:{value:2}}}).pixel_um,2);
  assert.equal(visionOptions(p,{pixel_um:3}).pixel_um,3);
});
test('HMI uses real wasm warning, latch persistence, manual reset and mutual heater exclusion',async()=>{
  const wasmBinary=readFileSync(new URL('../../firmware/build/controller.wasm',import.meta.url));
  const d=await createAlarmDemo(p,{wasmBinary});
  assert.equal(d.act('force-warning').warning,1);assert.equal(d.state().latched,0);
  assert.equal(d.act('force-latch').latched,1);assert.equal(d.act('reset').latched,1);
  assert.equal(d.act('clear').latched,1);assert.equal(d.act('reset').latched,0);
  assert.equal(d.act('temp-warning').warning,1);assert.equal(d.act('temp-latch').latched,1);
  d.act('clear');d.act('reset');assert.equal(d.act('hardware').latched,1);
  d.act('clear');d.act('reset');const s=d.act('heaters');assert.ok(s.head_W>0);assert.equal(s.reflow_W,0);assert.equal(s.dual_heater_blocked,1);
});
