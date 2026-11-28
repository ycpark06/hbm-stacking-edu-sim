#ifndef FW_H
#define FW_H
#include "force_ctrl.h"
#include "temp_ctrl.h"
#include "interlock.h"
#include "sequencer.h"
void fw_init(void);
fw_mode_t fw_get_mode(void);
/* 기존 성공 1 / 일반 유효성 실패 0 유지. 새 능력 초과 실패는 -1.
 * 호출자는 참/거짓 대신 == FW_OK로 성공을 확인해야 한다.
 * 모든 실패는 이전 레시피·제어 상태·HAL 출력을 보존한다. */
enum {
    FW_ERR_RAMP_EXCEEDS_CAPABILITY = -1, /* FIRMWARE ramp > k_spring*v_max */
    FW_ERR_INVALID_RECIPE = 0,
    FW_OK = 1
};
/* 프리셋은 값으로 반환하며 제어 상태를 바꾸지 않는다. 기본은 고레인지. */
fw_recipe_t fw_recipe_low_range_default(void);
fw_recipe_t fw_recipe_high_range_default(void);
/* 유효 레시피는 제어 상태와 시간 기준을 초기화한다.
 * REFERENCE는 golden 대조용으로 램프 능력 검사를 적용하지 않는다.
 * wasm의 fw_wasm_set_recipe도 이 반환값을 그대로 전달한다. */
int fw_set_recipe(const fw_recipe_t *recipe);
/* 설계값: 1 ms 정수 분주 설정. 0은 거부하며 상태를 바꾸지 않는다.
 * fw_init/fw_set_recipe는 기본 10 ms로 복원하고 온도 상태도 초기화한다.
 * 이 함수는 주기만 변경한다. 실행 시점은 공유 tick의 배수(t=0 포함). */
int fw_set_temp_period_ms(unsigned period_ms);
/* Requests apply on next 1 ms tick. Init/accepted recipe clears reflow and
 * enables head PI. Nonpositive/NaN reflow -> 0; positive capped at design max. */
void fw_set_head_heater_enabled(int enabled);
void fw_request_reflow_heater_W(float power_W);
float fw_get_reflow_heater_power(void); /* accepted output, W */
int fw_get_dual_heater_blocked(void); /* non-latching warning, no Z freeze */
void fw_step_1ms(void);
/* HANDOFF 3.3: 래치 해제 전용. 조건이 남아 있으면 즉시 다시 래치. */
void fw_reset_latch(void);
/* HANDOFF 2절: 유지 시간은 호출자가 결정, 해제 요청 후 램프 다운/상승. */
void fw_release(void);
const interlock_t *fw_get_interlock_state(void);
const sequencer_t *fw_get_sequence_state(void);
const temp_ctrl_t *fw_get_temp_state(void);
const force_ctrl_t *fw_get_force_state(void);
#endif
