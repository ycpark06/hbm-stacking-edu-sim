#include <float.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "fw.h"
#include "fw_config.h"
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
    double integral_max, ramp_integral_max, hold_min, hold_max, hold_last;
    double velocity_max, reach, settled_err, i_limit, early_err;
    unsigned hold_samples, settled_samples, saturated_ticks;
    int interlocked;
} result_t;

/* 설계값/가정값 테스트 옵션: limit=0은 단계 A 원본 플랜트.
 * limit=1: 실제 Z 이동속도 ±0.5 mm/s (10장 최대 접근 속도).
 * block_s: 접촉+block_start_s부터 구동기 고착, 밀린 위치 명령은 폐기한다. */
static result_t simulate_options(const golden_case_t *g, fw_mode_t mode,
                                  int limit, double block_s, double block_start_s)
{
    /* Plant constants: control_sim.py:6-19,29-33 / reference_models.py:312-346.
     * No noise; double plant, float controller connected only through host HAL. */
    const double dt = 1e-5, tau = 0.8e-3;
    const double ke = 1.0 / (1.0 / g->spring + 1.0 / 2000.0);
    double z = -0.02, z_cmd = -0.02, t = 0.0;
    double delay[50] = {0.0}; /* 0.5 ms / 10 us pure ADC delay. */
    double max_force = -DBL_MAX, prev_t = 0.0, prev_f = 0.0;
    unsigned slot = 0, i, n = (unsigned)(g->end_s / dt);
    result_t r = {.contact = -1.0, .peak = -DBL_MAX,
                  .hold_min = DBL_MAX, .hold_max = -DBL_MAX, .reach = -1.0};
    fw_recipe_t recipe = {(float)g->spring, (float)g->target, (float)g->ramp,
                          (float)g->approach, g->period_ms, mode};
    hal_host_reset();
    fw_reset_latch();
    fw_init();
    if (fw_set_recipe(&recipe) != FW_OK) return r;
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
            const force_ctrl_t *c = fw_get_force_state();
            r.interlocked |= fw_get_interlock_state()->warning || fw_get_interlock_state()->latched;
            if (r.contact < 0.0 && c->contacted) r.contact = t;
            /* Observe actual state after each selected mode update.
             * Sample every 1 ms call, including every actual PI update. */
            if (c->contacted) {
                double integral = c->integral_N_s;
                r.i_limit = c->integral_limit_N_s;
                if (fabs(c->velocity_mm_s) >= FW_FORCE_V_MAX_MM_S) ++r.saturated_ticks;
                r.integral_max = fmax(r.integral_max, fabs(integral));
                r.velocity_max = fmax(r.velocity_max, fabs(c->velocity_mm_s));
                if (t <= r.contact + (g->target - 0.1) / g->ramp)
                    r.ramp_integral_max = fmax(r.ramp_integral_max, fabs(integral));
                /* Same strict hold mask as original force_sim. */
                if (t > r.contact + g->target / g->ramp + 0.5) {
                    r.hold_min = fmin(r.hold_min, integral);
                    r.hold_max = fmax(r.hold_max, integral);
                    r.hold_last = integral;
                }
            }
        }
        {
            double v = hal_host_get_z_velocity_mm_s();
            /* 구동기가 수락하는 속도에도 한계 적용: 위치 backlog를
             * 무한 누적시키는 별도 가상 적분기를 만들지 않는다. */
            if (limit) v = fmax(-FW_FORCE_V_MAX_MM_S, fmin(FW_FORCE_V_MAX_MM_S, v));
            z_cmd += v * dt;
        }
        {
            double dz = (z_cmd - z) * dt / tau;
            if (limit) dz = fmax(-FW_FORCE_V_MAX_MM_S * dt,
                                  fmin(FW_FORCE_V_MAX_MM_S * dt, dz));
            if (r.contact >= 0 && t >= r.contact + block_start_s &&
                t < r.contact + block_start_s + block_s) {
                dz = 0;
                z_cmd = z; /* 고착 중 위치 명령 backlog 없음. */
            }
            z += dz;
        }
        if (i % 100u == 0u) {
            double sp = fw_get_force_state()->setpoint_N;
            if (r.contact >= 0 && r.reach < 0 && f >= 0.98 * g->target)
                r.reach = t;
            /* #13 설계값: 두 모드 동일, golden ss_err 마스크는 아래 보존. */
            if (r.reach >= 0 && t > fmax(r.contact + g->target/g->ramp + 0.5, r.reach + 0.5)) {
                r.settled_err = fmax(r.settled_err, fabs(f - g->target));
                ++r.settled_samples;
            }
            /* 지시의 1.4 s도 별도 관찰: (target-0.1)/ramp+0.5.
             * 원본 식 target/ramp+0.5는 1 N/s에서 실제로 1.5 s다. */
            if (r.contact >= 0 && t > r.contact + (g->target-0.1)/g->ramp + 0.5)
                r.early_err = fmax(r.early_err, fabs(f-g->target));
            max_force = fmax(max_force, f);
            /* Original hold mask is strict >; inventory section 6 item 14:
             * all metrics use pre-integration F_true recorded every 1 ms. */
            if (r.contact >= 0.0) {
                if (t > r.contact + g->target / g->ramp + 0.5) {
                    r.ss_err = fmax(r.ss_err, fabs(f - g->target));
                    ++r.hold_samples;
                }
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

static result_t simulate(const golden_case_t *g)
{
    return simulate_options(g, FW_MODE_REFERENCE, 0, 0, 0);
}

static unsigned check_firmware(void)
{
    unsigned i, failed = 0;
    puts("Validation 2 force (#13) | mode | ramp_N_s | overshoot_N | ss_original_N (observation) | ss_judged_N | spec_N | reach_s (observation) | result");
    for (i = 0; i < sizeof(cases)/sizeof(cases[0]); ++i) {
        const golden_case_t *g = &cases[i];
        if (!strncmp(g->id, "control.force_sim.", strlen("control.force_sim."))) {
            unsigned mode;
            for (mode = 0; mode < 2; ++mode) {
                /* golden/REFERENCE 원본 5 N/s 보존, FIRMWARE 저레인지는
                 * 승인된 설계값 1 N/s 사용. 능력 검사는 우회하지 않는다. */
                golden_case_t active = *g;
                if (mode && active.spring == 2) active.ramp = FW_FORCE_LOW_RANGE_RAMP_N_S;
                result_t r = simulate_options(&active, mode == 0 ? FW_MODE_REFERENCE : FW_MODE_FIRMWARE, 0, 0, 0);
                double spec = g->spring == 2 ? 0.06 : 0.30;
                /* #13: arrival and original error are observations only.
                 * Missing judged hold samples is a failed measurement. */
                int pass = !r.interlocked && r.settled_samples &&
                    isfinite(r.overshoot) && r.overshoot <= spec && r.settled_err <= spec;
                printf("%s | %s | %.2f | %.9g | %.9g | %.9g | %.2f | %.3f | %s\n",
                    g->id, mode == 0 ? "REFERENCE" : "FIRMWARE", active.ramp, r.overshoot,
                    r.ss_err, r.settled_err, spec, r.reach-r.contact, pass ? "PASS" : "FAIL");
                if (!pass) ++failed;
            }
        }
    }
    puts("Validation 3 | mode | overshoot_N | max_abs_I_Ns | I_max_Ns | reach_s | saturated_ticks | result");
    /* 저레인지 두 모드 모두 승인된 1 N/s로 변경한다. 상한 검사 우회 없음.
     * 정격 상한도 실제 k_eff*v_max보다 미세하게 높아 속도 한계만으로
     * 포화하며, 고착 조건도 유지해 anti-windup 효과를 비교한다.
     * 가정값 고착: high는 접촉+3.7 s부터 0.5 s, 추가 low는 접촉 직후 0.5 s. high 원본 5 N/s는
     * ±0.5 한계만 켜면 포화하지 않으므로 실제 포화를 만들기 위해 고착 주입. */
    for (i = 0; i < 3; ++i) {
        golden_case_t g = {.id = i == 0 ? "low1N-speed" :
            (i == 1 ? "high20N-block3.7+0.5s" : "low1N-block0.5s"),
            .spring = i == 1 ? 50 : 2, .target = i == 1 ? 20 : 1,
            .ramp = i == 1 ? 5 : FW_FORCE_LOW_RANGE_RAMP_N_S, .approach = 0.02, .period_ms = 1, .end_s = 12};
        double block = i == 0 ? 0 : 0.5;
        double start = i == 1 ? 3.7 : 0;
        result_t ref = simulate_options(&g, FW_MODE_REFERENCE, 1, block, start);
        result_t fw = simulate_options(&g, FW_MODE_FIRMWARE, 1, block, start);
        int pass = !ref.interlocked && !fw.interlocked &&
                   fw.reach >= 0 && ref.reach >= 0 && ref.saturated_ticks &&
                   fw.saturated_ticks && fw.overshoot < ref.overshoot &&
                   fw.integral_max <= fw.i_limit;
        printf("%s | REFERENCE | %.9g | %.9g | %.9g | %.3f | %u | %s\n",
               g.id, ref.overshoot, ref.integral_max, ref.i_limit,
               ref.reach-ref.contact, ref.saturated_ticks, pass ? "PASS" : "FAIL");
        printf("%s | FIRMWARE | %.9g | %.9g | %.9g | %.3f | %u | %s\n",
               g.id, fw.overshoot, fw.integral_max, fw.i_limit,
               fw.reach-fw.contact, fw.saturated_ticks, pass ? "PASS" : "FAIL");
        if (!pass) ++failed;
    }
    return failed;
}


static unsigned check_ramp_capability(void)
{
    unsigned failed = 0, tick;
    fw_recipe_t low = fw_recipe_low_range_default();
    fw_recipe_t high = fw_recipe_high_range_default();
    force_ctrl_t before;
    float sp;
#define CHECK_R(label, condition) do { int ok = (condition); \
    printf("Ramp %s | %s\n", label, ok ? "PASS" : "FAIL"); \
    if (!ok) ++failed; } while (0)
    hal_host_reset(); fw_reset_latch(); fw_init();
    CHECK_R("a high FIRMWARE 5 N/s (max 25)", fw_set_recipe(&high) == FW_OK);
    hal_host_set_force_N(0.2f);
    for (tick = 0; tick < 30; ++tick) fw_step_1ms();
    before = *fw_get_force_state();
    sp = before.setpoint_N;
    low.ramp_N_s = 5;
    CHECK_R("a low FIRMWARE 5 N/s rejected (-1)",
        fw_set_recipe(&low) == FW_ERR_RAMP_EXCEEDS_CAPABILITY);
    CHECK_R("a rejection preserves controller state/output",
        !memcmp(&before, fw_get_force_state(), sizeof(before)) &&
        hal_host_get_z_velocity_mm_s() == before.velocity_mm_s && fw_get_mode() == FW_MODE_FIRMWARE);
    fw_step_1ms();
    CHECK_R("a previous high recipe/time continues (5 N/s)",
        fabsf(fw_get_force_state()->setpoint_N - sp - 0.005f) < 1e-6f);
    low.ramp_N_s = FW_FORCE_LOW_RANGE_RAMP_N_S;
    CHECK_R("a low FIRMWARE 1.0 N/s accepted", fw_set_recipe(&low) == FW_OK);
    low.ramp_N_s = 1.01f; /* 경계 시험값: 승인 상한 1 N/s 바로 위. */
    CHECK_R("a low FIRMWARE 1.01 N/s rejected (-1)",
        fw_set_recipe(&low) == FW_ERR_RAMP_EXCEEDS_CAPABILITY);
    hal_host_set_force_N(0.2f);
    fw_step_1ms();
    fw_step_1ms();
    CHECK_R("a previous low recipe continues (1 N/s)",
        fabsf(fw_get_force_state()->setpoint_N - 0.101f) < 1e-7f);
    for (tick = 2; tick < 1200; ++tick) fw_step_1ms();
    CHECK_R("a rejection preserves low target/ramp/spring", fw_get_force_state()->setpoint_N == 1.0f &&
        fabsf(fw_get_force_state()->k_eff - 1.998002f) < 1e-5f);
    low.ramp_N_s = 5; low.mode = FW_MODE_REFERENCE;
    CHECK_R("b low REFERENCE 5 N/s accepted", fw_set_recipe(&low) == FW_OK);
    {
        const golden_case_t g = {.id="low1N-ramp1-noise0", .spring=2, .target=1,
            .ramp=FW_FORCE_LOW_RANGE_RAMP_N_S, .approach=0.02, .period_ms=1, .end_s=9};
        result_t r = simulate_options(&g, FW_MODE_FIRMWARE, 0, 0, 0);
        int original = r.hold_samples && r.overshoot <= 0.06 && r.ss_err <= 0.06;
        int judged = r.settled_samples && r.overshoot <= 0.06 && r.settled_err <= 0.06;
        puts("Ramp c stage-A noise0 | overshoot_N | ss_original_N | ss_13_N | ss_1.4s_N | contact_s | reach_absolute_s | reach_after_contact_s | max_abs_I_Ns | I_max_Ns | saturated_ticks | original | #13");
        printf("low1N-ramp1 | %.12g | %.12g | %.12g | %.12g | %.3f | %.3f | %.3f | %.12g | %.12g | %u | %s | %s\n",
            r.overshoot, r.ss_err, r.settled_err, r.early_err, r.contact, r.reach,
            r.reach-r.contact, r.integral_max, r.i_limit, r.saturated_ticks,
            original ? "PASS" : "FAIL", judged ? "PASS" : "FAIL");
        CHECK_R("c both windows / 1.4 s / I_max / reach / no interlock",
            original && judged && r.early_err <= 0.06 && r.reach >= 0 &&
            !r.interlocked && r.integral_max <= r.i_limit);
    }
#undef CHECK_R
    return failed;
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
    fw_reset_latch();
    fw_init();
    CHECK(fw_set_recipe(&recipe) == FW_OK);
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
    hal_host_set_force_N(1.0f);
    fw_step_1ms();
    CHECK(hal_host_get_z_velocity_mm_s() == velocity);
    CHECK(fw_set_recipe(&recipe) == FW_OK);
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
            if (fw_set_recipe(&recipe) != FW_OK) return 1;
        } else {
            r = simulate(g);
            if (!strncmp(g->id, "control.force_sim.", strlen("control.force_sim."))) {
                printf("Integral: %s | Ki=%.12g | max_abs=%.12g | ramp_max_abs=%.12g | hold_min=%.12g | hold_max=%.12g | hold_last=%.12g | velocity_max_abs=%.12g\n",
                       g->id, (double)fw_get_force_state()->Ki,
                       r.integral_max, r.ramp_integral_max, r.hold_min, r.hold_max,
                       r.hold_last, r.velocity_max);
            }
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
    failures += check_ramp_capability();
    failures += check_firmware();
    return failures ? 1 : 0;
}
