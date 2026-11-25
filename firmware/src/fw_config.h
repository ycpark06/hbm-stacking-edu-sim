#ifndef FW_CONFIG_H
#define FW_CONFIG_H
/* 설계값: HANDOFF 2절의 호스트 호출 주기. 원문 피드백 요구는 10 ms. */
#define FW_TICK_S 0.001f
/* 10장 10.2절, control_sim.py:6: 기본 하중 루프 1 ms. */
#define FW_FORCE_PERIOD_MS 1u
#endif
