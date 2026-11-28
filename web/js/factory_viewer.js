import * as THREE from '../vendor/three/build/three.module.js';
import {OrbitControls} from '../vendor/three/examples/jsm/controls/OrbitControls.js';
import {GLTFLoader} from '../vendor/three/examples/jsm/loaders/GLTFLoader.js';
import {DISPLAY,CAMERA_IDS,filmSectionFrame,cameraFitDistance,explodedAmount,filmSqueezeAt,layerHeat} from './factory_sequence.js';
// Scene dimensions here are display coordinates, never manufacturing dimensions.
export function createFactoryViewer(container,data,onStatus) {
  const p=data.params,scene=new THREE.Scene();scene.background=new THREE.Color('#101c25');
  const camera=new THREE.PerspectiveCamera(38,1,.01,200);
  const renderer=new THREE.WebGLRenderer({antialias:true});renderer.shadowMap.enabled=false;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,DISPLAY.pixelRatio));container.append(renderer.domElement);
  const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
  scene.add(new THREE.HemisphereLight(0xd9f5ff,0x20333e,3));
  const light=new THREE.DirectionalLight(0xffffff,3);light.position.set(5,12,8);scene.add(light);
  const nodes={},bases={},anchors={},stack=new THREE.Group();scene.add(stack);
  const names=['frame','head','z_carriage','stack_chuck','reflow_chuck','mold_jig','plunger','dispenser','ncf_tray','camera_bottom'];
  let headFloor=0,glb,scale=1,ready=false,cam=1,latest=null,simple=false;
  let fitNeeded=true,wasExploded=false;
  const overviewBounds=new THREE.Box3(),explodedBounds=new THREE.Box3(),headBounds=new THREE.Box3();
  // Display offsets in normalized scene space, unrelated to hardware dimensions.
  const explodeOffsets=Object.fromEntries(Object.entries({head:[0,6,-3],z_carriage:[4,4,-2],stack_chuck:[0,3,5],reflow_chuck:[6,2,-4],mold_jig:[-6,2,4],plunger:[-6,6,4],dispenser:[-7,4,-2],ncf_tray:[6,2,4],camera_bottom:[0,-2,5]}).map(([n,v])=>[n,new THREE.Vector3(...v)]));
  const origin=new THREE.Vector3(),dies=[],films=[],resins=[],solderBands=[];
  const heat=DISPLAY.heat,orange=new THREE.Color(heat.orange),red=new THREE.Color(heat.red);
  function box(color,transparent=false){const m=new THREE.Mesh(new THREE.BoxGeometry(1,1,1),new THREE.MeshStandardMaterial({color,metalness:.25,roughness:.42,transparent,opacity:transparent?.65:1}));stack.add(m);return m;}
  for(let i=0;i<data.layers;i++){
    dies.push(box(0x72c8ed));films.push(box(0xc5f17b));resins.push(box(0xf4b16e,true));
    const band=box(heat.solderColor);band.visible=false;
    band.material.emissive.set(heat.solderColor);band.material.emissiveIntensity=heat.solderEmissive;
    solderBands.push(band);
  }
  const carried=box(0x9de0ef),film=box(0xc5f17b,true),tempGauge=box(0xf4b16e),forceGauge=box(0xc5f17b);
  const beam=new THREE.Line(new THREE.BufferGeometry().setFromPoints([origin,origin]),new THREE.LineBasicMaterial({color:0xc5f17b}));scene.add(beam);
  const labels=[];
  function label(text,pos){const canvas=document.createElement('canvas');canvas.width=512;canvas.height=64;const ctx=canvas.getContext('2d');ctx.fillStyle='#10202ddd';ctx.fillRect(0,0,512,64);ctx.font='24px system-ui';ctx.fillStyle='#e7eee9';ctx.fillText(text,12,41);const sprite=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(canvas),depthTest:false}));sprite.position.copy(pos);sprite.position.y+=.4;sprite.scale.set(2.5,.32,1);scene.add(sprite);labels.push(sprite);}
  const modelReady=new Promise((resolve,reject)=>new GLTFLoader().load('../cad/web/hbm_stacker.glb',g=>{
    glb=g.scene;glb.updateMatrixWorld(true);
    const bounds=new THREE.Box3().setFromObject(glb),extent=bounds.getSize(new THREE.Vector3());
    scale=12/Math.max(extent.x,extent.y,extent.z);glb.scale.setScalar(scale);glb.updateMatrixWorld(true);
    const b=new THREE.Box3().setFromObject(glb),center=b.getCenter(new THREE.Vector3());glb.position.sub(new THREE.Vector3(center.x,b.min.y,center.z));scene.add(glb);glb.updateMatrixWorld(true);
    for(const name of names){const node=glb.getObjectByName(name);if(!node)continue;nodes[name]=node;bases[name]=node.position.clone();const box=new THREE.Box3().setFromObject(node);anchors[name]=box.getCenter(new THREE.Vector3());anchors[name].y=box.max.y;if(name==='head')headFloor=box.min.y;
      node.traverse(m=>{if(m.isMesh){m.castShadow=false;m.receiveShadow=false;m.material=m.material.clone();m.material.transparent=true;m.material.userData.originalOpacity=m.material.opacity;}});
    }
    const missing=names.filter(n=>!nodes[n]);if(missing.length){reject(Error(`GLB 노드 없음: ${missing.join(', ')}`));return;}
    overviewBounds.setFromObject(glb);explodedBounds.copy(overviewBounds);
    for(const name of names){
      const bounds=new THREE.Box3().setFromObject(nodes[name]);
      if(['head','z_carriage','stack_chuck'].includes(name))headBounds.union(bounds);
      if(explodeOffsets[name])explodedBounds.union(bounds.translate(explodeOffsets[name]));
    }
    [['stack_chuck','적층'],['reflow_chuck','리플로우'],['mold_jig','가압 충전'],['ncf_tray','공급']].forEach(([n,t])=>label(t,anchors[n]));
    ready=true;onStatus('GLB · 기능 노드 10개 연결 · 그림자 OFF');setCamera(cam);if(latest)update(...latest);resolve();
  },undefined,()=>reject(Error('GLB 로드 실패: ../cad/web/hbm_stacker.glb를 확인하세요.'))));
  function fitBounds(bounds,direction){
    if(bounds.isEmpty())return;
    // Clear pending orbit/pan damping before positioning the fitted camera.
    const damping=controls.enableDamping;controls.enableDamping=false;controls.update();
    const center=bounds.getCenter(new THREE.Vector3()),radius=bounds.getSize(new THREE.Vector3()).length()/2;
    const distance=cameraFitDistance(radius,camera.fov,camera.aspect);
    camera.position.copy(center).addScaledVector(direction.normalize(),distance);
    camera.near=Math.max(.001,distance-radius*1.5);camera.far=distance+radius*3;
    camera.updateProjectionMatrix();controls.target.copy(center);
    controls.update();controls.enableDamping=damping;
  }
  function setCamera(k){const next=Number(k);if(!CAMERA_IDS.includes(next))throw RangeError('camera 1/2/3/4');cam=next;fitNeeded=true;
    if(latest)update(...latest);else if(ready)fitBounds(overviewBounds,new THREE.Vector3(14,7,17));
  }
  function moveNode(name,delta){const n=nodes[name];if(n)n.position.copy(bases[name]).add(delta.clone().divideScalar(scale));}
  function update(s,v){latest=[s,v];if(!ready)return;
    const lerp=(a,b,u)=>a.clone().lerp(b,u),a=anchors.stack_chuck,r=anchors.reflow_chuck,m=anchors.mold_jig,t=anchors.ncf_tray;
    let at=a.clone();
    if(s.kind==='to-reflow')at=lerp(a,r,v.u);
    if(s.kind==='reflow')at=r.clone();
    if(s.kind==='to-mold')at=lerp(r,m,v.u);
    if(['dispense','fill','mold-cure','postcure'].includes(s.kind))at=m.clone();
    if(s.kind==='compare'&&s.mode==='MR-MUF')at=m.clone();
    for(const name of names)nodes[name].position.copy(bases[name]);

    const exploding=s.kind==='exploded';
    if(exploding!==wasExploded){fitNeeded=true;wasExploded=exploding;}
    if(exploding)for(const [name,offset] of Object.entries(explodeOffsets))moveNode(name,offset.clone().multiplyScalar(explodedAmount(v.u)));
    if(s.kind==='supply')moveNode('ncf_tray',new THREE.Vector3(-.3*Math.sin(Math.PI*v.u),0,0));
    if(s.kind==='fill'||s.kind==='mold-cure')moveNode('plunger',new THREE.Vector3(0,-.15*(s.kind==='fill'?v.u:1),0));
    if(s.kind==='dispense')moveNode('dispenser',new THREE.Vector3(0,-.15*Math.sin(Math.PI*v.u),0));
    const zoom=cam>=3?DISPLAY.stackMagnification:7;
    const w=p.geometry.die_size.value/1000*scale*zoom,h=p.geometry.die_thickness.value/1e6*scale*zoom,g=p.geometry.interlayer_gap.value/1e6*scale*zoom*DISPLAY.gapMagnification;
    // Parked GLB tool travel is fitted to the displayed stack surface; this is
    // a display trajectory, not a claim that the hardware has this Z stroke.
    const surface=a.y+Math.max(0,s.layer)*(h+g);
    const travel=Math.max(0,headFloor-surface);
    const down=travel*v.down;
    if(s.kind!=='exploded'){moveNode('head',new THREE.Vector3(0,-down,0));moveNode('z_carriage',new THREE.Vector3(0,-down,0));}
    const attach=['ramp','hold','cool','tack','rise'].includes(s.kind),n=Math.max(v.count,attach?s.layer:0);
    for(let i=0;i<data.layers;i++){
      const y=at.y+i*(h+g)+h/2;dies[i].visible=i<n;films[i].visible=i<n&&s.mode==='TC-NCF';resins[i].visible=i<n&&['fill','mold-cure','postcure','compare'].includes(s.kind)&&s.mode==='MR-MUF';
      // Offset is illustrative only; no invented numeric alignment prediction.
      const offset=s.mode==='TC-NCF'?i*w*.009: s.kind==='reflow'?i*w*.009*(1-(s.segment+v.u)/data.profile.length):i*w*.009;
      dies[i].position.set(at.x+offset,y,at.z);dies[i].scale.set(w,h,w);
      // Keep the film inside the open interlayer gap, away from die/chuck faces.
      // Previously bonded layers retain the final display squeeze even on stage jumps.
      const squeeze=filmSqueezeAt(i<s.layer-1?'rise':s.kind,v.u);
      films[i].position.set(at.x+offset,y-h/2-g/2,at.z);
      films[i].scale.set(w*squeeze.spread,g*.65*squeeze.thickness,w*squeeze.spread);
      const heating=layerHeat(data,s,v,i);
      for(const mesh of [dies[i],films[i]]){
        mesh.material.emissive.copy(orange).lerp(red,heating.glow);
        mesh.material.emissiveIntensity=heat.maxEmissive*heating.glow;
      }
      const band=solderBands[i];band.visible=dies[i].visible&&heating.molten;
      band.position.copy(films[i].position);
      band.scale.set(w*squeeze.spread*heat.bandSpread,g*heat.bandThickness,w*squeeze.spread*heat.bandSpread);
      const f=s.kind==='fill'?Math.sqrt(v.u):1;resins[i].position.set(at.x-w*(1-f)/2,y-h/2-g/2,at.z);resins[i].scale.set(Math.max(.001,w*f),g*.7,w);
    }
    const carryKinds=['supply','align','pickup','ncf','approach'];carried.visible=carryKinds.includes(s.kind);
    let pos=t.clone();if(s.kind==='align')pos=anchors.camera_bottom.clone().add(new THREE.Vector3(0,.7,0));
    if(['pickup','ncf','approach'].includes(s.kind))pos=lerp(t,a,s.kind==='pickup'?v.u:1).add(new THREE.Vector3(0,s.kind==='approach'?(1-v.u)*.7:.7,0));
    carried.position.copy(pos);carried.scale.set(w,h,w);
    film.visible=s.mode==='TC-NCF'&&['ncf','approach'].includes(s.kind);film.position.copy(pos).add(new THREE.Vector3(0,-h-(1-v.u)*.25,0));film.scale.set(w,g,w);
    beam.visible=s.kind==='align';beam.geometry.setFromPoints([anchors.camera_bottom,pos]);
    tempGauge.visible=forceGauge.visible=!['overview','exploded'].includes(s.kind);
    const th=Math.max(.02,v.temp/p.equipment_limits.head_max_temp_C.value),fh=Math.max(.02,v.force/p.equipment_limits.bond_force_max_N.value);
    tempGauge.scale.set(.06,th,.06);tempGauge.position.copy(at).add(new THREE.Vector3(-w,th/2,0));forceGauge.scale.set(.06,fh,.06);forceGauge.position.copy(at).add(new THREE.Vector3(-w-.15,fh/2,0));
    const active={align:'camera_bottom',supply:'ncf_tray',ncf:'ncf_tray',approach:'head',ramp:'head',hold:'head',tack:'head',reflow:'reflow_chuck',fill:'plunger',dispense:'dispenser','mold-cure':'mold_jig',postcure:'mold_jig'}[s.kind];
    for(const name of names)nodes[name].traverse(mesh=>{if(mesh.isMesh){mesh.material.opacity=cam>=3?.12:mesh.material.userData.originalOpacity;if(mesh.material.emissive){mesh.material.emissive.set(name===active?0x396924:0);mesh.material.emissiveIntensity=.45;}}});
    labels.forEach(l=>l.visible=cam===1&&!simple);
    const stackBounds=new THREE.Box3().setFromCenterAndSize(at.clone().add(new THREE.Vector3(0,data.layers*(h+g)/2,0)),new THREE.Vector3(w*4,Math.max(2,data.layers*(h+g)+1),w*3));
    const layerIndex=Math.max(1,s.layer)-1;
    const edgeOffset=s.mode==='TC-NCF'?layerIndex*w*.009:dies[layerIndex].position.x-at.x;
    const section=filmSectionFrame(w,h,g,s.layer,edgeOffset);
    const sectionBounds=new THREE.Box3().setFromCenterAndSize(at.clone().add(new THREE.Vector3(...section.center)),new THREE.Vector3(...section.size));
    if(fitNeeded){
      const bounds=exploding?explodedBounds:cam===1?overviewBounds:cam===2?headBounds:cam===4?sectionBounds:stackBounds;
      fitBounds(bounds,new THREE.Vector3(...(cam===1?[14,7,17]:cam===2?[3,2.3,5]:cam===4?DISPLAY.filmSection.direction:[4,1.5,5])));fitNeeded=false;
    }else if(cam>=3&&!exploding){const center=(cam===4?sectionBounds:stackBounds).getCenter(new THREE.Vector3()),delta=center.clone().sub(controls.target);camera.position.add(delta);controls.target.copy(center);}

  }
  const resize=new ResizeObserver(()=>{const w=container.clientWidth,h=container.clientHeight;if(!w||!h)return;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();fitNeeded=true;if(latest)update(...latest);});resize.observe(container);
  let slow=0,last=performance.now();
  function render(now){const dt=now-last;last=now;if(dt>40&&dt<1000)slow++;else slow=Math.max(0,slow-1);if(slow>90&&!simple){simple=true;renderer.setPixelRatio(1);labels.forEach(l=>l.visible=false);onStatus('GLB · 성능 단순화: 픽셀 비율 1 / 라벨 숨김');}controls.update();renderer.render(scene,camera);}
  return {ready:modelReady,update,setCamera,render};
}
