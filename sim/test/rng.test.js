import assert from 'node:assert/strict';
import test from 'node:test';
import {makeRng} from '../rng.js';
import {alignOnce} from '../alignment.js';
test('seeded streams replay including Box–Muller spare and alignment',()=>{
  const a=makeRng(3),b=makeRng(3),c=makeRng(4);
  assert.notEqual(a.uniform(),c.uniform());b.uniform();
  for(let i=0;i<100;i++) {assert.equal(a.normal(),b.normal());assert.equal(a.uniform(-30,30),b.uniform(-30,30));}
  assert.deepEqual(alignOnce(a,0.015),alignOnce(b,0.015));
});
test('uniform bounds and Gaussian moments over a fixed statistical sample',()=>{
  const rng=makeRng(42),count=100000;let sum=0,squares=0;
  for(let i=0;i<count;i++) {const u=rng.uniform();assert.ok(u>=0&&u<1);const z=rng.normal();sum+=z;squares+=z*z;}
  assert.ok(Math.abs(sum/count)<0.02);assert.ok(Math.abs(squares/count-1)<0.02);
});
