// Plant and fault injection copied from firmware/test/test_force.c simulate_options,
// Validation 3 high20N-block3.7+0.5s. Both modes use the same valid recipe.
import fs from 'node:fs';
import createController from '../../../../firmware/build/controller.js';
const output = new URL('./ch17_force_data.json', import.meta.url);
const wasmBinary = fs.readFileSync(new URL('../../../../firmware/build/controller.wasm', import.meta.url));
const data = {source:'firmware/test/test_force.c: simulate_options / Validation 3',
  recipe:{spring_N_mm:50,target_N:20,ramp_N_s:5,approach_mm_s:0.02,period_ms:1},
  plant:{dt_s:1e-5,tau_s:0.8e-3,contact_stiffness_N_mm:2000,adc_delay_s:0.0005,
    velocity_limit_mm_s:0.5,block_start_after_contact_s:3.7,block_duration_s:0.5}, runs:[]};
for (const mode of [0,1]) {
 const m=await createController({wasmBinary}); m._fw_init();
 if(m._fw_wasm_set_recipe(50,20,5,0.02,1,mode)!==1) throw Error('Recipe rejected');
 let z=-0.02,zc=z,t=0,contact=-1,peak=-Infinity;
 const dt=1e-5,tau=0.8e-3,ke=1/(1/50+1/2000),delay=Array(50).fill(0), rows=[];
 let slot=0;
 for(let i=0;i<Math.trunc(12/dt);i++){
  const f=Math.max(0,ke*z), delayed=delay[slot];delay[slot]=f;slot=(slot+1)%50;
  if(i%100===0){
   m._fw_step_1ms(delayed,150);
   if(contact<0 && m._fw_get_phase()!==0) contact=t;
  }
  const v=Math.max(-0.5,Math.min(0.5,m._fw_get_z_velocity()));zc+=v*dt;
  let dz=Math.max(-0.5*dt,Math.min(0.5*dt,(zc-z)*dt/tau));
  if(contact>=0 && t>=contact+3.7 && t<contact+4.2){dz=0;zc=z;}
  z+=dz;
  if(i%100===0){peak=Math.max(peak,f); rows.push([t,f,m._fw_get_force_setpoint()]);}
  t+=dt;
 }
 data.runs.push({mode:mode?'FIRMWARE':'REFERENCE',contact_s:contact,overshoot_N:peak-20,rows});
}
fs.writeFileSync(output,JSON.stringify(data,null,2)+'\n');
console.log(data.runs.map(({mode,contact_s,overshoot_N})=>({mode,contact_s,overshoot_N})));
