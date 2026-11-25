import fs from 'node:fs';
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
    if (!m._fw_wasm_set_recipe(2, 1, 5, 0.02, 1, mode)) throw new Error('Recipe rejected');
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
  console.log('Recorded build/fixed_pc.csv and build/fixed_wasm.csv (no JS plant).');
} catch (err) {
  console.error('Validation 6: FAIL', err.message);
  process.exitCode=1;
}
