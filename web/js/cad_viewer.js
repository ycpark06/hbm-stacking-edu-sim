import * as THREE from '../vendor/three/build/three.module.js';
import {OrbitControls} from '../vendor/three/examples/jsm/controls/OrbitControls.js';
import {GLTFLoader} from '../vendor/three/examples/jsm/loaders/GLTFLoader.js';
import {createLightPresentation} from './cad_light.js';
import {GROUPS} from './cad_parts.js';
// Display settings only: Y-up directions and offset as fractions of model extent.
// They do not represent hardware dimensions, motion limits or assembly sequence.
export const EXPLODE = {
  frame:[0,0,0],head:[0,.38,0],z_carriage:[.28,.18,0],
  stack_chuck:[0,.16,.3],reflow_chuck:[.35,.12,.12],
  mold_jig:[-.3,.12,-.18],plunger:[-.3,.42,-.18],
  dispenser:[-.38,.1,.25],ncf_tray:[.35,.05,-.3],camera_bottom:[0,-.12,.38]
};
export async function createCADViewer(container,onSelect,onStatus){
  const scene=new THREE.Scene();scene.background=new THREE.Color('#101b2a');
  const camera=new THREE.PerspectiveCamera(40,1,.01,1000);
  const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));container.append(renderer.domElement);
  const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
  scene.add(new THREE.HemisphereLight(0xdcf5ff,0x263347,3));
  const light=new THREE.DirectionalLight(0xffffff,3);light.position.set(8,15,10);scene.add(light);
  let resize=null,model=null;
  try{
    onStatus('GLB 모델 로드 중…');
    const gltf=await new GLTFLoader().loadAsync('../cad/web/hbm_stacker.glb');model=gltf.scene;
    const nodes=new Map(Object.keys(GROUPS).map(id=>[id,model.getObjectByName(id)]));
    const missing=[...nodes].filter(([,node])=>!node).map(([id])=>id);if(missing.length)throw new Error(`GLB 노드 누락: ${missing.join(', ')}`);
    const box=new THREE.Box3().setFromObject(model),extent=box.getSize(new THREE.Vector3());
    const originalExtent=Math.max(extent.x,extent.y,extent.z);if(!(originalExtent>0))throw new Error('빈 GLB 형상');
    // Normalize only the display wrapper; preserve source geometry and node transforms.
    const wrapper=new THREE.Group();wrapper.scale.setScalar(10/originalExtent);wrapper.add(model);scene.add(wrapper);
    const center=box.getCenter(new THREE.Vector3());model.position.sub(center);
    const bases=new Map([...nodes].map(([id,node])=>[id,node.position.clone()]));
    const originals=new Map();model.traverse(node=>{if(node.isMesh){node.material=Array.isArray(node.material)?node.material.map(m=>m.clone()):node.material.clone();for(const material of [].concat(node.material))originals.set(material,material.emissive.clone());}});
    const light=document.documentElement.dataset.theme==='light'?createLightPresentation(scene,camera,container,Object.fromEntries(nodes)):null;
    function select(id){if(light){light.focus(id);return;}for(const [key,node] of nodes)node.traverse(child=>{if(child.isMesh)for(const material of [].concat(child.material))material.emissive.copy(key===id?new THREE.Color('#245c57'):originals.get(material));});}
    function fit(){
      const bounds=new THREE.Box3().setFromObject(wrapper),size=bounds.getSize(new THREE.Vector3()),target=bounds.getCenter(new THREE.Vector3());
      // Reserve space for exploded groups; camera values are display settings.
      const halfAngle=THREE.MathUtils.degToRad(camera.fov/2),distance=Math.max(size.y,size.x/camera.aspect,size.z)/2/Math.tan(halfAngle)*1.65;
      controls.target.copy(target);camera.position.copy(target).add(new THREE.Vector3(1,.75,1.25).normalize().multiplyScalar(distance));controls.update();
    }
    function size(){const w=container.clientWidth,h=container.clientHeight;if(!w||!h)return;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();fit();}
    resize=new ResizeObserver(size);resize.observe(container);size();
    const ray=new THREE.Raycaster(),pointer=new THREE.Vector2();let down=null;
    renderer.domElement.addEventListener('pointerdown',event=>{down={x:event.clientX,y:event.clientY,id:event.pointerId};});
    renderer.domElement.addEventListener('pointercancel',()=>{down=null;});
    renderer.domElement.addEventListener('pointerup',event=>{
      const start=down;down=null;if(!start||start.id!==event.pointerId||Math.hypot(event.clientX-start.x,event.clientY-start.y)>5)return;
      const r=renderer.domElement.getBoundingClientRect();pointer.set((event.clientX-r.left)/r.width*2-1,-(event.clientY-r.top)/r.height*2+1);
      scene.updateMatrixWorld(true);ray.setFromCamera(pointer,camera);
      const visible=[...nodes.values()].filter(node=>node.visible);
      for(const hit of ray.intersectObjects(visible,true)){
        for(let n=hit.object;n&&n!==model;n=n.parent)if(nodes.get(n.name)===n){onSelect(n.name);return;}
      }
    });
    renderer.domElement.addEventListener('webglcontextlost',event=>{event.preventDefault();renderer.setAnimationLoop(null);onStatus('WebGL 연결이 끊겼습니다. 새로고침하거나 부품 목록·도면을 이용하세요.');});
    renderer.setAnimationLoop(()=>{controls.update();light?.render();renderer.render(scene,camera);});
    onStatus(`GLB 연결 · ${nodes.size}개 그룹 · 회전/확대 가능`);
    return {
      select,
      setVisible(id,value){nodes.get(id).visible=value;},
      explode(amount){const t=Math.max(0,Math.min(1,amount));for(const [id,node] of nodes)node.position.copy(bases.get(id)).addScaledVector(new THREE.Vector3(...EXPLODE[id]),originalExtent*t);},
      reset:fit
    };
  }catch(error){
    resize?.disconnect();controls.dispose();renderer.dispose();renderer.domElement.remove();
    model?.traverse(node=>{if(node.isMesh){node.geometry.dispose();for(const material of [].concat(node.material))material.dispose();}});
    throw error;
  }
}
