#!/usr/bin/env node
// Exercise the actual browser Worker message handler using a Node transport.
// No DOM/WebGL substitution or browser pass is claimed by this check.
import {Worker} from 'node:worker_threads';
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const params=JSON.parse(readFileSync(new URL('../../sim/params.json',import.meta.url)));
const workerURL=new URL('../js/worker.js',import.meta.url).href;
const shim=`import {parentPort} from 'node:worker_threads';
globalThis.self={postMessage:message=>parentPort.postMessage(message)};
await import(${JSON.stringify(workerURL)});
parentPort.on('message',data=>self.onmessage({data}));`;
for(const scenario of ['S1','S2','S3','S4','S5']) {
  const w=new Worker(new URL('data:text/javascript,'+encodeURIComponent(shim)));
  try {
    await new Promise((resolve,reject)=>{
      const timeout=setTimeout(()=>reject(Error(`${scenario}: timeout`)),60000);
      let gotResults=false,gotSil=false,progress=0;
      w.on('error',reject);
      w.on('message',m=>{
        try {
          if(m.type==='error')throw Error(m.message);
          if(m.type==='results'){
            assert.ok(m.results.length>=2);gotResults=true;
            for(const r of m.results){assert.ok(r.thermal.history.length);assert.ok(r.warpage.history.length);}
            if(scenario==='S1'){
              assert.equal(m.results.length,3);
              assert.deepEqual(m.results[0].alarms.map(a=>a.layer),[1,2]);
              assert.equal(m.results[1].alarms.length,0);
            }
            if(scenario==='S3')assert.ok(m.results.every(r=>r.model_limit&&r.warpage.thickness_half_ratio>1));
            if(scenario==='S5')assert.equal(m.results.length,12);
          }
          if(m.type==='sil'){assert.ok(m.sil.F.length);gotSil=true;}
          if(m.type==='progress'){assert.ok(m.layer>=1);assert.ok(m.recipe.layers>=m.layer);progress++;}
          if(m.type==='done'){assert.ok(gotResults&&gotSil&&progress>0);clearTimeout(timeout);console.log(`PASS ${scenario}: results, full histories, wasm SIL, ${progress} progress events, done`);resolve();}
        }catch(error){clearTimeout(timeout);reject(error);}
      });
      w.postMessage({id:scenario,scenario,params});
    });
  }finally{await w.terminate();}
}
