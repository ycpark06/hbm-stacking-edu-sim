#ifndef HAL_H
#define HAL_H
/* 센서 N, 지령 mm/s. src는 이 인터페이스만 통해 하드웨어에 접근한다. */
float hal_read_force_N(void);
void hal_write_z_velocity_mm_s(float velocity);
/* 호스트 플랜트 연결: 실제 MCU HAL에서는 구현할 필요가 없다. */
void hal_host_reset(void);
void hal_host_set_force_N(float force);
float hal_host_get_z_velocity_mm_s(void);
#endif
