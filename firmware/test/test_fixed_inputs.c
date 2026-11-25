#include <stdio.h>
#include "fw.h"
#include "hal.h"
#include "hal_host.h"
/* 검증 6 가정값: fixed_inputs.csv is an open-loop measurement sequence,
 * not a plant. Exercise two modes, warning/latch/reset, contact and saturation. */
int main(int argc, char **argv)
{
    FILE *in;
    unsigned mode;
    if (argc != 2) return 1;
    in = fopen(argv[1], "r");
    if (!in) return 1;
    puts("mode,step,z_velocity,heater,warning,latched,brake,sto,setpoint,force_integral,temp_integral,phase");
    for (mode = 0; mode < 2; ++mode) {
        unsigned step = 0;
        float f, t;
        int hw, reset;
        char header[80];
        fw_recipe_t r = {2.0f, 1.0f, 5.0f, 0.02f, 1u, (fw_mode_t)mode};
        rewind(in);
        if (!fgets(header, sizeof(header), in)) return 1;
        hal_host_reset();
        fw_reset_latch();
        fw_init();
        if (!fw_set_recipe(&r)) return 1;
        while (fscanf(in, "%f,%f,%d,%d", &f, &t, &hw, &reset) == 4) {
            hal_host_set_force_N(f);
            hal_host_set_temp_C(t);
            hal_host_set_hw_fault(hw);
            /* Reset sees the previous measurement in both HALs: step first,
             * optional reset afterwards, then observe all outputs. */
            fw_step_1ms();
            if (reset) fw_reset_latch();
            const interlock_t *s = fw_get_interlock_state();
            printf("%d,%u,%.9g,%.9g,%d,%d,%d,%d,%.9g,%.9g,%.9g,%d\n",
                fw_get_mode(), step++, (double)hal_host_get_z_velocity_mm_s(),
                (double)hal_host_get_heater_W(), s->warning, s->latched, s->brake, s->sto,
                (double)fw_get_force_state()->setpoint_N,
                (double)fw_get_force_state()->integral_N_s,
                (double)fw_get_temp_state()->integral_C_s,
                fw_get_sequence_state()->phase);
        }
        if (step < 200 || !feof(in)) return 1;
    }
    return fclose(in) ? 1 : 0;
}
