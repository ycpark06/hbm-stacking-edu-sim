#include "fw.h"
#include "fw_config.h"
#include "hal.h"
static fw_recipe_t recipe;
static force_ctrl_t force;
static uint32_t tick_ms;
void fw_init(void)
{
    /* 기본 시나리오: control_sim.py:38 고레인지 20 N, ramp/approach:6. */
    const fw_recipe_t defaults = {50.0f, 20.0f, 5.0f, 0.02f,
                                  FW_FORCE_PERIOD_MS, FW_MODE_REFERENCE};
    (void)fw_set_recipe(&defaults);
}
int fw_set_recipe(const fw_recipe_t *r)
{
    if (!r || !(r->k_spring_N_mm > 0.0f) || !(r->target_N > 0.0f) ||
        !(r->ramp_N_s > 0.0f) || !(r->approach_mm_s > 0.0f) ||
        r->force_period_ms == 0u || r->mode != FW_MODE_REFERENCE) return 0;
    recipe = *r;
    tick_ms = 0u;
    force_ctrl_init(&force, &recipe);
    hal_write_z_velocity_mm_s(force.velocity_mm_s);
    return 1;
}
void fw_step_1ms(void)
{
    /* control_sim.py:21: 첫 제어는 t=0, 이후 Ts마다. */
    if (tick_ms % recipe.force_period_ms == 0u) {
        force_ctrl_step(&force, &recipe, hal_read_force_N(), tick_ms);
        hal_write_z_velocity_mm_s(force.velocity_mm_s);
    }
    ++tick_ms;
}
const force_ctrl_t *fw_get_force_state(void) { return &force; }
