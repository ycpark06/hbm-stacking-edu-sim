#include "fw.h"
#include "fw_config.h"
#include "hal.h"
static fw_recipe_t recipe;
static force_ctrl_t force;
static uint32_t tick_ms, force_tick_ms;
static interlock_t safety;
static sequencer_t sequence;
static unsigned temp_period_ms;
static temp_ctrl_t temp;
static int head_heater_enabled;
static float reflow_request_W, head_output_W, reflow_output_W;
static void heaters_off(void)
{
    head_output_W = reflow_output_W = 0.0f;
    hal_write_heater_W(0.0f);
    hal_write_reflow_heater_W(0.0f);
}
void fw_set_head_heater_enabled(int enabled) { head_heater_enabled = enabled != 0; }
void fw_request_reflow_heater_W(float power_W)
{
    reflow_request_W = !(power_W > 0.0f) ? 0.0f :
        (power_W > FW_REFLOW_HEATER_MAX_W ? FW_REFLOW_HEATER_MAX_W : power_W);
}
float fw_get_reflow_heater_power(void) { return reflow_output_W; }
int fw_get_dual_heater_blocked(void) { return safety.dual_heater_blocked; }
fw_recipe_t fw_recipe_low_range_default(void)
{
    /* control_sim.py:6,38 저레인지 2 N/mm, 1 N, 접근 0.02 mm/s, 1 ms.
     * 램프 1 N/s: 설계값, #13 / 사용자 결정 2026-11-25. */
    const fw_recipe_t r = {2.0f, 1.0f, FW_FORCE_LOW_RANGE_RAMP_N_S, 0.02f,
                          FW_FORCE_PERIOD_MS, FW_MODE_FIRMWARE};
    return r;
}
fw_recipe_t fw_recipe_high_range_default(void)
{
    /* control_sim.py:6,38 고레인지 원본 시험 조건: 50 N/mm, 20 N,
     * 5 N/s, 접근 0.02 mm/s, 1 ms. FIRMWARE 기본 선택은 HANDOFF 3.1. */
    const fw_recipe_t r = {50.0f, 20.0f, 5.0f, 0.02f,
                          FW_FORCE_PERIOD_MS, FW_MODE_FIRMWARE};
    return r;
}
void fw_init(void)
{
    const fw_recipe_t defaults = fw_recipe_high_range_default();
    /* fw_init 및 레시피 변경도 기존 래치를 해제하지 않는다. */
    (void)fw_set_recipe(&defaults);
}
int fw_set_recipe(const fw_recipe_t *r)
{
    if (!r || !(r->k_spring_N_mm > 0.0f) || !(r->target_N > 0.0f) ||
        !(r->ramp_N_s > 0.0f) || !(r->approach_mm_s > 0.0f) ||
        r->force_period_ms == 0u || (r->mode != FW_MODE_REFERENCE && r->mode != FW_MODE_FIRMWARE)) return FW_ERR_INVALID_RECIPE;
    if (r->mode == FW_MODE_FIRMWARE &&
        r->ramp_N_s > FW_FORCE_RAMP_MAX_N_S(r->k_spring_N_mm))
        return FW_ERR_RAMP_EXCEEDS_CAPABILITY;
    recipe = *r;
    tick_ms = force_tick_ms = 0u;
    sequencer_init(&sequence);
    force_ctrl_init(&force, &recipe);
    temp_period_ms = FW_TEMP_PERIOD_MS;
    temp_ctrl_init(&temp);
    interlock_update(&safety, hal_read_force_N(), hal_read_temp_C(), hal_hw_fault());
    hal_write_safety(safety.brake, safety.sto);
    head_heater_enabled = 1;
    reflow_request_W = 0.0f;
    safety.dual_heater_blocked = 0;
    heaters_off();
    hal_write_z_velocity_mm_s(safety.warning || safety.latched ? 0.0f : force.velocity_mm_s);
    return FW_OK;
}
int fw_set_temp_period_ms(unsigned period_ms)
{
    if (period_ms == 0u) return 0;
    temp_period_ms = period_ms;
    return 1;
}
void fw_step_1ms(void)
{
    interlock_update(&safety, hal_read_force_N(), hal_read_temp_C(), hal_hw_fault());
    hal_write_safety(safety.brake, safety.sto);
    /* 경고/래치는 매 1 ms 검사; 분주 사이에도 정지한다.
     * 정지 중 PI/시퀀서 시간도 동결해 해제 후 sp가 뛰지 않게 한다. */
    if (!safety.warning && !safety.latched) {
        if (force_tick_ms % recipe.force_period_ms == 0u)
            sequencer_step(&sequence, &force, &recipe, hal_read_force_N(), force_tick_ms);
        ++force_tick_ms;
    } else force.velocity_mm_s = 0.0f;
    hal_write_z_velocity_mm_s(force.velocity_mm_s);
    /* control_sim.py:52-53: 첫 온도 제어도 t=0, 이후 설정 Ts마다. */
    if (!safety.latched && head_heater_enabled && tick_ms % temp_period_ms == 0u) {
        temp_ctrl_step(&temp, hal_read_temp_C(),
                       temp_profile_C((float)tick_ms * FW_TICK_S),
                       (float)temp_period_ms * FW_TICK_S);
    }
    {
        float head = head_heater_enabled ? temp.power_W : 0.0f;
        float reflow = reflow_request_W;
        interlock_heaters(&safety, &head, &reflow, head_output_W, reflow_output_W);
        /* Always turn the inactive channel off before energizing the owner. */
        if (head > 0.0f) {
            hal_write_reflow_heater_W(0.0f);
            hal_write_heater_W(head);
        } else {
            hal_write_heater_W(0.0f);
            hal_write_reflow_heater_W(reflow);
        }
        head_output_W = head;
        reflow_output_W = reflow;
    }
    if (safety.latched) temp.power_W = temp.duty = 0.0f;
    ++tick_ms;
}
const force_ctrl_t *fw_get_force_state(void) { return &force; }
const temp_ctrl_t *fw_get_temp_state(void) { return &temp; }
void fw_reset_latch(void)
{
    interlock_reset(&safety, hal_read_force_N(), hal_read_temp_C(), hal_hw_fault());
    hal_write_safety(safety.brake, safety.sto);
    if (safety.latched || safety.warning) {
        force.velocity_mm_s = 0.0f;
        hal_write_z_velocity_mm_s(0.0f);
    }
    if (safety.latched) {
        temp.power_W = temp.duty = 0.0f;
        safety.dual_heater_blocked = 0;
        heaters_off();
    }
}
void fw_release(void) { sequencer_release(&sequence); }
const interlock_t *fw_get_interlock_state(void) { return &safety; }
const sequencer_t *fw_get_sequence_state(void) { return &sequence; }

fw_mode_t fw_get_mode(void) { return recipe.mode; }
