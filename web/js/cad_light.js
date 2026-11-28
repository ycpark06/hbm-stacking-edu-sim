import * as THREE from '../vendor/three/build/three.module.js';
import {GROUPS} from './cad_parts.js';
// All values in this module are display settings, not material properties.
export const LIGHT_COLORS=Object.freeze({frame:'#C9D0D8',head:'#14365A',z_carriage:'#14365A',stack_chuck:'#E08A3C',reflow_chuck:'#B8322A',mold_jig:'#3E8E5A',plunger:'#3E8E5A',dispenser:'#7A5BA6',ncf_tray:'#7A5BA6',camera_bottom:'#7A8899'});
export const LIGHT_ROLES=Object.freeze({frame:'하중 지지 · 기판 XY 이동',head:'하중 전달 · 가열 · 접합',z_carriage:'헤드 하중과 위치 전달',stack_chuck:'층별 지지 · 진공 고정',reflow_chuck:'스택 일괄 가열 · 냉각',mold_jig:'캐비티·게이트·벤트로 수지 안내',plunger:'수지를 가압 이송',dispenser:'충전 전 액상 수지 공급',ncf_tray:'필름 부착 다이 공급 준비',camera_bottom:'하부 광로로 충전 선단 관찰'});
export function createLightPresentation(scene,camera,container,nodes){
  scene.background=new THREE.Color('#FFFFFF');
  scene.traverse(n=>{if(n.isHemisphereLight){n.color.set('#FFFFFF');n.groundColor.set('#C9D0D8');n.intensity=2;}if(n.isDirectionalLight)n.intensity=1.3;});
  for(const [id,node] of Object.entries(nodes))node.traverse(mesh=>{
    if(!mesh.isMesh)return;
    mesh.material=Array.isArray(mesh.material)?mesh.material.map(m=>m.clone()):mesh.material.clone();
    for(const m of [].concat(mesh.material)){m.color.set(LIGHT_COLORS[id]);m.emissive?.set(0);m.metalness=.05;m.roughness=.8;}
    const edge=new THREE.LineSegments(new THREE.EdgesGeometry(mesh.geometry,35),new THREE.LineBasicMaterial({color:'#44505F',transparent:true,opacity:.35}));edge.userData.lightEdge=true;mesh.add(edge);
  });
  scene.updateMatrixWorld(true);
  const bounds=new THREE.Box3();for(const n of Object.values(nodes))bounds.union(new THREE.Box3().setFromObject(n));
  const size=bounds.getSize(new THREE.Vector3()),center=bounds.getCenter(new THREE.Vector3());
  const canvas=document.createElement('canvas');canvas.width=canvas.height=128;const ctx=canvas.getContext('2d'),gradient=ctx.createRadialGradient(64,64,0,64,64,64);gradient.addColorStop(0,'#14365A30');gradient.addColorStop(1,'#14365A00');ctx.fillStyle=gradient;ctx.fillRect(0,0,128,128);
  const shadow=new THREE.Mesh(new THREE.PlaneGeometry(size.x*1.5,size.z*1.5),new THREE.MeshBasicMaterial({map:new THREE.CanvasTexture(canvas),transparent:true,depthWrite:false}));shadow.rotation.x=-Math.PI/2;shadow.position.set(center.x,bounds.min.y-.01,center.z);scene.add(shadow);
  const overlay=document.createElement('div');overlay.className='light-callout';overlay.hidden=true;
  const line=document.createElementNS('http://www.w3.org/2000/svg','svg');line.classList.add('light-leader');line.innerHTML='<path fill="none" stroke="#14365A" stroke-width="2"/>';container.append(line,overlay);
  let focused=null;
  function focus(id){
    if(id!==null&&!nodes[id])throw RangeError('unknown part group');focused=id;
    if(id){overlay.replaceChildren();const title=document.createElement('strong'),role=document.createElement('span');title.textContent=GROUPS[id].name;role.textContent=LIGHT_ROLES[id];overlay.append(title,role);}
    apply();
  }
  function apply(){for(const [id,node] of Object.entries(nodes))node.traverse(mesh=>{
    if(mesh.isMesh)for(const m of [].concat(mesh.material)){m.color.set(focused&&focused!==id?'#C9D0D8':LIGHT_COLORS[id]);m.opacity=focused&&focused!==id?.25:1;m.transparent=m.opacity<1;m.depthWrite=m.opacity===1;m.emissive?.set(0);}
    if(mesh.userData.lightEdge)mesh.material.opacity=focused&&focused!==id?.08:.35;
  });}
  function render(){
    const node=focused&&nodes[focused];overlay.hidden=line.hidden=!node||!node.visible;if(!node||!node.visible)return;
    scene.updateMatrixWorld(true);const p=new THREE.Box3().setFromObject(node).getCenter(new THREE.Vector3()).project(camera);
    if(p.z < -1||p.z>1){overlay.hidden=line.hidden=true;return;}
    const w=container.clientWidth,h=container.clientHeight,x=(p.x+1)*w/2,y=(1-p.y)*h/2;
    const left=Math.max(16,Math.min(w-overlay.offsetWidth-16,x+45)),top=Math.max(92,Math.min(h-overlay.offsetHeight-250,y-120));
    overlay.style.left=`${left}px`;overlay.style.top=`${top}px`;line.setAttribute('viewBox',`0 0 ${w} ${h}`);line.firstChild.setAttribute('d',`M${x} ${y}L${left+20} ${top+overlay.offsetHeight}`);
  }
  focus(null);return {focus,apply,render};
}
export function setLightTitle(container,text){
  let title=container.querySelector('.light-scene-title');
  if(!title){title=document.createElement('div');title.className='light-scene-title';container.append(title);}
  title.textContent=String(text??'');title.hidden=!title.textContent;
}
