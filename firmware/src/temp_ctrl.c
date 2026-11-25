#include "temp_ctrl.h"
#include "fw_config.h"
static float clip(float x, float lo, float hi)
{
    return x < lo ? lo : (x > hi ? hi : x);
}
void temp_ctrl_init(temp_ctrl_t *c) { *c = (temp_ctrl_t){0}; }
void temp_ctrl_step(temp_ctrl_t *c, float measured, float sp, float Ts)
{
    float e = sp - measured;
    float delta = e * Ts;
    c->setpoint_C = sp;
    /* control_sim.py:54-56 / reference_models.py:temp_ctrl_step.
     * 원본 순서: clip 적분 -> clip 출력 -> 포화 시 delta 차감.
     * 이전 적분 복원 또는 차감 후 재clip으로 바꾸지 않는다. */
    c->integral_C_s = clip(c->integral_C_s + delta,
                           -FW_TEMP_I_LIMIT_C_S, FW_TEMP_I_LIMIT_C_S);
    c->power_W = clip(FW_TEMP_KP_W_C * e + FW_TEMP_KI_W_C_S * c->integral_C_s,
                      0.0f, FW_HEATER_MAX_W);
    if (c->power_W >= FW_HEATER_MAX_W || c->power_W <= 0.0f)
        c->integral_C_s -= delta;
    c->duty = c->power_W / FW_HEATER_MAX_W;
}
float temp_profile_C(float t)
{
    /* control_sim.py:65, HANDOFF 3.2절: 원본 prof의 분기와 상한. */
    if (t < FW_TEMP_RAMP_START_S) return FW_TEMP_INITIAL_C;
    if (t < FW_TEMP_HOLD_START_S) {
        float sp = FW_TEMP_INITIAL_C + FW_TEMP_RAMP_K_S * (t - FW_TEMP_RAMP_START_S);
        return sp < FW_TEMP_FINAL_C ? sp : FW_TEMP_FINAL_C;
    }
    return FW_TEMP_FINAL_C;
}
