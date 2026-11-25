#include "hal.h"
#include "fw.h"
/* Build renames the core no-argument tick to fw_core_step_1ms.
 * The JS export below supplies measurements before executing that same core. */
#undef fw_step_1ms
static float force_N, temp_C, velocity_mm_s, heater_W;
static int hardware_fault;
float hal_read_force_N(void) { return force_N; }
float hal_read_temp_C(void) { return temp_C; }
void hal_write_z_velocity_mm_s(float v) { velocity_mm_s = v; }
void hal_write_heater_W(float p) { heater_W = p; }
int hal_hw_fault(void) { return hardware_fault; }
void hal_write_safety(int brake, int sto) { (void)brake; (void)sto; }
void fw_step_1ms(float force_meas_N, float temp_meas_C)
{
    force_N = force_meas_N;
    temp_C = temp_meas_C;
    fw_core_step_1ms();
}
int fw_wasm_set_recipe(float spring, float target, float ramp, float approach,
                       unsigned period_ms, int mode)
{
    fw_recipe_t r = {spring, target, ramp, approach, period_ms, (fw_mode_t)mode};
    return fw_set_recipe(&r);
}
void fw_set_hw_fault(int fault) { hardware_fault = fault; }
float fw_get_z_velocity(void) { return velocity_mm_s; }
float fw_get_heater_power(void) { return heater_W; }
/* Mode is the REFERENCE/FIRMWARE selection, phase is the sequencer state. */
int fw_get_phase(void) { return (int)fw_get_sequence_state()->phase; }
int fw_get_warning(void) { return fw_get_interlock_state()->warning; }
int fw_get_latched(void) { return fw_get_interlock_state()->latched; }
int fw_get_brake(void) { return fw_get_interlock_state()->brake; }
int fw_get_sto(void) { return fw_get_interlock_state()->sto; }
float fw_get_force_setpoint(void) { return fw_get_force_state()->setpoint_N; }
float fw_get_force_integral(void) { return fw_get_force_state()->integral_N_s; }
float fw_get_temp_integral(void) { return fw_get_temp_state()->integral_C_s; }
