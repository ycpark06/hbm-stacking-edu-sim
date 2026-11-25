#include <math.h>
#include <stdio.h>
#include "fw.h"
#include "fw_config.h"
#include "hal_host.h"
#define CHECK(x) do { if (!(x)) { printf("Safety FAIL line %d: %s\n", __LINE__, #x); ++failed; } } while (0)

static unsigned check_interlocks(void)
{
    const struct { const char *id; float f, t; int hw, warning, latch; } cases[] = {
        {"force53", 53, 20, 0, 1, 0}, {"force56", 56, 20, 0, 1, 1},
        {"temp411", 1, 411, 0, 1, 0}, {"temp421", 1, 421, 0, 1, 1},
        {"hw_fault", 1, 20, 1, 0, 1},
        /* HANDOFF 3.3: inclusive threshold comparisons. */
        {"force52", 52, 20, 0, 1, 0}, {"force55", 55, 20, 0, 1, 1},
        {"temp410", 1, 410, 0, 1, 0}, {"temp420", 1, 420, 0, 1, 1}
    };
    unsigned i, mode, failed = 0, tick;
    puts("Validation 4 | mode | warning | latch | Z_mm_s | heater_W | brake | STO | freeze/persist/reset | result");
    for (mode = 0; mode < 2; ++mode) for (i = 0; i < sizeof(cases)/sizeof(cases[0]); ++i) {
        fw_recipe_t r = {50, 20, 5, 0.02f, 10, (fw_mode_t)mode};
        unsigned before = failed;
        float sp, integral;
        hal_host_reset(); fw_reset_latch(); fw_init();
        CHECK(fw_set_recipe(&r));
        hal_host_set_temp_C(149); hal_host_set_force_N(0.2f);
        fw_step_1ms(); /* both controllers active at tick 0 */
        sp = fw_get_force_state()->setpoint_N;
        integral = fw_get_force_state()->integral_N_s;
        CHECK(hal_host_get_z_velocity_mm_s() != 0);
        CHECK(hal_host_get_heater_W() > 0);
        hal_host_set_force_N(cases[i].f); hal_host_set_temp_C(cases[i].t);
        hal_host_set_hw_fault(cases[i].hw);
        fw_step_1ms(); /* tick 1: must override between divided updates */
        CHECK(fw_get_interlock_state()->warning == cases[i].warning);
        CHECK(fw_get_interlock_state()->latched == cases[i].latch);
        CHECK(hal_host_get_z_velocity_mm_s() == 0);
        CHECK(hal_host_get_brake() == cases[i].latch);
        CHECK(hal_host_get_sto() == cases[i].latch);
        if (cases[i].latch) CHECK(hal_host_get_heater_W() == 0);
        else CHECK(hal_host_get_heater_W() > 0);
        for (tick = 0; tick < 40; ++tick) fw_step_1ms();
        CHECK(fw_get_force_state()->setpoint_N == sp);
        CHECK(fw_get_force_state()->integral_N_s == integral);
        fw_reset_latch(); /* persistent condition must re-latch immediately */
        CHECK(fw_get_interlock_state()->latched == cases[i].latch);
        printf("%s | %s | %d | %d | %.3f | %.3f | %d | %d | ", cases[i].id,
               mode ? "FIRMWARE" : "REFERENCE", fw_get_interlock_state()->warning,
               fw_get_interlock_state()->latched, (double)hal_host_get_z_velocity_mm_s(),
               (double)hal_host_get_heater_W(), hal_host_get_brake(), hal_host_get_sto());
        hal_host_set_force_N(0.2f); hal_host_set_temp_C(149); hal_host_set_hw_fault(0);
        for (tick = 0; tick < 20; ++tick) fw_step_1ms();
        CHECK(!fw_get_interlock_state()->warning);
        CHECK(fw_get_interlock_state()->latched == cases[i].latch);
        if (cases[i].latch) {
            CHECK(hal_host_get_heater_W() == 0 && hal_host_get_z_velocity_mm_s() == 0);
            /* Init/recipe must never provide another latch reset path. */
            fw_init(); CHECK(fw_get_interlock_state()->latched);
            CHECK(fw_set_recipe(&r)); CHECK(fw_get_interlock_state()->latched);
            CHECK(hal_host_get_z_velocity_mm_s() == 0 && hal_host_get_heater_W() == 0);
        } else CHECK(fw_get_force_state()->setpoint_N > sp);
        fw_reset_latch();
        CHECK(!fw_get_interlock_state()->latched);
        CHECK(!hal_host_get_brake() && !hal_host_get_sto());
        for (tick = 0; tick < 20; ++tick) fw_step_1ms();
        CHECK(hal_host_get_heater_W() > 0);
        CHECK(hal_host_get_z_velocity_mm_s() != 0);
        printf("checked | %s\n", failed == before ? "PASS" : "FAIL");
    }
    return failed;
}

static unsigned check_sequence(void)
{
    unsigned i, failed = 0;
    int saw_ramp = 0, saw_hold = 0, saw_release = 0, saw_retract = 0;
    double z = -0.02, cmd = z, previous_sp = 1;
    /* 설계값 테스트: low 1 N, 원본 dt=10 us, servo=0.8 ms, noise=0.
     * 6 s 유지 후 호출자가 해제 요청; 12 s 안에 무하중/상승/정지 확인. */
    fw_recipe_t r = {2, 1, 5, 0.02f, 1, FW_MODE_FIRMWARE};
    hal_host_reset(); fw_reset_latch(); fw_init(); CHECK(fw_set_recipe(&r));
    CHECK(fw_get_sequence_state()->phase == FW_SEQ_APPROACH);
    for (i = 0; i < 1200000; ++i) {
        double f = fmax(0, (1.0/(1.0/2 + 1.0/2000)) * z);
        if (i % 100 == 0) {
            fw_sequence_phase_t phase;
            if (i == 600000) fw_release();
            hal_host_set_force_N((float)f); hal_host_set_temp_C(20);
            fw_step_1ms();
            phase = fw_get_sequence_state()->phase;
            saw_ramp |= phase == FW_SEQ_RAMP;
            saw_hold |= phase == FW_SEQ_HOLD;
            saw_release |= phase == FW_SEQ_RELEASE;
            saw_retract |= phase == FW_SEQ_RETRACT;
            if (phase == FW_SEQ_RELEASE) {
                CHECK(fw_get_force_state()->setpoint_N <= previous_sp);
                previous_sp = fw_get_force_state()->setpoint_N;
            }
            if (phase == FW_SEQ_RETRACT) {
                CHECK(fw_get_force_state()->setpoint_N == 0);
                CHECK(f <= FW_CONTACT_FORCE_N);
            }
        }
        cmd += hal_host_get_z_velocity_mm_s() * 1e-5;
        z += (cmd-z) * 1e-5 / 0.0008;
    }
    CHECK(saw_ramp && saw_hold && saw_release && saw_retract);
    CHECK(fw_get_sequence_state()->phase == FW_SEQ_DONE);
    CHECK(hal_host_get_z_velocity_mm_s() == 0 && z < 0);
    printf("Sequence approach/ramp/hold/release/retract/done | %s\n", failed ? "FAIL" : "PASS");
    return failed;
}

static unsigned check_antiwindup_order(void)
{
    unsigned failed = 0;
    fw_recipe_t r = {50, 20, 5, 0.02f, 1, FW_MODE_FIRMWARE};
    force_ctrl_t c;
    float e, delta;
    force_ctrl_init(&c, &r);
    /* Inclusive +v_max with zero starting integral; exact float boundary. */
    e = FW_FORCE_V_MAX_MM_S / c.Kp;
    delta = e * FW_TICK_S;
    c.integral_N_s = -delta;
    force_ctrl_track(&c, &r, 0, e);
    CHECK(c.velocity_mm_s == FW_FORCE_V_MAX_MM_S);
    CHECK(c.integral_N_s == -delta);
    c.integral_N_s = delta;
    force_ctrl_track(&c, &r, e, 0);
    CHECK(c.velocity_mm_s == -FW_FORCE_V_MAX_MM_S);
    CHECK(c.integral_N_s == delta);
    /* Clip before rollback: expected result differs from old-I restoration. */
    c.integral_N_s = c.integral_limit_N_s;
    e = 0.1f; delta = e * FW_TICK_S;
    force_ctrl_track(&c, &r, 0, e);
    CHECK(c.integral_N_s == c.integral_limit_N_s - delta);
    CHECK(c.velocity_mm_s == FW_FORCE_V_MAX_MM_S);
    r.mode = FW_MODE_REFERENCE;
    c.integral_N_s = c.integral_limit_N_s;
    force_ctrl_track(&c, &r, 0, e);
    CHECK(c.integral_N_s > c.integral_limit_N_s);
    CHECK(c.velocity_mm_s > FW_FORCE_V_MAX_MM_S);
    CHECK(!fw_set_recipe(&(fw_recipe_t){50, 20, 5, 0.02f, 1, (fw_mode_t)2}));
    printf("Force clip/rollback order and mode | %s\n", failed ? "FAIL" : "PASS");
    return failed;
}
int main(void)
{
    unsigned failed = check_interlocks();
    failed += check_sequence();
    failed += check_antiwindup_order();
    return failed ? 1 : 0;
}
