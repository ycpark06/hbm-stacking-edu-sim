#ifndef HAL_H
#define HAL_H
/* 센서 N, 지령 mm/s. src는 이 인터페이스만 통해 하드웨어에 접근한다. */
float hal_read_force_N(void);
void hal_write_z_velocity_mm_s(float velocity);
#endif
