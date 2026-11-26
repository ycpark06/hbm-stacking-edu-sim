import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {render,detect,measure,flatten,affineFit,alignLayer,visionOptions} from '../vision.js';
import {makeRng} from '../rng.js';
import {evaluate} from './helpers/evaluate.js';
const params=JSON.parse(readFileSync(new URL('../params.json',import.meta.url)));
const c=visionOptions(params);
test('production measurement preserves every golden output within abs 2e-4 px',async t=>{
  const vectors=JSON.parse(readFileSync(new URL('./golden_vectors.json',import.meta.url))).vectors;
  for(const g of vectors.filter(v=>v.id.startsWith('alignment.measure.'))){
    const q=Object.fromEntries(Object.entries(g.inputs).map(([k,v])=>[k,v.value]));
    const a=await evaluate(g.id,q);
    for(const [k,v] of Object.entries(g.output)){const e=Math.abs(a[k]-v.value);t.diagnostic(`${g.id}.${k}: abs_error=${e} px (limit 0.0002)`);assert.ok(e<=2e-4);}
  }
});
test('known integer/subpixel shifts: bounded pixel-lock bias, no search-edge wrap',()=>{
  // Midterm 9.4: RMS 0.0086 px is an accuracy statistic, not 2e-4 golden tolerance.
  for(const [x,y] of [[0,0],[1,-2],[.37,-.21],[-1.2,2.4]]){
    const [mx,my]=measure(render(x,y));assert.ok(Math.abs(mx-x)<.02);assert.ok(Math.abs(my-y)<.02);
  }
  assert.throws(()=>detect(render(24,0)),/boundary/);
  assert.throws(()=>detect(Array.from({length:128},()=>Array(128).fill(0))),/contrast/);
});
test('blank-reference and border-fit flattening reduce multiplicative gradient bias',t=>{
  const x=.37,y=-.21,im=render(x,y,{blur:2.5,bright:120,dark:70});
  // Original robust experiment ±10% illumination across X; noiseless isolates bias.
  const blank=im.map((r,j)=>r.map((_,i)=>120*(1+.2*(i/c.N-.5))));
  const tilted=im.map((r,j)=>r.map((v,i)=>v*blank[j][i]/120));
  const error=a=>Math.hypot(...measure(a).map((v,i)=>v-[x,y][i]));
  const before=error(tilted),after=error(flatten(tilted,blank)),fit=error(flatten(tilted));
  t.diagnostic(`gradient error px raw=${before}, reference=${after}, border=${fit}`);
  assert.ok(after<before);assert.ok(fit<before);
});
test('noiseless affine calibration recovers rotation, shear, scale and translation',()=>{
  const A=[[1.7,-.02],[.03,1.73]],b=[12,-7],P=[[-100,-80],[100,-80],[100,80],[-100,80],[0,0]];
  const S=P.map(([x,y])=>A.map((r,i)=>r[0]*x+r[1]*y+b[i])),f=affineFit(P,S);
  f.A.flat().forEach((v,i)=>assert.ok(Math.abs(v-A.flat()[i])<1e-12));f.b.forEach((v,i)=>assert.ok(Math.abs(v-b[i])<1e-12));
});
test('image-driven loop converges reproducibly; seeded MC reports residual 3sigma, no fit to 0.09 um',t=>{
  const opts={params,true_dx_um:12.37,true_dy_um:-9.21,true_theta_mrad:2,rng:makeRng(489)};
  const r=alignLayer(opts),repeat=alignLayer({...opts,rng:makeRng(489)});
  assert.deepEqual(r,repeat);assert.ok(r.converged);assert.ok(r.iterations>0);
  assert.ok(r.history[0].fiducials[0].upper.data instanceof Float32Array);
  assert.ok(Math.hypot(r.residual.dx_um,r.residual.dy_um)<Math.hypot(opts.true_dx_um,opts.true_dy_um));
  // 32 image-driven trials (256+ image detections), fixed seed; reports sampling
  // uncertainty ~13% for sigma. Smaller than original statistical MC's 5000.
  const samples=32,rng=makeRng(params.alignment.mc_seed.value),values=[],counts=[];
  for(let i=0;i<samples;i++){
    const trial=alignLayer({params,rng,true_dx_um:rng.uniform(-c.initial_um,c.initial_um),true_dy_um:rng.uniform(-c.initial_um,c.initial_um),true_theta_mrad:rng.uniform(-c.initial_theta_mrad,c.initial_theta_mrad)});
    assert.ok(trial.converged,`trial ${i}`);values.push([trial.residual.dx_um,trial.residual.dy_um]);counts.push(trial.iterations);
  }
  const sigma=[0,1].map(j=>{const mean=values.reduce((s,r)=>s+r[j],0)/samples;return Math.sqrt(values.reduce((s,r)=>s+(r[j]-mean)**2,0)/(samples-1));});
  t.diagnostic(`image-driven MC seed=${params.alignment.mc_seed.value} N=${samples}; residual 3sigma XY=${sigma.map(s=>3*s)} um; max=${3*Math.max(...sigma)} um; midterm result=0.09 um (comparison only); sigma relative SE=${1/Math.sqrt(2*(samples-1))}; correction counts=${JSON.stringify(counts)}`);
});
