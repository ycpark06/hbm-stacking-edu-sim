#include "hal.h"
#include "hal_host.h"
static float measured_force;
static float commanded_velocity;
static float measured_temp, commanded_heater, commanded_reflow_heater;
static int hardware_fault, brake_flag, sto_flag;
void hal_host_reset(void)
{
    hardware_fault = brake_flag = sto_flag = 0;
    measured_force = 0.0f;
    commanded_velocity = 0.0f;
    measured_temp = 0.0f;
    commanded_heater = commanded_reflow_heater = 0.0f;
}
float hal_read_force_N(void) { return measured_force; }
void hal_write_z_velocity_mm_s(float velocity) { commanded_velocity = velocity; }
void hal_host_set_force_N(float force) { measured_force = force; }
float hal_host_get_z_velocity_mm_s(void) { return commanded_velocity; }
float hal_read_temp_C(void) { return measured_temp; }
void hal_write_heater_W(float power) { commanded_heater = power; }
void hal_host_set_temp_C(float temp) { measured_temp = temp; }
float hal_host_get_heater_W(void) { return commanded_heater; }
void hal_write_reflow_heater_W(float power) { commanded_reflow_heater = power; }
float hal_host_get_reflow_heater_W(void) { return commanded_reflow_heater; }
int hal_hw_fault(void) { return hardware_fault; }
void hal_host_set_hw_fault(int fault) { hardware_fault = fault; }
void hal_write_safety(int brake, int sto) { brake_flag = brake; sto_flag = sto; }
int hal_host_get_brake(void) { return brake_flag; }
int hal_host_get_sto(void) { return sto_flag; }
