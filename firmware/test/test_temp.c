#include <float.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "fw.h"
#include "fw_config.h"
#include "hal_host.h"

typedef struct { const char *name; double value; } metric_t;
typedef struct {
    const char *id;
    unsigned period_ms;
    double end_s;
    metric_t expected[6];
} temp_case_t;
typedef struct { const char *id; double time_s, expected_C; } profile_case_t;
#include "golden_temp_cases.h"
typedef struct { double overshoot, stab150, stab300, ramp, hold_W, at50; } result_t;

static result_t simulate(const temp_case_t *g)
{
    /* control_sim.py:45-64 / reference_models.py:temp_sim:
     * double test plant, float firmware; noise=0, explicit Euler dt=1 ms.
     * Tip C=8.77 J/K; MACOR rho, cp, dimensions, conductivity as original.
     * All node fluxes use old Tm; thermocouple uses updated tip T. */
    const double dt = 0.001, C = 8.77, A = 0.0011, ambient = 20.0;
    const double Cm = 2.52e3 * 790 * 0.04 * 0.04 * 0.016;
    const double Gseg = 1.46 * 0.0016 / (0.016 / 3);
    const double tc_tau = 0.005;
    double T = ambient, Ttc = ambient, Tm[3] = {20, 20, 20};
    double sum_x = 0, sum_y = 0, sum_xx = 0, sum_xy = 0, hold_sum = 0;
    unsigned i, j, nr = 0, nh = 0;
    result_t r = {.overshoot = -DBL_MAX};
    hal_host_reset();
    fw_init();
    if (!fw_set_temp_period_ms(g->period_ms)) return r;
    for (i = 0; i < (unsigned)(g->end_s / dt); ++i) {
        double t = i * dt, P, loss, q1, q[3], fl01, fl12;
        hal_host_set_temp_C((float)Ttc);
        fw_step_1ms();
        P = hal_host_get_heater_W();
        /* Original loss area 0.0011 m², h=10, eps=0.3; Kelvin offset 273.
         * control_sim.py:57-63 (unused Gm omitted). */
        loss = 10 * A * (T - ambient) + 0.3 * 5.67e-8 * A *
               (pow(T + 273, 4) - pow(ambient + 273, 4));
        q1 = Gseg * 2 * (T - Tm[0]);
        T += dt * (P - loss - q1) / C;
        fl01 = Gseg * (Tm[0] - Tm[1]);
        fl12 = Gseg * (Tm[1] - Tm[2]);
        q[0] = q1 - fl01;
        q[1] = fl01 - fl12;
        q[2] = fl12 - Gseg * 2 * (Tm[2] - ambient);
        for (j = 0; j < 3; ++j) Tm[j] += dt * q[j] / (Cm / 3);
        Ttc += dt * (T - Ttc) / tc_tau;
        /* control_sim.py:64,69-72: post-update temperature sampled each
         * 50 ms, labelled with pre-update time. Strict open masks. */
        if (i % 50u == 0u) {
            if (t > 45) r.overshoot = fmax(r.overshoot, T - 300);
            if (t > 25 && t < 40) r.stab150 = fmax(r.stab150, fabs(T - 150));
            if (t > 65 && t < 120) {
                r.stab300 = fmax(r.stab300, fabs(T - 300));
                hold_sum += P; ++nh;
            }
            if (t > 41 && t < 47) {
                sum_x += t; sum_y += T; sum_xx += t*t; sum_xy += t*T; ++nr;
            }
            /* 50 s is an exact recorded sample, so numpy.interp returns T. */
            if (i == 50000u) r.at50 = T;
        }
    }
    /* Ordinary least squares with intercept, equivalent to numpy.polyfit(1). */
    r.ramp = (nr * sum_xy - sum_x * sum_y) / (nr * sum_xx - sum_x * sum_x);
    r.hold_W = hold_sum / nh;
    return r;
}
static double metric(const char *name, result_t r)
{
    if (!strcmp(name, "overshoot")) return r.overshoot;
    if (!strcmp(name, "stab_150")) return r.stab150;
    if (!strcmp(name, "stab_300")) return r.stab300;
    if (!strcmp(name, "ramp")) return r.ramp;
    if (!strcmp(name, "P_hold")) return r.hold_W;
    if (!strcmp(name, "T_at_50s")) return r.at50;
    return NAN;
}
static unsigned check_contract(void)
{
    unsigned failed = 0, tick;
    temp_ctrl_t c;
    float power;
#define CHECK(x) do { if (!(x)) { printf("Temperature contract FAIL: %s\n", #x); ++failed; } } while (0)
    /* Exact-boundary saturation also rolls back; order after clipping matters. */
    temp_ctrl_init(&c);
    c.integral_C_s = 29.0f;
    temp_ctrl_step(&c, 0.0f, 100.0f, 0.1f);
    CHECK(c.integral_C_s == 20.0f && c.power_W == 400.0f && c.duty == 1.0f);
    c.integral_C_s = -29.0f;
    temp_ctrl_step(&c, 100.0f, 0.0f, 0.1f);
    CHECK(c.integral_C_s == -20.0f && c.power_W == 0.0f && c.duty == 0.0f);
    c.integral_C_s = 30.0f;
    temp_ctrl_step(&c, 149.0f, 150.0f, 0.01f);
    CHECK(c.integral_C_s == 30.0f && c.power_W == 205.0f);
    /* Exactly 400 W also rolls back (not just raw output >400 W). */
    c.integral_C_s = -(16.0f * 0.01f);
    temp_ctrl_step(&c, 134.0f, 150.0f, 0.01f);
    CHECK(c.power_W == 400.0f && c.integral_C_s == -(16.0f * 0.01f));
    c.integral_C_s = 0.0f;
    temp_ctrl_step(&c, 150.0f, 150.0f, 0.01f);
    CHECK(c.power_W == 0.0f && c.integral_C_s == 0.0f);
    c.integral_C_s = 2.0f;
    temp_ctrl_step(&c, 149.0f, 150.0f, 0.01f);
    CHECK(fabsf(c.power_W - 37.06f) < 1e-4f);
    CHECK(c.duty == c.power_W / FW_HEATER_MAX_W);
    hal_host_reset(); fw_init();
    CHECK(hal_host_get_heater_W() == 0.0f);
    hal_host_set_temp_C(149.0f); fw_step_1ms();
    power = hal_host_get_heater_W();
    CHECK(fabsf(power - 25.06f) < 1e-4f);
    hal_host_set_temp_C(20.0f);
    for (tick = 1; tick < FW_TEMP_PERIOD_MS; ++tick) fw_step_1ms();
    CHECK(hal_host_get_heater_W() == power);
    fw_step_1ms(); CHECK(hal_host_get_heater_W() == 400.0f);
    CHECK(!fw_set_temp_period_ms(0u));
    /* Explicit 100 ms divider must hold output through ticks 1..99. */
    fw_init(); CHECK(fw_set_temp_period_ms(100u));
    hal_host_set_temp_C(149.0f); fw_step_1ms();
    power = hal_host_get_heater_W();
    CHECK(fabsf(power - 25.6f) < 1e-4f);
    hal_host_set_temp_C(20.0f);
    for (tick = 1; tick < 100; ++tick) fw_step_1ms();
    CHECK(hal_host_get_heater_W() == power);
    fw_step_1ms(); CHECK(hal_host_get_heater_W() == 400.0f);
    fw_init();
    CHECK(fw_get_temp_state()->integral_C_s == 0.0f);
    CHECK(hal_host_get_heater_W() == 0.0f);
#undef CHECK
    printf("Temperature contract: %s\n", failed ? "FAIL" : "PASS");
    return failed;
}
int main(void)
{
    unsigned i, j, checks = 0, failures = 0;
    puts("id.metric | golden | fw | abs_error | result");
    for (i = 0; i < sizeof(temp_cases)/sizeof(temp_cases[0]); ++i) {
        result_t r = simulate(&temp_cases[i]);
        for (j = 0; j < 6; ++j) {
            const metric_t *m = &temp_cases[i].expected[j];
            double v = metric(m->name, r), err = fabs(v - m->value);
            /* Stage B: relative 1e-3; temperatures also absolute 1e-3 C. */
            double absolute = (!strcmp(m->name, "ramp") || !strcmp(m->name, "P_hold")) ? 0 : 1e-3;
            int pass = isfinite(v) && err <= fmax(1e-3 * fabs(m->value), absolute);
            printf("%s.%s | %.12g | %.12g | %.6g | %s\n", temp_cases[i].id,
                   m->name, m->value, v, err, pass ? "PASS" : "FAIL");
            ++checks; if (!pass) ++failures;
        }
    }
    printf("Temperature golden: %u/%u PASS (2 vectors), %u FAIL\n", checks-failures, checks, failures);
    checks = 0;
    for (i = 0; i < sizeof(profile_cases)/sizeof(profile_cases[0]); ++i) {
        const profile_case_t *p = &profile_cases[i];
        double v = temp_profile_C((float)p->time_s);
        int pass = isfinite(v) && fabs(v-p->expected_C) <= fmax(1e-3*fabs(p->expected_C), 1e-3);
        printf("%s.sp | %.12g | %.12g | %.6g | %s\n", p->id, p->expected_C,
               v, fabs(v-p->expected_C), pass ? "PASS" : "FAIL");
        if (pass) ++checks; else ++failures;
    }
    printf("Profile golden: %u/6 PASS\n", checks);
    failures += check_contract();
    return failures ? 1 : 0;
}
