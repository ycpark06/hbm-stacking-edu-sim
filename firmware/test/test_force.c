#include <float.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "fw.h"
#include "hal.h"
#include "hal_host.h"

typedef struct { const char *name; double value; } metric_t;
typedef struct {
    const char *id;
    int gains_only;
    double spring, target, ramp, approach;
    unsigned period_ms;
    double end_s, therm;
    unsigned count;
    metric_t expected[4];
} golden_case_t;
#include "golden_cases.h"

typedef struct {
    double contact, overshoot, ss_err, peak, force_1s;
} result_t;

static result_t simulate(const golden_case_t *g)
{
    /* Plant constants: control_sim.py:6-19,29-33 / reference_models.py:312-346.
     * No noise; double plant, float controller connected only through host HAL. */
    const double dt = 1e-5, tau = 0.8e-3;
    const double ke = 1.0 / (1.0 / g->spring + 1.0 / 2000.0);
    double z = -0.02, z_cmd = -0.02, t = 0.0;
    double delay[50] = {0.0}; /* 0.5 ms / 10 us pure ADC delay. */
    double max_force = -DBL_MAX, prev_t = 0.0, prev_f = 0.0;
    unsigned slot = 0, i, n = (unsigned)(g->end_s / dt);
    result_t r = {-1.0, 0.0, 0.0, -DBL_MAX, 0.0};
    fw_recipe_t recipe = {(float)g->spring, (float)g->target, (float)g->ramp,
                          (float)g->approach, g->period_ms, FW_MODE_REFERENCE};
    hal_host_reset();
    fw_init();
    if (!fw_set_recipe(&recipe)) return r;
    for (i = 0; i < n; ++i) {
        double f = fmax(0.0, ke * (z + g->therm * t));
        double delayed = delay[slot];
        delay[slot] = f;
        slot = (slot + 1u) % 50u;
        /* control_sim.py:21: first control at i=0, then each 1 ms tick.
         * fw_step_1ms divides ticks for the 10 ms recipe. */
        if (i % 100u == 0u) {
            hal_host_set_force_N((float)delayed);
            fw_step_1ms();
            if (r.contact < 0.0 && fw_get_force_state()->contacted) r.contact = t;
        }
        z_cmd += (double)hal_host_get_z_velocity_mm_s() * dt;
        z += (z_cmd - z) * dt / tau;
        if (i % 100u == 0u) {
            double sp = fw_get_force_state()->setpoint_N;
            max_force = fmax(max_force, f);
            /* Original hold mask is strict >; inventory section 6 item 14:
             * all metrics use pre-integration F_true recorded every 1 ms. */
            if (r.contact >= 0.0) {
                if (t > r.contact + g->target / g->ramp + 0.5)
                    r.ss_err = fmax(r.ss_err, fabs(f - g->target));
                /* reference_models.py:349-353: strict open 0.3 s window. */
                if (t > r.contact && t < r.contact + 0.3)
                    r.peak = fmax(r.peak, f - sp);
                /* reference_models.py:768-770: numpy.interp on recorded F. */
                if (prev_t <= r.contact + 1.0 && t >= r.contact + 1.0)
                    r.force_1s = prev_f + (f - prev_f) *
                        ((r.contact + 1.0 - prev_t) / (t - prev_t));
            }
            prev_t = t;
            prev_f = f;
        }
        t += dt;
    }
    r.overshoot = max_force - g->target;
    return r;
}

static double metric(const char *name, result_t r, const force_ctrl_t *c)
{
    if (!strcmp(name, "k_eff")) return c->k_eff;
    if (!strcmp(name, "Kp")) return c->Kp;
    if (!strcmp(name, "Ki")) return c->Ki;
    if (!strcmp(name, "t_contact"))
        return c->contacted ? c->t_contact_s : -1.0;
    if (!strcmp(name, "overshoot")) return r.overshoot;
    if (!strcmp(name, "ss_err")) return r.ss_err;
    if (!strcmp(name, "peak_over_sp_0p3s")) return r.peak;
    if (!strcmp(name, "F_at_t_contact_plus_1s")) return r.force_1s;
    return NAN;
}

/* Contract checks cover timing/transition behavior beyond aggregate metrics. */
static unsigned check_contract(void)
{
    fw_recipe_t recipe = {50.0f, 5.0f, 5.0f, 0.02f, 10u, FW_MODE_REFERENCE};
    unsigned tick, failed = 0;
    float velocity;
#define CHECK(condition) do { if (!(condition)) { \
    printf("Contract FAIL: %s\n", #condition); ++failed; } } while (0)
    hal_host_reset();
    fw_init();
    CHECK(fw_set_recipe(&recipe));
    hal_host_set_force_N(0.1f);
    fw_step_1ms(); /* tick 0: equality must remain approach. */
    CHECK(!fw_get_force_state()->contacted);
    hal_host_set_force_N(0.2f);
    for (tick = 1; tick < 10; ++tick) fw_step_1ms();
    CHECK(!fw_get_force_state()->contacted);
    CHECK(hal_host_get_z_velocity_mm_s() == recipe.approach_mm_s);
    fw_step_1ms(); /* tick 10: contact and first PI calculation together. */
    CHECK(fw_get_force_state()->contacted);
    CHECK(fw_get_force_state()->contact_tick_ms == 10u);
    CHECK(fabsf(fw_get_force_state()->integral_N_s + 0.001f) < 1e-8f);
    CHECK(fw_get_force_state()->setpoint_N == 0.1f);
    CHECK(hal_host_get_z_velocity_mm_s() < 0.0f);
    velocity = hal_host_get_z_velocity_mm_s();
    hal_host_set_force_N(100.0f);
    fw_step_1ms();
    CHECK(hal_host_get_z_velocity_mm_s() == velocity);
    CHECK(fw_set_recipe(&recipe));
    CHECK(!fw_get_force_state()->contacted);
    CHECK(fw_get_force_state()->integral_N_s == 0.0f);
    CHECK(hal_host_get_z_velocity_mm_s() == recipe.approach_mm_s);
    recipe.force_period_ms = 0u;
    CHECK(!fw_set_recipe(&recipe));
    CHECK(!fw_set_recipe(NULL));
    fw_init(); /* Default loop executes each 1 ms tick. */
    hal_host_set_force_N(0.2f);
    fw_step_1ms();
    CHECK(fw_get_force_state()->contacted);
    CHECK(fw_get_force_state()->contact_tick_ms == 0u);
    fw_step_1ms();
    CHECK(fw_get_force_state()->setpoint_N > 0.1f);
#undef CHECK
    printf("Contract: %s\n", failed ? "FAIL" : "PASS");
    return failed;
}

int main(void)
{
    unsigned i, j, failures = 0, checks = 0;
    puts("id.metric | golden | fw | abs_error | result");
    for (i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        const golden_case_t *g = &cases[i];
        result_t r = {0};
        if (g->gains_only) {
            fw_recipe_t recipe = {(float)g->spring, (float)g->target,
                (float)g->ramp, (float)g->approach, g->period_ms, FW_MODE_REFERENCE};
            fw_init();
            if (!fw_set_recipe(&recipe)) return 1;
        } else {
            r = simulate(g);
        }
        for (j = 0; j < g->count; ++j) {
            const metric_t *m = &g->expected[j];
            double value = metric(m->name, r, fw_get_force_state());
            double error = fabs(value - m->value);
            /* HANDOFF 4.1 / stage A: max(relative 1e-3, absolute 1e-4 N).
             * Contact time uses absolute 1e-3 s per stage A instruction. */
            double absolute = !strcmp(m->name, "t_contact") ? 1e-3 : 1e-4;
            double limit = fmax(1e-3 * fabs(m->value), absolute);
            int pass = isfinite(value) && error <= limit;
            printf("%s.%s | %.12g | %.12g | %.6g | %s\n",
                   g->id, m->name, m->value, value, error, pass ? "PASS" : "FAIL");
            ++checks;
            if (!pass) ++failures;
        }
    }
    printf("Golden: %u/%u PASS (%u vectors), %u FAIL\n", checks - failures,
           checks, (unsigned)(sizeof(cases) / sizeof(cases[0])), failures);
    failures += check_contract();
    return failures ? 1 : 0;
}
