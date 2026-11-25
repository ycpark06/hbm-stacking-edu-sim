#include "sequencer.h"
#include "fw_config.h"
void sequencer_init(sequencer_t *s) { *s = (sequencer_t){FW_SEQ_APPROACH, 0.0f}; }
void sequencer_release(sequencer_t *s)
{
    if (s->phase <= FW_SEQ_HOLD) s->phase = FW_SEQ_RELEASE;
}
void sequencer_step(sequencer_t *s, force_ctrl_t *c, const fw_recipe_t *r,
                    float f, uint32_t tick)
{
    float Ts = (float)r->force_period_ms * FW_TICK_S;
    if (s->phase == FW_SEQ_RELEASE) {
        float sp = c->setpoint_N - r->ramp_N_s * Ts;
        force_ctrl_track(c, r, f, sp > 0.0f ? sp : 0.0f);
        /* 설계값: 접촉 판정 문턱 이하로 실제 하중이 풀린 뒤 상승한다.
         * HANDOFF 2절 해제 단계; 하중 0 설정까지 램프 다운을 완료한다. */
        if (c->setpoint_N == 0.0f && f <= FW_CONTACT_FORCE_N)
            s->phase = FW_SEQ_RETRACT;
    } else if (s->phase == FW_SEQ_RETRACT) {
        c->velocity_mm_s = -r->approach_mm_s;
        /* 설계값: 잔류 탄성 압축을 먼저 풀고, 무하중부터 초기 간극만큼
         * 더 상승한다. 저레인지에서는 문턱 0.1 N도 50 μm 압축이다. */
        if (f <= 0.0f) s->retract_mm += r->approach_mm_s * Ts;
        if (s->retract_mm >= FW_RETRACT_DISTANCE_MM) {
            s->phase = FW_SEQ_DONE;
            c->velocity_mm_s = 0.0f;
        }
    } else if (s->phase == FW_SEQ_DONE) {
        c->velocity_mm_s = 0.0f;
    } else {
        force_ctrl_step(c, r, f, tick);
        if (c->contacted)
            s->phase = c->setpoint_N >= r->target_N ? FW_SEQ_HOLD : FW_SEQ_RAMP;
    }
}
