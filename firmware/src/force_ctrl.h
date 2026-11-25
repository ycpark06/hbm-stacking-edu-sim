#ifndef FORCE_CTRL_H
#define FORCE_CTRL_H
#include <stdint.h>
typedef enum { FW_MODE_REFERENCE = 0, FW_MODE_FIRMWARE = 1 } fw_mode_t;
typedef struct {
    float k_spring_N_mm, target_N, ramp_N_s, approach_mm_s;
    uint32_t force_period_ms;
    fw_mode_t mode;
} fw_recipe_t;
typedef struct {
    float k_eff, Kp, Ki, integral_N_s, setpoint_N, velocity_mm_s;
    float t_contact_s, integral_limit_N_s;
    uint32_t contact_tick_ms;
    int contacted;
} force_ctrl_t;
void force_ctrl_init(force_ctrl_t *ctrl, const fw_recipe_t *recipe);
void force_ctrl_track(force_ctrl_t *ctrl, const fw_recipe_t *recipe,
                      float measured_N, float setpoint_N);
void force_ctrl_step(force_ctrl_t *ctrl, const fw_recipe_t *recipe,
                     float measured_N, uint32_t tick_ms);
#endif
