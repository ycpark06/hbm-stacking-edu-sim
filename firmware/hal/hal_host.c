#include "hal.h"
static float measured_force;
static float commanded_velocity;
void hal_host_reset(void) { measured_force = 0.0f; commanded_velocity = 0.0f; }
float hal_read_force_N(void) { return measured_force; }
void hal_write_z_velocity_mm_s(float velocity) { commanded_velocity = velocity; }
void hal_host_set_force_N(float force) { measured_force = force; }
float hal_host_get_z_velocity_mm_s(void) { return commanded_velocity; }
