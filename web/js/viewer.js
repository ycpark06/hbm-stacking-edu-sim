import * as THREE from '../vendor/three/build/three.module.js';
import {OrbitControls} from '../vendor/three/examples/jsm/controls/OrbitControls.js';
import {GLTFLoader} from '../vendor/three/examples/jsm/loaders/GLTFLoader.js';
// Fixture proportions, colours, camera, timing and scale below are schematic
// display settings, not dimensions of the hardware or process inputs. Dies use params.
export function createViewer(container,p,onStatus) {
  const lightTheme=document.documentElement.dataset.theme==='light';
  const scene=new THREE.Scene();scene.background=new THREE.Color(lightTheme?'#FFFFFF':'#101b2a');
  const camera=new THREE.PerspectiveCamera(40,1,.01,1000);camera.position.set(14,12,17);
  const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));container.append(renderer.domElement);
  const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(0,2,0);controls.enableDamping=true;
  scene.add(new THREE.HemisphereLight(0xdcf5ff,0x263347,3));const light=new THREE.DirectionalLight(0xffffff,3);light.position.set(8,15,10);scene.add(light);
  const fixture=new THREE.Group();scene.add(fixture);const dies=new THREE.Group();scene.add(dies);
  function box(x,y,z,color,parent=fixture){const mesh=new THREE.Mesh(new THREE.BoxGeometry(x,y,z),new THREE.MeshStandardMaterial({color,metalness:.35,roughness:.4}));parent.add(mesh);return mesh;}
  box(12,.7,10,0x3b4f66).position.y=-.8;
  const chuck=box(7,.5,7,0x9faebe);chuck.position.y=-.25;
  const head=box(4,1,4,0xc2d1e0);head.position.y=5;
  let movers=[head],bases=[head.position.y],anchor=new THREE.Vector3(0,0,0),glb=null;
  let layer=0,target=0,phase='',recipe={thickness_um:p.geometry.die_thickness.value,gap_um:p.geometry.interlayer_gap.value},warp=0,exaggeration=1;
  const size=p.geometry.die_size.value;
  function rebuild(){while(dies.children.length){const m=dies.children[0];dies.remove(m);m.geometry.dispose();m.material.dispose();}
    for(let i=0;i<layer;i++){
      const h=recipe.thickness_um/1000,gap=recipe.gap_um/1000;
      const geometry=new THREE.BoxGeometry(size,h,size,20,1,1),pos=geometry.attributes.position;
      for(let v=0;v<pos.count;v++){const x=pos.getX(v);pos.setY(v,pos.getY(v)+warp/1000*exaggeration*(1-(2*x/size)**2));}geometry.computeVertexNormals();
      const m=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({color:i%2?0x6ba8d9:0x55ccb4}));
      m.position.set(anchor.x,anchor.y+i*(h+gap)+h/2,anchor.z);dies.add(m);
    }
  }
  // URL remains relative to web/, including under a Pages repository prefix.
  new GLTFLoader().load('../cad/web/hbm_stacker.glb',g=>{
    glb=g.scene;
    // Normalize arbitrary CAD units using its bounding box; preserve node names.
    glb.updateMatrixWorld(true);const bounds=new THREE.Box3().setFromObject(glb),extent=bounds.getSize(new THREE.Vector3());
    const scale=12/Math.max(extent.x,extent.y,extent.z);glb.scale.setScalar(scale);glb.updateMatrixWorld(true);
    const b=new THREE.Box3().setFromObject(glb),center=b.getCenter(new THREE.Vector3());glb.position.sub(new THREE.Vector3(center.x,b.min.y,center.z));scene.add(glb);glb.updateMatrixWorld(true);
    const nodes=['head','z_carriage'].map(n=>glb.getObjectByName(n)).filter(Boolean);
    movers=nodes.filter(n=>!nodes.some(other=>other!==n&&isAncestor(other,n)));
    bases=movers.map(m=>m.position.y);
    const stack=glb.getObjectByName('stack_chuck');if(stack){const cb=new THREE.Box3().setFromObject(stack);anchor=cb.getCenter(new THREE.Vector3());anchor.y=cb.max.y;}
    fixture.visible=false;rebuild();onStatus(`GLB 모델 · ${nodes.length?'헤드 노드 연결':'헤드 노드 없음, 정적 표시'}`);
  },undefined,()=>onStatus('절차적 모델 · GLB 없음 또는 로드 불가'));
  function isAncestor(a,b){for(let n=b.parent;n;n=n.parent)if(n===a)return true;return false;}
  const resize=new ResizeObserver(()=>{const w=container.clientWidth,h=container.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();});resize.observe(container);
  renderer.setAnimationLoop(()=>{target=phase.includes('bond')||phase.includes('tack')?1:0;
    movers.forEach((m,i)=>{const distance=glb?1/glb.scale.y:3;const desired=bases[i]-target*distance;m.position.y+=(desired-m.position.y)*.08;});
    controls.update();renderer.render(scene,camera);
  });
  return {progress(event){recipe=event.recipe;layer=event.layer;phase=event.phase;rebuild();},reset(){layer=0;phase='';rebuild();},warp(value,multiplier){warp=value;exaggeration=multiplier;rebuild();}};
}
