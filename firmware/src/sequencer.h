#ifndef SEQUENCER_H
#define SEQUENCER_H
#include "force_ctrl.h"
typedef enum {
    FW_SEQ_APPROACH, FW_SEQ_RAMP, FW_SEQ_HOLD,
    FW_SEQ_RELEASE, FW_SEQ_RETRACT, FW_SEQ_DONE
} fw_sequence_phase_t;
typedef struct { fw_sequence_phase_t phase; float retract_mm; } sequencer_t;
void sequencer_init(sequencer_t *s);
void sequencer_release(sequencer_t *s);
void sequencer_step(sequencer_t *s, force_ctrl_t *c, const fw_recipe_t *r,
                    float force_N, uint32_t tick_ms);
#endif
