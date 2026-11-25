#ifndef FW_H
#define FW_H
#include "force_ctrl.h"
#include "temp_ctrl.h"
#include "interlock.h"
#include "sequencer.h"
void fw_init(void);
fw_mode_t fw_get_mode(void);
/* 유효 레시피는 제어 상태와 시간 기준을 초기화한다. 실패는 0, 성공은 1. */
int fw_set_recipe(const fw_recipe_t *recipe);
/* 설계값: 1 ms 정수 분주 설정. 0은 거부하며 상태를 바꾸지 않는다.
 * fw_init/fw_set_recipe는 기본 10 ms로 복원하고 온도 상태도 초기화한다.
 * 이 함수는 주기만 변경한다. 실행 시점은 공유 tick의 배수(t=0 포함). */
int fw_set_temp_period_ms(unsigned period_ms);
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
