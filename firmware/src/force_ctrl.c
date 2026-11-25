#include "force_ctrl.h"
#include "fw_config.h"
void force_ctrl_init(force_ctrl_t *c, const fw_recipe_t *r)
{
    float wc = 2.0f * FW_PI * FW_FORCE_CROSSOVER_HZ;
    float wi = 2.0f * FW_PI * FW_FORCE_INTEGRAL_HZ;
    *c = (force_ctrl_t){0};
    /* control_sim.py:9-10,40; 모든 제어 연산은 float. */
    c->k_eff = 1.0f / (1.0f / r->k_spring_N_mm +
                         1.0f / FW_CONTACT_STIFFNESS_N_MM);
    c->Kp = wc / c->k_eff;
    c->Ki = wc * wi / c->k_eff;
    c->velocity_mm_s = r->approach_mm_s;
}
void force_ctrl_step(force_ctrl_t *c, const fw_recipe_t *r, float f, uint32_t tick)
{
    if (!c->contacted) {
        c->velocity_mm_s = r->approach_mm_s;
        if (f > FW_CONTACT_FORCE_N) {
            c->contacted = 1;
            c->contact_tick_ms = tick;
            c->t_contact_s = (float)tick * FW_TICK_S;
            c->integral_N_s = 0.0f;
        }
    }
    if (c->contacted) {
        /* control_sim.py:26-28: 접촉 판정과 같은 주기부터 PI 실행.
         * REFERENCE는 원본처럼 출력/적분 제한과 anti-windup이 없다.
         * 설계값: 시간은 정수 ms 차이를 float 초로 변환해 누적 오차 방지. */
        float elapsed = (float)(tick - c->contact_tick_ms) * FW_TICK_S;
        float sp = FW_CONTACT_FORCE_N + r->ramp_N_s * elapsed;
        float e;
        c->setpoint_N = sp < r->target_N ? sp : r->target_N;
        e = c->setpoint_N - f;
        c->integral_N_s += e * ((float)r->force_period_ms * FW_TICK_S);
        c->velocity_mm_s = c->Kp * e + c->Ki * c->integral_N_s;
    }
}
