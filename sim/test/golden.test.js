import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import {loadController} from '../plant.js';
import {evaluate} from './helpers/evaluate.js';
const read=path=>JSON.parse(readFileSync(new URL(path,import.meta.url),'utf8'));
const golden=read('./golden_vectors.json').vectors,cases=read('./cases.json');
const load=()=>loadController({wasmBinary:readFileSync(new URL('../../firmware/build/controller.wasm',import.meta.url))});
// Approved exception ONLY: firmware HANDOFF §4.1, C controller float precision.
// Pure functions, force_gains, profile and leaf_flexure retain golden tolerances.
const floatPrefixes=['control.force_sim.','control.contact_peak.','control.temp_sim.'];
function compare(e,a,tol,path='',issues=[]) {
  if(Array.isArray(e)||Array.isArray(a)) {
    if(!Array.isArray(e)||!Array.isArray(a)||e.length!==a.length) issues.push(`${path}: shape`);
    else e.forEach((v,i)=>compare(v,a[i],tol,`${path}[${i}]`,issues));
  } else if(typeof e==='number'&&typeof a==='number') {
    const error=Math.abs(a-e),limit=tol(e);
    if(!(Object.is(e,a)||Number.isNaN(e)&&Number.isNaN(a)||Number.isFinite(e)&&Number.isFinite(a)&&error<=limit)) issues.push(`${path}: ref=${e} js=${a} abs_error=${error} rel_error=${e?error/Math.abs(e):Infinity} limit=${limit}`);
  } else if(e!==a) issues.push(`${path}: ${JSON.stringify(e)} != ${JSON.stringify(a)}`);
  return issues;
}
function index(vs) {const m=new Map();for(const v of vs) {assert.ok(!m.has(v.id),`duplicate ${v.id}`);m.set(v.id,v);}return m;}
test('golden 111: independent case manifest, schema and all outputs',async t=>{
  const expected=index(golden),actual=index(cases);assert.equal(expected.size,111);
  assert.deepEqual([...actual.keys()].sort(),[...expected.keys()].sort());
  let strict=0,float=0,failed=0;
  for(const [id,c] of actual) await t.test(id,async()=>{
    try {
      const g=expected.get(id);for(const key of ['model','function','source','inputs']) assert.deepEqual(c[key],g[key],`${id}.${key}`);
      const values=await evaluate(id,Object.fromEntries(Object.entries(c.inputs).map(([k,v])=>[k,v.value])),load);
      assert.deepEqual(Object.keys(values).sort(),Object.keys(g.output).sort(),'output names');
      assert.deepEqual(Object.keys(c.output).sort(),Object.keys(g.output).sort(),'manifest output names');
      let strictIssues=[],issues=[];
      for(const [name,e] of Object.entries(g.output)) {
        assert.equal(c.output[name].unit,e.unit,`${name}.unit`);
        const si=compare(e.value,values[name],ref=>g.tolerance.abs+g.tolerance.rel*Math.abs(ref),name);
        strictIssues.push(...si);
        const exception=floatPrefixes.some(s=>id.startsWith(s));
        // t_contact seconds: 1 ms; force: 1e-4 N; temperature: 1e-3 C.
        const abs=name==='t_contact'?1e-3:id.startsWith('control.temp_sim.')?1e-3:1e-4;
        issues.push(...(exception?compare(e.value,values[name],ref=>Math.max(abs,1e-3*Math.abs(ref)),name):si));
        if(exception) t.diagnostic(`FLOAT ${id}.${name} ref=${e.value} js=${values[name]} abs_error=${Math.abs(values[name]-e.value)} golden_limit=${g.tolerance.abs+g.tolerance.rel*Math.abs(e.value)} golden_pass=${si.length===0}`);
      }
      assert.equal(issues.length,0,issues.join('\n'));
      if(strictIssues.length) float++;else strict++;
    } catch(e) {failed++;throw e;}
  });
  t.diagnostic(`SUMMARY total=111 golden_pass=${strict} float_exception_pass=${float} failures=${failed}`);
});
