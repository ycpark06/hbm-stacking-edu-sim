#ifndef TEMP_CTRL_H
#define TEMP_CTRL_H
typedef struct {
    float integral_C_s, setpoint_C, power_W, duty;
} temp_ctrl_t;
void temp_ctrl_init(temp_ctrl_t *ctrl);
void temp_ctrl_step(temp_ctrl_t *ctrl, float measured_C, float setpoint_C,
                    float period_s);
float temp_profile_C(float time_s);
#endif
