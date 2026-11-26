// Existing firmware README low-range preset, not new process assumptions or KPIs.
// spring/target/approach/period: original control_sim.py test conditions;
// ramp=1: approved design value (firmware/README.md, 2026-11-25).
export const recipe = Object.freeze({
  spring_N_mm: 2, target_N: 1, ramp_N_s: 1,
  approach_mm_s: 0.02, period_ms: 1, mode: 1,
});
// Fixed measurement reuses target load and the 20 C original test input
// (sim/plant.js; firmware/test/fixed_inputs.csv). No physical plant is simulated.
export const input = Object.freeze({force_N: recipe.target_N, temperature_C: 20});
export const steps = 1000;

// Schema v1: all fields except elapsed_ms are deterministic and compared exactly.
export async function runWasmCheck(options = {}) {
  // From web/js/, this is the page-relative ../firmware/build/controller.js.
  // Import inside the checked operation so module-load failures reach the error UI.
  const {default: createController} = await import('../../firmware/build/controller.js');
  const fw = await createController(options);
  fw._fw_init();
  const accepted = fw._fw_wasm_set_recipe(
    recipe.spring_N_mm, recipe.target_N, recipe.ramp_N_s,
    recipe.approach_mm_s, recipe.period_ms, recipe.mode,
  );
  if (accepted !== 1) throw new Error(`Recipe rejected: ${accepted}`);
  const started = performance.now();
  for (let tick = 0; tick < steps; tick++) {
    fw._fw_step_1ms(input.force_N, input.temperature_C);
  }
  const elapsed_ms = performance.now() - started;
  const final = {
    force_setpoint_N: fw._fw_get_force_setpoint(),
    z_velocity_mm_s: fw._fw_get_z_velocity(),
    heater_power_W: fw._fw_get_heater_power(),
    warning: fw._fw_get_warning(), latched: fw._fw_get_latched(),
    brake: fw._fw_get_brake(), sto: fw._fw_get_sto(),
    mode: fw._fw_get_mode(), phase: fw._fw_get_phase(),
    force_integral_N_s: fw._fw_get_force_integral(),
    temp_integral_C_s: fw._fw_get_temp_integral(),
  };
  if (![elapsed_ms, ...Object.values(final)].every(Number.isFinite)) {
    throw new Error('Non-finite wasm output');
  }
  return {schema_version: 1, steps, recipe, input, final, elapsed_ms};
}

async function showResult() {
  const status = document.getElementById('status');
  const pre = document.getElementById('result');
  try {
    const result = await runWasmCheck();
    const rows = [
      ['실행 스텝', result.steps],
      ['하중 지령 (N)', result.final.force_setpoint_N],
      ['Z 속도 출력 (mm/s)', result.final.z_velocity_mm_s],
      ['히터 출력 (W)', result.final.heater_power_W],
      ['경고 플래그', result.final.warning],
      ['래치 플래그', result.final.latched],
      ['브레이크 플래그', result.final.brake],
      ['STO 플래그', result.final.sto],
      ['실행 시간 (ms)', result.elapsed_ms],
    ];
    for (const [label, value] of rows) {
      const row = document.createElement('tr');
      const heading = document.createElement('th');
      heading.scope = 'row';
      heading.textContent = label;
      const cell = document.createElement('td');
      cell.textContent = String(value);
      row.append(heading, cell);
      document.getElementById('measurements').append(row);
    }
    pre.textContent = JSON.stringify(result, null, 2);
    status.textContent = 'wasm 실행 완료';
    document.body.dataset.wasmCheck = 'ok';
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    pre.textContent = message;
    status.textContent = `wasm 실행 실패: ${message}`;
    document.body.dataset.wasmCheck = 'error';
  }
}

if (typeof document !== 'undefined') void showResult();
