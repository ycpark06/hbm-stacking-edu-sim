#ifndef FW_CONFIG_H
#define FW_CONFIG_H
/* 설계값: HANDOFF 2절의 호스트 호출 주기. 원문 피드백 요구는 10 ms. */
#define FW_TICK_S 0.001f
/* 10장 10.2절, control_sim.py:6: 기본 하중 루프 1 ms. */
#define FW_FORCE_PERIOD_MS 1u
/* 10장 10.2절, control_sim.py:8-10,40: 직렬 강성 및 PI 대역폭. */
#define FW_CONTACT_STIFFNESS_N_MM 2000.0f
#define FW_PI 3.14159265358979323846f
#define FW_FORCE_CROSSOVER_HZ 20.0f
#define FW_FORCE_INTEGRAL_HZ 2.0f
/* control_sim.py:24,26: 접촉 문턱과 램프 시작 하중. */
#define FW_CONTACT_FORCE_N 0.1f
#endif
