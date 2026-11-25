#include "interlock.h"
#include "fw_config.h"
/* 실물은 비교기·래치 회로가 소프트웨어와 무관하게 차단한다(10장 10.4절).
 * 펌웨어 래치는 그 동작을 모사하고 상태를 보고한다. */
void interlock_update(interlock_t *s, float f, float t, int hw)
{
    s->warning = f >= FW_WARN_FORCE_N || t >= FW_WARN_TEMP_C;
    if (f >= FW_FAULT_FORCE_N || t >= FW_FAULT_TEMP_C || hw) s->latched = 1;
    s->brake = s->sto = s->latched;
}
void interlock_reset(interlock_t *s, float f, float t, int hw)
{
    s->latched = 0;
    interlock_update(s, f, t, hw);
}
