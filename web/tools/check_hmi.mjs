#!/usr/bin/env node
import {readFileSync,existsSync,readdirSync} from 'node:fs';
import {resolve,dirname,relative} from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const root=fileURLToPath(new URL('../../',import.meta.url));
const walk=dir=>readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(resolve(dir,e.name)):[resolve(dir,e.name)]);
const files=[...walk(resolve(root,'web')),...walk(resolve(root,'sim')).filter(f=>!f.includes('/test/'))].filter(f=>f.endsWith('.js')||f.endsWith('.mjs'));
let count=0;
for(const f of files){
  const result=spawnSync(process.execPath,['--check',f],{encoding:'utf8'});assert.equal(result.status,0,`${f}: ${result.stderr}`);
  const code=readFileSync(f,'utf8').replace(/^\s*\/\/.*$/gm,'').replace(/\/\*[\s\S]*?\*\//g,'');
  // Static/dynamic ES imports and browser URL dependencies; bare 'three' is
  // mapped explicitly by web/index.html. Other bare imports must be Node tools.
  const imports=[...code.matchAll(/(?:^\s*(?:import|export)\s+(?:\{[^}]*\}|[\w$*]+(?:\s*,\s*\{[^}]*\})?|\*\s+as\s+\w+)\s+from\s*|^\s*import\s*|\bimport\s*\(\s*|new URL\(\s*)['"]([^'"]+)['"]/gm)].map(m=>m[1]);
  for(const path of imports){
    if(path==='three'){assert.ok(readFileSync(resolve(root,'web/index.html'),'utf8').includes('"three":"./vendor/three/build/three.module.js"'));continue;}
    if(!path.startsWith('.')){assert.ok(path.startsWith('node:')||(f.includes('/tools/')&&path.startsWith('data:')),`${relative(root,f)}: unexpected external import ${path}`);continue;}
    const target=resolve(dirname(f),path);assert.ok(existsSync(target),`${relative(root,f)}: missing ${path}`);count++;
  }
}
const manifest=readFileSync(resolve(root,'web/vendor/README.md'),'utf8');
for(const m of manifest.matchAll(/\| `([^`]+)` \| `([0-9a-f]{64})` \|/g)){
  const bytes=readFileSync(resolve(root,'web/vendor/three',m[1]));assert.equal(createHash('sha256').update(bytes).digest('hex'),m[2],m[1]);
}
for(const html of ['index.html','vision.html','wasm_check.html','cad.html']){
  const code=readFileSync(resolve(root,'web',html),'utf8');
  for(const m of code.matchAll(/(?:src|href)="([^"#]+)"/g)){
    if(/^(https?:|#)/.test(m[1]))continue;
    // Existing provenance links point to source docs, not deployment imports.
    if(html!=='cad.html'&&m[1].startsWith('../docs/'))continue;
    // factory.html is delivered by the parallel stage-9 worktree. Validate it
    // normally as soon as present, without failing this isolated CAD branch.
    if(m[1]==='factory.html'&&!existsSync(resolve(root,'web/factory.html'))){
      console.log(`PENDING: ${html} → factory.html (parallel factory branch)`);continue;
    }
    assert.ok(existsSync(resolve(root,'web',m[1])),`${html}: ${m[1]}`);
  }
}
console.log(`PASS: ${files.length} JS syntax checks, ${count} relative dependencies, HTML assets and vendor SHA256`);
