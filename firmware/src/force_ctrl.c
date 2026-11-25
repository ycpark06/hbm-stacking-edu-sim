#include "force_ctrl.h"
void force_ctrl_init(force_ctrl_t *c, const fw_recipe_t *r)
{
    *c = (force_ctrl_t){0};
    c->velocity_mm_s = r->approach_mm_s;
}
void force_ctrl_step(force_ctrl_t *c, const fw_recipe_t *r, float f, uint32_t tick)
{
    (void)f; (void)tick;
    c->velocity_mm_s = r->approach_mm_s;
}
