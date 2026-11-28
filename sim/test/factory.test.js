import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {MODES,CAMERA_IDS,filmSectionFrame,readFactoryData,buildStages,sampleStage,cameraFitDistance,explodedAmount,filmSqueezeAt,heatGlow,layerHeat,alignmentOffsetRatio,DISPLAY} from '../../web/js/factory_sequence.js';
const read=path=>JSON.parse(readFileSync(new URL(path,import.meta.url),'utf8'));
const p=read('../params.json'),r=read('./stage4_results.json'),data=readFactoryData(p,r);
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-8,`${a} != ${b}`);
test('heat glow clamps ambient/peak boundaries and increases monotonically',()=>{
  const ambient=p.thermal_stack.ambient_temp.value,peak=p.reflow.peak_temp.value,span=peak-ambient;
  assert.equal(heatGlow(ambient-span,ambient,peak),0);
  assert.equal(heatGlow(ambient,ambient,peak),0);
  assert.equal(heatGlow(peak,ambient,peak),1);
  assert.equal(heatGlow(peak+span,ambient,peak),1);
  let previous=0;
  for(let i=0;i<=20;i++){
    const u=i/20,glow=heatGlow(ambient+span*u,ambient,peak);
    close(glow,u);assert.ok(glow>=previous);previous=glow;
  }
});
test('heating follows displayed temperature, process scope and solder liquidus on stage jumps',()=>{
  const ambient=p.thermal_stack.ambient_temp.value,peak=p.reflow.peak_temp.value;
  const liquidus=p.solder.liquidus_snag.value;
  for(const mode of MODES)for(const s of buildStages(data,mode)){
    for(const u of [0,.5,1]){
      const v=sampleStage(data,s,u);
      for(let i=0;i<data.layers;i++){
        const h=layerHeat(data,s,v,i);
        const active=mode==='MR-MUF'?s.kind==='reflow':
          ['ramp','hold'].includes(s.kind)&&[s.layer-1,s.layer-2].includes(i);
        close(h.glow,active?heatGlow(v.temp,ambient,peak):0);
        assert.equal(h.molten,active&&i>0&&v.temp>=liquidus);
      }
    }
  }
  for(const mode of MODES){
    const s=buildStages(data,mode).find(s=>mode==='MR-MUF'?s.kind==='reflow':s.kind==='hold'&&s.layer===2);
    assert.equal(layerHeat(data,s,{temp:ambient},1).molten,false);
    assert.equal(layerHeat(data,s,{temp:liquidus},1).molten,true);
    assert.equal(layerHeat(data,s,{temp:peak},1).molten,true);
    assert.equal(layerHeat(data,s,{temp:peak},0).molten,false);
  }
});
test('S1/S4 recipe, S4 occupancy and S5 inlet match original JSON',()=>{
  const scenario=id=>r.representative.find(s=>s.id===id);
  assert.equal(data.layers,scenario('S1').recipes[0].layers);
  assert.deepEqual(data.tc,scenario('S4').results[0]);
  assert.equal(data.fill.recipe.inlet_pressure_MPa,p.muf.applied_pressure.value);
  assert.equal(data.fill.recipe.gap_um,p.geometry.interlayer_gap.value);
  const fill=scenario('S5').results.find(s=>s.recipe.gap_um===p.geometry.interlayer_gap.value&&s.recipe.inlet_pressure_MPa===p.muf.applied_pressure.value);
  assert.equal(data.fill.muf.fill_time_s,fill.muf.fill_time_s);
});
for(const mode of MODES)test(`${mode}: complete, ordered per-layer flow; screen budget independent of real time`,()=>{
  const stages=buildStages(data,mode),tc=mode===MODES[0];
  const flow=tc?['supply','align','pickup','ncf','approach','ramp','hold','cool','rise']:['supply','align','pickup','approach','tack','rise'];
  assert.deepEqual(stages.slice(0,2).map(s=>s.kind),['overview','exploded']);
  for(let layer=1;layer<=data.layers;layer++)assert.deepEqual(stages.filter(s=>s.layer===layer&&!['to-reflow','reflow','to-mold','dispense','fill','mold-cure','postcure','compare'].includes(s.kind)).map(s=>s.kind),flow);
  assert.equal(stages.at(-1).id,'compare');assert.equal(new Set(stages.map(s=>s.id)).size,stages.length);
  assert.ok(stages.every(s=>s.mode===mode&&s.duration_s>0&&s.real_duration_s>=0));
  close(stages.reduce((a,s)=>a+s.duration_s,0),90);
  const longer=buildStages(data,mode,120);close(longer.reduce((a,s)=>a+s.duration_s,0),120);
  assert.deepEqual(stages.map(s=>s.real_duration_s),longer.map(s=>s.real_duration_s));
  const layerTime=stages.filter(s=>!['overview','exploded','compare','to-reflow','reflow','to-mold','dispense','fill','mold-cure','postcure'].includes(s.kind)).reduce((a,s)=>a+s.real_duration_s,0);
  close(layerTime,(tc?data.tc:data.mr).cycle.bonder_s);
  assert.equal(stages.some(s=>s.kind==='reflow'),!tc);
});
test('TC force/head/ramp/hold/cooling and N−1 are taken from params',()=>{
  const s=buildStages(data,MODES[0]),get=kind=>s.find(s=>s.kind===kind);
  close(get('ramp').real_duration_s,(p.tcncf_process.head_setpoint.value-p.tcncf_process.stage_temp.value)/p.tcncf_process.ramp_rate.equipment_value);
  assert.equal(get('hold').real_duration_s,p.tcncf_process.hold_time.value);
  assert.equal(get('cool').real_duration_s,p.tcncf_process.cool_time.value);
  assert.equal(sampleStage(data,get('hold'),.5).force,p.tcncf_process.bond_force.value);
  assert.equal(sampleStage(data,get('hold'),.5).temp,p.tcncf_process.head_setpoint.value);
  assert.equal(sampleStage(data,get('ramp'),0).temp,p.tcncf_process.stage_temp.value);
  assert.equal(sampleStage(data,get('cool'),1).temp,p.tcncf_process.stage_temp.value);
  assert.equal(sampleStage(data,s.at(-1),1).reheats,data.layers-1);
  assert.equal(sampleStage(data,s.at(-1),1).count,data.layers);
});
test('MR transfer → complete profile → mold → fill → two cure stages',()=>{
  const stages=buildStages(data,MODES[1]),post=stages.slice(stages.findIndex(s=>s.kind==='to-reflow'));
  assert.deepEqual(post.map(s=>s.kind),['to-reflow',...data.profile.map(()=>'reflow'),'to-mold','dispense','fill','mold-cure','postcure','compare']);
  const profile=stages.filter(s=>s.kind==='reflow');
  close(profile.reduce((a,s)=>a+s.real_duration_s,0),data.mr.cycle.breakdown.once.reflow_s);
  const temps=profile.flatMap(s=>[sampleStage(data,s,0).temp,sampleStage(data,s,1).temp]);
  close(Math.max(...temps),p.reflow.peak_temp.value);
  assert.equal(stages.find(s=>s.kind==='fill').real_duration_s,data.fill.muf.fill_time_s);
  const cure=stages.find(s=>s.kind==='postcure');assert.equal(cure.real_duration_s,p.muf.cure_time.value*3600);assert.equal(sampleStage(data,cure,.5).temp,p.muf.cure_temp.value);
  const tack=stages.find(s=>s.kind==='tack');assert.equal(sampleStage(data,tack,.5).force,p.mrmuf_process.tack_force.value);assert.equal(sampleStage(data,tack,.5).temp,p.mrmuf_process.tack_temp.value);
});
test('invalid display settings and modes rejected',()=>{
  assert.throws(()=>buildStages(data,'wrong'),RangeError);
  for(const time of [0,NaN,59,121])assert.throws(()=>buildStages(data,MODES[0],time),RangeError);
});

// No WebGL/browser required: project actual GLB bounding-box corners with three.js.
import {Box3,Vector3,Matrix4,Quaternion,PerspectiveCamera} from '../../web/vendor/three/build/three.module.js';
test('camera fitting keeps GLB and head bounds inside portrait/wide perspective frusta',()=>{
  const bytes=readFileSync(new URL('../../cad/web/hbm_stacker.glb',import.meta.url));
  const gltf=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString());
  const bounds=gltf.nodes.filter(n=>n.mesh!==undefined).map(n=>{
    const box=new Box3();
    for(const primitive of gltf.meshes[n.mesh].primitives){const a=gltf.accessors[primitive.attributes.POSITION];box.union(new Box3(new Vector3(...a.min),new Vector3(...a.max)));}
    const matrix=n.matrix?new Matrix4().fromArray(n.matrix):new Matrix4().compose(new Vector3(...(n.translation||[0,0,0])),new Quaternion(...(n.rotation||[0,0,0,1])),new Vector3(...(n.scale||[1,1,1])));
    return {name:n.name,box:box.applyMatrix4(matrix)};
  });
  const all=new Box3(),head=new Box3();for(const n of bounds){all.union(n.box);if(['head','z_carriage','stack_chuck'].includes(n.name))head.union(n.box);}
  for(const box of [all,head,new Box3(new Vector3(-1,-1,-1),new Vector3(1,1,1))])for(const aspect of [0.25,9/16,1,16/9,4])for(const direction of [[14,7,17],[3,2.3,5],[4,1.5,5],DISPLAY.filmSection.direction]){
    const center=box.getCenter(new Vector3()),radius=box.getSize(new Vector3()).length()/2;
    const distance=cameraFitDistance(radius,38,aspect),camera=new PerspectiveCamera(38,aspect,Math.max(.001,distance-radius*1.5),distance+radius*3);
    camera.position.copy(center).addScaledVector(new Vector3(...direction).normalize(),distance);camera.lookAt(center);camera.updateMatrixWorld(true);
    for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z]){
      const projected=new Vector3(x,y,z).project(camera);
      assert.ok(Math.abs(projected.x)<1&&Math.abs(projected.y)<1&&Math.abs(projected.z)<1,`clipped at aspect ${aspect}`);
    }
  }
});
test('exploded display opens fully at midpoint and smoothly returns before next stage',()=>{
  close(explodedAmount(0),0);close(explodedAmount(.5),1);close(explodedAmount(1),0);
  assert.ok(explodedAmount(.25)>.4);close(explodedAmount(.25),explodedAmount(.75));
  assert.ok(explodedAmount(.001)<.0001);assert.ok(explodedAmount(.999)<.0001);
});

test('film squeeze display is monotone, continuous and retained after bonding',()=>{
  for(const kind of ['ncf','approach','supply'])for(const u of [0,.5,1])
    assert.deepEqual(filmSqueezeAt(kind,u),{thickness:1,spread:1});
  const samples=['ramp','hold'].flatMap(kind=>Array.from({length:21},(_,i)=>filmSqueezeAt(kind,i/20)));
  for(let i=1;i<samples.length;i++){
    assert.ok(samples[i].thickness<=samples[i-1].thickness);
    assert.ok(samples[i].spread>=samples[i-1].spread);
  }
  assert.deepEqual(filmSqueezeAt('ramp',1),filmSqueezeAt('hold',0));
  assert.deepEqual(filmSqueezeAt('ramp',-1),{thickness:1,spread:1});
  for(const kind of ['hold','cool','rise','compare'])
    assert.deepEqual(filmSqueezeAt(kind,1),DISPLAY.filmSqueeze);
  for(const kind of ['cool','rise','compare'])for(const u of [0,.5,1])
    assert.deepEqual(filmSqueezeAt(kind,u),filmSqueezeAt('hold',1));
});

test('camera 4 follows current front edge with a thickness-based display frame',()=>{
  assert.deepEqual(CAMERA_IDS,[1,2,3,4]);
  const w=p.geometry.die_size.value/1000,h=p.geometry.die_thickness.value/1e6;
  const g=p.geometry.interlayer_gap.value/1e6*DISPLAY.gapMagnification;
  assert.deepEqual(filmSectionFrame(w,h,g,0),filmSectionFrame(w,h,g,1));
  for(let layer=1;layer<=data.layers;layer++){
    const offset=(layer-1)*w*.009,frame=filmSectionFrame(w,h,g,layer,offset);
    close(frame.center[0],offset);close(frame.center[2],w/2);
    close(frame.center[1],(layer-1)*(h+g)-g/2);
    assert.ok(frame.size[1]>=h+g&&frame.size[1]<w/2);
    // Both top of current die and upper face of the lower die fit vertically.
    assert.ok(frame.size[1]/2>=h+g/2);
    assert.ok(w*(DISPLAY.filmSqueeze.spread-1)/2<frame.size[2]/2);
  }
  const app=readFileSync(new URL('../../web/js/factory_app.js',import.meta.url),'utf8');
  const viewer=readFileSync(new URL('../../web/js/factory_viewer.js',import.meta.url),'utf8');
  assert.match(app,/CAMERA_IDS.includes\(Number\(k\)\)/);
  assert.match(viewer,/CAMERA_IDS.includes\(next\)/);
});


test('alignment display decreases without reaching zero and retains residual on direct/reverse seeks',()=>{
  const stages=buildStages(data,'MR-MUF'),profile=stages.filter(s=>s.kind==='reflow');
  let previous=1;
  for(const stage of profile){
    for(const u of [0,.25,.5,.75,1]){
      const ratio=alignmentOffsetRatio(stage,u,profile.length);
      assert.ok(ratio<=previous&&ratio>=DISPLAY.alignmentResidual&&ratio>0);
      previous=ratio;
    }
    if(stage.segment>0)close(alignmentOffsetRatio(stage,0,profile.length),alignmentOffsetRatio(profile[stage.segment-1],1,profile.length));
  }
  close(alignmentOffsetRatio(profile[0],0,profile.length),1);
  close(previous,DISPLAY.alignmentResidual);
  for(const stage of [...stages].reverse())for(const u of [0,.5,1]){
    const ratio=alignmentOffsetRatio(stage,u,profile.length);
    if(['to-mold','dispense','fill','mold-cure','postcure','compare'].includes(stage.kind))close(ratio,DISPLAY.alignmentResidual);
    else if(stage.kind!=='reflow')close(ratio,1);
  }
  for(const stage of buildStages(data,'TC-NCF'))close(alignmentOffsetRatio(stage,.5,profile.length),1);
  close(alignmentOffsetRatio(profile[0],-1,profile.length),1);
  close(alignmentOffsetRatio(profile.at(-1),2,profile.length),DISPLAY.alignmentResidual);
});
