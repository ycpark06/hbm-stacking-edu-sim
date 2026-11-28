import {loadController} from '../../sim/plant.js';
export async function createAlarmDemo(params,options={}) {
  const fw=await loadController(options),e=params.equipment_limits;
  let force=0,temp=params.tcncf_process.stage_temp.value;
  const step=()=>fw._fw_step_1ms(force,temp);
  const state=()=>({warning:fw._fw_get_warning(),latched:fw._fw_get_latched(),
    dual_heater_blocked:fw._fw_get_dual_heater_blocked(),head_W:fw._fw_get_heater_power(),
    reflow_W:fw._fw_get_reflow_heater_power(),force_N:force,temp_C:temp});
  return {act(action){
    if(action==='force-warning')force=e.force_warning_N.value;
    if(action==='force-latch')force=e.force_latch_N.value;
    if(action==='temp-warning')temp=e.temp_warning_C.value;
    if(action==='temp-latch')temp=e.temp_latch_C.value;
    if(action==='hardware')fw._fw_set_hw_fault(1);
    if(action==='clear'){force=0;temp=params.tcncf_process.stage_temp.value;fw._fw_set_hw_fault(0);fw._fw_request_reflow_heater_W(0);}
    if(action==='reset')fw._fw_reset_latch();
    if(action==='heaters'){
      fw._fw_set_head_heater_enabled(1);fw._fw_request_reflow_heater_W(0);
      // Advance to a temperature PI tick (firmware README §7).
      for(let i=0;i<e.temp_period_ms.value/e.force_period_ms.value;i++)step();
      fw._fw_request_reflow_heater_W(e.reflow_heater_max_W.value);
    }
    step();return state();
  },state};
}
