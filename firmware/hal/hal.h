#ifndef HAL_H
#define HAL_H
/* 센서 N, 지령 mm/s. src는 이 인터페이스만 통해 하드웨어에 접근한다. */
float hal_read_force_N(void);
void hal_write_z_velocity_mm_s(float velocity);
/* 온도 센서 ℃, 히터 지령 W. PWM duty=P/400 구동은 HAL 몫 (HANDOFF 3.2절). */
float hal_read_temp_C(void);
void hal_write_heater_W(float power);
#endif
