#!/usr/bin/env node
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {runWasmCheck} from '../js/wasm_check.js';

try {
  if (process.argv.length > 3) throw new Error('Usage: wasm_check_node.mjs [browser-result.json]');
  const wasmBinary = await readFile(new URL('../../firmware/build/controller.wasm', import.meta.url));
  const result = await runWasmCheck({wasmBinary});
  if (process.argv[2]) {
    const browser = JSON.parse(await readFile(process.argv[2], 'utf8'));
    assert.ok(Number.isFinite(browser.elapsed_ms) && browser.elapsed_ms >= 0, 'Invalid browser elapsed_ms');
    const {elapsed_ms: browserTime, ...browserValues} = browser;
    const {elapsed_ms: nodeTime, ...nodeValues} = result;
    assert.deepStrictEqual(browserValues, nodeValues);
    console.error(`PASS: browser == Node (elapsed_ms excluded; browser=${browserTime}, Node=${nodeTime})`);
  }
  console.log(JSON.stringify(result, null, 2));
} catch (error) {
  console.error(error);
  process.exitCode = 1;
}
