import fs from 'node:fs';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import createController from '../build/controller.js';

try {
  const root = fileURLToPath(new URL('../', import.meta.url));
  const inputPath = root + 'test/fixed_inputs.csv';
  const inputs = fs.readFileSync(inputPath, 'utf8').trim().split('\n').slice(1)
    .map(line => line.split(',').map(Number));
  if (inputs.length < 200) throw new Error('Need >=200 fixed inputs');
  const pcCSV = execFileSync(root + 'build/test_fixed_inputs', [inputPath], {encoding:'utf8'});
  fs.writeFileSync(root + 'build/fixed_pc.csv', pcCSV);
  const lines = pcCSV.trim().split('\n');
  const pc = lines.slice(1).map(line => line.split(',').map(Number));
  const wasm = [];
  let worst = 0;
  for (let mode = 0; mode < 2; ++mode) {
    const m = await createController({wasmBinary: fs.readFileSync(root + 'build/controller.wasm')});
    m._fw_init();
    if (mode === 1) { if (m._fw_wasm_set_recipe(2, 1, 5, 0.02, 1, mode) !== -1) throw new Error('Ramp rejection code mismatch'); console.log('Ramp d wasm low FIRMWARE 5 N/s: -1 PASS'); }
    // 승인된 설계값 1 N/s, PC와 동일한 유효 레시피 (#13, 2026-11-25).
    if (m._fw_wasm_set_recipe(2, 1, 1, 0.02, 1, mode) !== 1) throw new Error('Recipe rejected');
    for (const [step, [f,t,hw,reset]] of inputs.entries()) {
      m._fw_set_hw_fault(hw);
      m._fw_step_1ms(f,t);
      if (reset) m._fw_reset_latch();
      wasm.push([m._fw_get_mode(),step,m._fw_get_z_velocity(),m._fw_get_heater_power(),
        m._fw_get_warning(),m._fw_get_latched(),m._fw_get_brake(),m._fw_get_sto(),
        m._fw_get_force_setpoint(),m._fw_get_force_integral(),m._fw_get_temp_integral(),m._fw_get_phase()]);
    }
  }
  fs.writeFileSync(root + 'build/fixed_wasm.csv', lines[0]+'\n'+wasm.map(r=>r.join(',')).join('\n')+'\n');
  if (pc.length !== wasm.length) throw new Error('Row count mismatch');
  for (let i=0; i<pc.length; ++i) for (let j=0; j<pc[i].length; ++j) {
    const a=pc[i][j], b=wasm[i][j];
    // HANDOFF §4.1 / requested validation 6: max(relative 1e-3, absolute 1e-4).
    const limit=Math.max(1e-4,Math.abs(a)*1e-3), err=Math.abs(a-b);
    if (!Number.isFinite(a) || !Number.isFinite(b) || err>limit)
      throw new Error(`row ${i}, column ${j}: PC=${a}, wasm=${b}, limit=${limit}`);
    worst=Math.max(worst,err);
  }
  console.log(`Validation 6: PASS (${wasm.length} rows, ${wasm.length*pc[0].length} values, max_abs_error=${worst.toExponential(6)}; rel=1e-3/abs=1e-4)`);
  for (let mode = 0; mode < 2; ++mode) {
    const m = await createController({wasmBinary: fs.readFileSync(root + 'build/controller.wasm')});
    const step = () => {
      m._fw_step_1ms(0, 149); // Test input: existing initial profile minus 1 C.
      assert.ok(m._fw_get_heater_power() === 0 || m._fw_get_reflow_heater_power() === 0);
    };
    const init = () => {
      m._fw_init();
      assert.equal(m._fw_wasm_set_recipe(50, 20, 5, 0.02, 1, mode), 1);
    };
    init();
    step();
    assert.ok(m._fw_get_heater_power() > 0);
    m._fw_request_reflow_heater_W(150); // Design rating, user decision 2026-11-28.
    step();
    assert.equal(m._fw_get_reflow_heater_power(), 0);
    assert.equal(m._fw_get_dual_heater_blocked(), 1);
    assert.equal(m._fw_get_warning(), 0);
    assert.equal(m._fw_get_latched(), 0);
    m._fw_set_head_heater_enabled(0);
    step(); assert.equal(m._fw_get_reflow_heater_power(), 0);
    step(); assert.equal(m._fw_get_reflow_heater_power(), 150);
    assert.equal(m._fw_get_dual_heater_blocked(), 0);
    m._fw_set_head_heater_enabled(1);
    step(); assert.equal(m._fw_get_heater_power(), 0);
    assert.equal(m._fw_get_dual_heater_blocked(), 1);
    m._fw_request_reflow_heater_W(0);
    step(); assert.equal(m._fw_get_heater_power(), 0);
    step(); assert.ok(m._fw_get_heater_power() > 0);
    for (const reverse of [false, true]) {
      init();
      if (reverse) m._fw_request_reflow_heater_W(150);
      m._fw_set_head_heater_enabled(1);
      if (!reverse) m._fw_request_reflow_heater_W(150);
      step();
      assert.ok(m._fw_get_heater_power() > 0);
      assert.equal(m._fw_get_reflow_heater_power(), 0);
      assert.equal(m._fw_get_dual_heater_blocked(), 1);
    }
    init(); m._fw_set_head_heater_enabled(0);
    m._fw_request_reflow_heater_W(300); step();
    assert.equal(m._fw_get_reflow_heater_power(), 150);
    for (const invalid of [-1, NaN]) {
      m._fw_request_reflow_heater_W(invalid); step();
      assert.equal(m._fw_get_reflow_heater_power(), 0);
    }
    for (const [f, t, hw] of [[55, 149, 0], [0, 420, 0], [0, 149, 1]]) {
      for (const headOwner of [false, true]) {
        m._fw_set_hw_fault(0); m._fw_step_1ms(0, 149); m._fw_reset_latch(); init();
        m._fw_set_head_heater_enabled(headOwner ? 1 : 0);
        m._fw_request_reflow_heater_W(headOwner ? 0 : 150); step();
        assert.ok(m._fw_get_heater_power() > 0 || m._fw_get_reflow_heater_power() > 0);
        m._fw_set_hw_fault(hw); m._fw_step_1ms(f, t);
        assert.equal(m._fw_get_latched(), 1);
        assert.equal(m._fw_get_heater_power(), 0);
        assert.equal(m._fw_get_reflow_heater_power(), 0);
        assert.equal(m._fw_get_dual_heater_blocked(), 0);
        m._fw_reset_latch();
        assert.equal(m._fw_get_latched(), 1);
      }
    }
  }
  console.log('Dual heater wasm interlock: PASS (both modes, orders, idle tie, off tick, clamp, latches)');
  console.log('Recorded build/fixed_pc.csv and build/fixed_wasm.csv (no JS plant).');
} catch (err) {
  console.error('Validation 6: FAIL', err.message);
  process.exitCode=1;
}
