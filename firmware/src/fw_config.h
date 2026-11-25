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
/* 10장 10.3절, HANDOFF 3.2절, control_sim.py:45,54-56.
 * 10 ms는 원문 피드백 요구; 100 ms는 원본 비교 시나리오에서 설정. */
#define FW_TEMP_PERIOD_MS 10u
#define FW_TEMP_KP_W_C 25.0f
#define FW_TEMP_KI_W_C_S 6.0f
/* Kd=0: PI만 계산 (control_sim.py:45). */
#define FW_TEMP_I_LIMIT_C_S 30.0f
#define FW_HEATER_MAX_W 400.0f
/* control_sim.py:65 프로파일 가정값. 원문 최고 온도 KPI와 구분. */
#define FW_TEMP_INITIAL_C 150.0f
#define FW_TEMP_FINAL_C 300.0f
#define FW_TEMP_RAMP_K_S 20.0f
#define FW_TEMP_RAMP_START_S 40.0f
#define FW_TEMP_HOLD_START_S 70.0f
#endif
