#ifndef FW_H
#define FW_H
#include "force_ctrl.h"
void fw_init(void);
/* 유효 레시피는 제어 상태와 시간 기준을 초기화한다. 실패는 0, 성공은 1. */
int fw_set_recipe(const fw_recipe_t *recipe);
void fw_step_1ms(void);
const force_ctrl_t *fw_get_force_state(void);
#endif
