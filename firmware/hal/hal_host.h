#ifndef HAL_HOST_H
#define HAL_HOST_H
/* PC 테스트 플랜트 전용. MCU/wasm HAL의 구현 대상이 아니다. */
void hal_host_reset(void);
void hal_host_set_force_N(float force);
float hal_host_get_z_velocity_mm_s(void);
void hal_host_set_temp_C(float temp);
float hal_host_get_heater_W(void);
#endif
