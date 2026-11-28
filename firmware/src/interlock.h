#ifndef INTERLOCK_H
#define INTERLOCK_H
typedef struct { int warning, latched, brake, sto, dual_heater_blocked; } interlock_t;
void interlock_update(interlock_t *state, float force_N, float temp_C, int hw_fault);
/* Previous accepted outputs enforce one all-off tick before switching. */
void interlock_heaters(interlock_t *state, float *head_W, float *reflow_W,
                       float previous_head_W, float previous_reflow_W);
void interlock_reset(interlock_t *state, float force_N, float temp_C, int hw_fault);
#endif
