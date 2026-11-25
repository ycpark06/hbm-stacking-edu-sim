#include "fw.h"
#include "fw_config.h"
#include "hal.h"
static fw_recipe_t recipe;
static force_ctrl_t force;
static uint32_t tick_ms;
static unsigned temp_period_ms;
static temp_ctrl_t temp;
void fw_init(void)
{
    /* 기본 시나리오: control_sim.py:38 고레인지 20 N, ramp/approach:6. */
    const fw_recipe_t defaults = {50.0f, 20.0f, 5.0f, 0.02f,
                                  FW_FORCE_PERIOD_MS, FW_MODE_FIRMWARE};
    (void)fw_set_recipe(&defaults);
}
int fw_set_recipe(const fw_recipe_t *r)
{
    if (!r || !(r->k_spring_N_mm > 0.0f) || !(r->target_N > 0.0f) ||
        !(r->ramp_N_s > 0.0f) || !(r->approach_mm_s > 0.0f) ||
        r->force_period_ms == 0u || (r->mode != FW_MODE_REFERENCE && r->mode != FW_MODE_FIRMWARE)) return 0;
    recipe = *r;
    tick_ms = 0u;
    force_ctrl_init(&force, &recipe);
    temp_period_ms = FW_TEMP_PERIOD_MS;
    temp_ctrl_init(&temp);
    hal_write_heater_W(temp.power_W);
    hal_write_z_velocity_mm_s(force.velocity_mm_s);
    return 1;
}
int fw_set_temp_period_ms(unsigned period_ms)
{
    if (period_ms == 0u) return 0;
    temp_period_ms = period_ms;
    return 1;
}
void fw_step_1ms(void)
{
    /* control_sim.py:21: 첫 제어는 t=0, 이후 Ts마다. */
    if (tick_ms % recipe.force_period_ms == 0u) {
        force_ctrl_step(&force, &recipe, hal_read_force_N(), tick_ms);
        hal_write_z_velocity_mm_s(force.velocity_mm_s);
    }
    /* control_sim.py:52-53: 첫 온도 제어도 t=0, 이후 설정 Ts마다. */
    if (tick_ms % temp_period_ms == 0u) {
        temp_ctrl_step(&temp, hal_read_temp_C(),
                       temp_profile_C((float)tick_ms * FW_TICK_S),
                       (float)temp_period_ms * FW_TICK_S);
        hal_write_heater_W(temp.power_W);
    }
    ++tick_ms;
}
const force_ctrl_t *fw_get_force_state(void) { return &force; }
const temp_ctrl_t *fw_get_temp_state(void) { return &temp; }
