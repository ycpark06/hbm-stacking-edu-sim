import {makeRng} from '../../sim/rng.js';
export async function initVisionView({alignLayer,visionOptions}) {
const $=id=>document.getElementById(id),fmt=v=>v.toFixed(5);
let params,result;
for(let i=1;i<=12;i++)$('layer').add(new Option(`${i}층`,i));
function image(id,im,d){
  const cv=$(id);cv.width=im.width;cv.height=im.height;const ctx=cv.getContext('2d'),pixels=ctx.createImageData(im.width,im.height);
  for(let i=0;i<im.data.length;i++){const v=Math.max(0,Math.min(255,im.data[i]));pixels.data.set([v,v,v,255],i*4);}
  ctx.putImageData(pixels,0,0);ctx.strokeStyle='#26f3cf';ctx.lineWidth=.6;ctx.beginPath();ctx.moveTo(d.canvas_x-8,d.canvas_y);ctx.lineTo(d.canvas_x+8,d.canvas_y);ctx.moveTo(d.canvas_x,d.canvas_y-8);ctx.lineTo(d.canvas_x,d.canvas_y+8);ctx.stroke();
  $(`${id}-info`).textContent=`검출 (${fmt(d.x_px)}, ${fmt(d.y_px)}) px · NCC ${d.score.toFixed(6)} [계산 결과]`;
}
function display(){if(!result)return;const row=result.history[+$('iteration').value],f=row.fiducials[+$('mark').value];image('upper',f.upper,f.upper_detection);image('lower',f.lower,f.lower_detection);}
function graph(){
  const cv=$('graph'),ctx=cv.getContext('2d'),w=cv.width,h=cv.height,p=40,c=result.config;
  const lines=[['#49d8c0','X',r=>Math.abs(r.measured.dx_um)/c.tol_um],['#eeb966','Y',r=>Math.abs(r.measured.dy_um)/c.tol_um],['#b799ff','θ',r=>Math.abs(r.measured.theta_mrad)/c.tol_theta_mrad]];
  const max=Math.max(1.2,...result.history.flatMap(r=>lines.map(l=>l[2](r))));
  // Log1p keeps both the initial displacement and the convergence region visible.
  const y=v=>h-p-Math.log1p(v)/Math.log1p(max)*(h-2*p),x=i=>p+i/Math.max(1,result.history.length-1)*(w-2*p);
  ctx.clearRect(0,0,w,h);ctx.font='14px system-ui';ctx.strokeStyle='#688099';ctx.setLineDash([5,5]);ctx.beginPath();ctx.moveTo(p,y(1));ctx.lineTo(w-p,y(1));ctx.stroke();ctx.setLineDash([]);ctx.fillStyle='#c8d8e8';ctx.fillText('수렴 기준 1 · log(1+비율) 축',p,20);
  for(const [color,label,get] of lines){ctx.strokeStyle=color;ctx.lineWidth=2;ctx.beginPath();result.history.forEach((r,i)=>i?ctx.lineTo(x(i),y(get(r))):ctx.moveTo(x(i),y(get(r))));ctx.stroke();ctx.fillStyle=color;ctx.fillText(label,w-130+lines.findIndex(l=>l[1]===label)*35,20);result.history.forEach((r,i)=>{ctx.beginPath();ctx.arc(x(i),y(get(r)),3,0,Math.PI*2);ctx.fill();});}
  ctx.fillStyle='#b1c2d3';result.history.forEach((r,i)=>ctx.fillText(`${i}회`,x(i)-10,h-12));
}
async function run(){
  $('error').textContent='';$('run').disabled=true;$('status').textContent='합성 영상 검출 중…';
  await new Promise(resolve=>requestAnimationFrame(()=>setTimeout(resolve,0)));
  try{
    const seed=Number($('seed').value);if(!Number.isInteger(seed)||seed<0||seed>4294967295)throw new RangeError('시드는 0~4294967295 정수로 입력하세요.');
    const c=visionOptions(params),rng=makeRng(seed);let initial;
    for(let i=1;i<=+$('layer').value;i++)initial={true_dx_um:rng.uniform(-c.initial_um,c.initial_um),true_dy_um:rng.uniform(-c.initial_um,c.initial_um),true_theta_mrad:rng.uniform(-c.initial_theta_mrad,c.initial_theta_mrad)};
    result=alignLayer({params,rng,...initial});
    $('iteration').replaceChildren(...result.history.map(r=>new Option(`${r.iteration}회${r.iteration===0?' (초기)':''}`,r.iteration)));$('iteration').value=result.iterations;
    $('history').replaceChildren(...result.history.map(r=>{const tr=document.createElement('tr');for(const text of [r.iteration,fmt(r.measured.dx_um),fmt(r.measured.dy_um),fmt(r.measured.theta_mrad),`${fmt(r.residual.dx_um)} / ${fmt(r.residual.dy_um)}`,r.converged?'수렴':'미수렴']){const td=document.createElement('td');td.textContent=text;tr.append(td);}return tr;}));
    $('status').textContent=`${$('layer').value}층 · ${result.iterations}회 보정 · ${result.converged?'수렴':'반복 상한 도달'} [계산 결과]`;
    $('settings').textContent=`수렴 기준: 축별 ${c.tol_um} μm / ${fmt(c.tol_theta_mrad)} mrad · 최대 ${c.max_iter}회 [중간 설계값] · 픽셀 ${c.pixel_um} μm/px · 블러 σ ${c.blur} px · 노이즈 σ ${c.noise_sigma} 계조 · ${c.frames}프레임 [중간 모델값] · XY 분해능 ${c.stage_resolution_um} μm [중간 설계값]`;
    display();graph();
  }catch(e){$('error').textContent=e.message;$('status').textContent='정렬 계산 실패';}finally{$('run').disabled=false;}
}
$('run').addEventListener('click',run);$('layer').addEventListener('change',run);$('iteration').addEventListener('change',display);$('mark').addEventListener('change',display);
try{const response=await fetch(new URL('../../sim/params.json',import.meta.url));if(!response.ok)throw new Error(`params HTTP ${response.status}`);params=await response.json();$('seed').value=params.alignment.mc_seed.value;await run();}catch(e){$('error').textContent=e.message;$('status').textContent='초기화 실패';}

}
