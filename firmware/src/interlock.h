#ifndef INTERLOCK_H
#define INTERLOCK_H
typedef struct { int warning, latched, brake, sto; } interlock_t;
void interlock_update(interlock_t *state, float force_N, float temp_C, int hw_fault);
void interlock_reset(interlock_t *state, float force_N, float temp_C, int hw_fault);
#endif
