import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {PARTS,FOOTPRINT_LIMIT} from '../../web/js/cad_data.js';
import {GROUPS,groupParts,dimensionText,materialText} from '../../web/js/cad_parts.js';
const root=fileURLToPath(new URL('../../',import.meta.url));
const read=path=>readFileSync(new URL(`../../${path}`,import.meta.url));

test('CAD catalog retains every source dimension, material, group and classification',()=>{
  // Detect stale display snapshots when the single geometry source changes.
  // Pure stdlib import: no Fusion, geometry regeneration or repository writes.
  const result=spawnSync('python3',['-B','-c',`
import importlib.util,json
s=importlib.util.spec_from_file_location('cad_source','cad/stacker/spec_stacker.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
print(json.dumps({'parts':[{'type':t,'name':n,'group':g,'material':mat,'params':list(p),'kind':m.PART_SOURCES[n]['kind']} for t,n,g,mat,p in m.P],'limit':m.VALUES['limit.footprint']}))
`],{cwd:root,encoding:'utf8'});
  assert.equal(result.status,0,result.stderr);
  const source=JSON.parse(result.stdout);
  assert.deepEqual(PARTS.map(({type,name,group,material,params,kind})=>({type,name,group,material,params,kind})),source.parts);
  assert.deepEqual(FOOTPRINT_LIMIT,source.limit);
  for(const part of PARTS){
    assert.ok(part.source.includes(`PART_SOURCES["${part.name}"].dimensions_mm`));
    assert.ok(part.materialSource.includes(`PART_SOURCES["${part.name}"].material`));
  }
});

test('GLB groups, STL downloads, summary components and catalog agree',()=>{
  const summary=JSON.parse(read('cad/stacker/out/summary.json'));
  const glb=read('cad/web/hbm_stacker.glb');
  assert.equal(glb.toString('ascii',0,4),'glTF');
  const scene=JSON.parse(glb.toString('utf8',20,20+glb.readUInt32LE(12)));
  const names=scene.nodes.map(node=>node.name).sort();
  assert.deepEqual(Object.keys(GROUPS).sort(),names);
  assert.deepEqual([...summary.mesh_groups].sort(),names);
  assert.equal(PARTS.length,summary.parts.length);
  for(const id of names){
    assert.ok(existsSync(new URL(`../../cad/stacker/out/mesh/${id}.stl`,import.meta.url)));
    assert.deepEqual(groupParts(id).map(p=>[p.name,p.material]),summary.parts.filter(p=>p[0]===id).map(p=>p.slice(1,3)));
  }
});

test('cylindrical dimensions use endpoint differences and diameters, with explicit material grades',()=>{
  const window=PARTS.find(p=>p.name==='Quartz_Window');
  assert.equal(dimensionText(window),`외경 Ø${window.params[4]*2} × 높이 ${window.params[3]-window.params[2]} mm`);
  const tube=PARTS.find(p=>p.type==='tube');
  assert.ok(dimensionText(tube).includes(`내경 Ø${tube.params[5]*2}`));
  assert.match(materialText(window),/fused silica/);
  assert.match(materialText(PARTS.find(p=>p.name==='Mold_Block')),/SUS304/);
});
