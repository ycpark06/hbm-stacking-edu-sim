// Browser-safe image pipeline; original golden arithmetic is preserved.
export {subpixelPeak, affineFit} from './alignment.js';
import {affineFit,subpixelPeak} from './alignment.js';
export const VISION_DEFAULTS = Object.freeze({
  // calc/midterm/vision.py:5
  pixel_um: Object.freeze({"value": 1.725, "unit": "um/px", "kind": "midterm", "source": "calc/midterm/vision.py:5"}),
  // calc/midterm/vision.py:7
  N: Object.freeze({"value": 128, "unit": "px", "kind": "midterm", "source": "calc/midterm/vision.py:7"}),
  // calc/midterm/vision.py:19
  template_size: Object.freeze({"value": 80, "unit": "px", "kind": "midterm", "source": "calc/midterm/vision.py:19"}),
  // calc/midterm/vision.py:7
  arm: Object.freeze({"value": 60, "unit": "px", "kind": "midterm", "source": "calc/midterm/vision.py:7"}),
  // calc/midterm/vision.py:7
  w: Object.freeze({"value": 6, "unit": "px", "kind": "midterm", "source": "calc/midterm/vision.py:7"}),
  // calc/midterm/vision.py:7
  blur: Object.freeze({"value": 1, "unit": "px", "kind": "midterm", "source": "calc/midterm/vision.py:7"}),
  // calc/midterm/vision.py:7
  bright: Object.freeze({"value": 220, "unit": "gray", "kind": "midterm", "source": "calc/midterm/vision.py:7"}),
  // calc/midterm/vision.py:7
  dark: Object.freeze({"value": 30, "unit": "gray", "kind": "midterm", "source": "calc/midterm/vision.py:7"}),
  // calc/midterm/vision.py:77
  noise_sigma: Object.freeze({"value": 2, "unit": "gray", "kind": "midterm", "source": "calc/midterm/vision.py:77"}),
  // calc/midterm/vision.py:77
  frames: Object.freeze({"value": 4, "unit": "count", "kind": "midterm", "source": "calc/midterm/vision.py:77"}),
  // calc/midterm/vision.py:32
  gray_max: Object.freeze({"value": 1023, "unit": "gray", "kind": "midterm", "source": "calc/midterm/vision.py:32"}),
  // calc/midterm/vision.py:82
  tol_um: Object.freeze({"value": 0.15, "unit": "um", "kind": "midterm", "source": "calc/midterm/vision.py:82"}),
  // calc/midterm/vision.py:82 (0.002 deg)
  tol_theta_mrad: Object.freeze({"value": 0.03490658503988659, "unit": "mrad", "kind": "midterm", "source": "calc/midterm/vision.py:82 (0.002 deg)"}),
  // calc/midterm/vision.py:80
  max_iter: Object.freeze({"value": 3, "unit": "count", "kind": "midterm", "source": "calc/midterm/vision.py:80"}),
  // calc/midterm/vision.py:83-84
  map_error_sigma: Object.freeze({"value": 0.0005, "unit": "ratio", "kind": "midterm", "source": "calc/midterm/vision.py:83-84"}),
  // calc/midterm/vision.py:83-84
  stage_sigma_um: Object.freeze({"value": 0.02, "unit": "um", "kind": "midterm", "source": "calc/midterm/vision.py:83-84"}),
  // docs/report/midterm/03_시스템구성.md 3.3 미동 XY 10 nm
  stage_resolution_um: Object.freeze({"value": 0.01, "unit": "um", "kind": "midterm", "source": "docs/report/midterm/03_시스템구성.md 3.3 미동 XY 10 nm"}),
  // calc/midterm/vision.py:84 (0.0003 deg)
  theta_sigma_mrad: Object.freeze({"value": 0.005235987755982988, "unit": "mrad", "kind": "midterm", "source": "calc/midterm/vision.py:84 (0.0003 deg)"}),
  // 가정: θ 지령 양자화 자료 없음; 반복 오차만 반영
  theta_resolution_mrad: Object.freeze({"value": 0, "unit": "mrad", "kind": "assumption", "source": "가정: θ 지령 양자화 자료 없음; 반복 오차만 반영"}),
  // calc/midterm/vision.py:95; 중간 9.6절
  mark_spacing_um: Object.freeze({"value": 4000, "unit": "um", "kind": "midterm", "source": "calc/midterm/vision.py:95; 중간 9.6절"}),
  // 가정: 기본 균일 조명; vision_robust.py:5의 곱셈 기울기 모델
  gradient_x: Object.freeze({"value": 0, "unit": "ratio", "kind": "assumption", "source": "가정: 기본 균일 조명; vision_robust.py:5의 곱셈 기울기 모델"}),
  // 가정: X와 동일한 선형 조명 모델을 Y로 확장
  gradient_y: Object.freeze({"value": 0, "unit": "ratio", "kind": "assumption", "source": "가정: X와 동일한 선형 조명 모델을 Y로 확장"}),
  // calc/midterm/vision.py:79
  initial_um: Object.freeze({"value": 30, "unit": "um", "kind": "midterm", "source": "calc/midterm/vision.py:79"}),
  // calc/midterm/vision.py:79 (0.3 deg)
  initial_theta_mrad: Object.freeze({"value": 5.235987755982988, "unit": "mrad", "kind": "midterm", "source": "calc/midterm/vision.py:79 (0.3 deg)"}),
});
export function visionOptions(params, overrides={}) {
  return {...Object.fromEntries(Object.entries(VISION_DEFAULTS).map(([k,v])=>[k,params?.alignment?.[k]?.value ?? v.value])),...overrides};
}
export function render(dx,dy,options={}) {
  const {N,arm,w,blur,bright,dark}=visionOptions(options.params,options);
  if(![dx,dy,N,arm,w,blur,bright,dark].every(Number.isFinite)||!Number.isInteger(N)||N<2||arm<=0||w<=0||blur<0||blur>=N/2) throw new RangeError("render inputs");
  const overlap=(i,center,width)=>Math.max(0,Math.min(i+1-N/2,center+width/2)-Math.max(i-N/2,center-width/2));
  const img=Array.from({length:N},(_,y)=>Array.from({length:N},(_,x)=>Math.fround(bright-(bright-dark)*(overlap(x,dx,arm)*overlap(y,dy,w)+overlap(x,dx,w)*overlap(y,dy,arm)-overlap(x,dx,w)*overlap(y,dy,w)))));
  if(!blur) return img;
  // Original reference: OpenCV GaussianBlur support approximately ±4 sigma.
  const k=Math.round(8*blur+1)|1,r=(k-1)/2,g=Array.from({length:k},(_,i)=>Math.exp(-((i-r)**2)/(2*blur**2))),sum=g.reduce((s,v)=>s+v,0);
  g.forEach((v,i)=>g[i]=v/sum);
  const reflect=i=>i<0?-i:i>=N?2*N-2-i:i;
  const tmp=img.map((row,y)=>row.map((_,x)=>g.reduce((s,v,j)=>s+v*img[y][reflect(x+j-r)],0)));
  return tmp.map((row,y)=>row.map((_,x)=>g.reduce((s,v,j)=>s+v*tmp[reflect(y+j-r)][x],0)));
}

const rows=image=>Array.isArray(image)?image:Array.from({length:image.height},(_,y)=>Array.from(image.data.subarray(y*image.width,(y+1)*image.width)));
const packed=im=>({data:Float32Array.from(im.flat()),width:im[0].length,height:im.length});
/** Multiplicative flat-field division by a separately acquired blank reference.
 * Without a blank, fit a plane to the outer border (assumption: no mark there).
 */
export function flatten(image,reference) {
  const im=rows(image),N=im.length,W=im[0].length;
  let plane;
  if(!reference) {
    const P=[],S=[];
    for(let y=0;y<N;y++)for(let x=0;x<W;x++)if(x===0||y===0||x===W-1||y===N-1){P.push([x,y]);S.push([im[y][x],0]);}
    const fit=affineFit(P,S);plane=im.map((r,y)=>r.map((_,x)=>fit.A[0][0]*x+fit.A[0][1]*y+fit.b[0]));
  } else plane=rows(reference);
  const av=plane.flat().reduce((a,b)=>a+b,0)/(N*W);
  if(plane.length!==N||plane.some(r=>r.length!==W||r.some(v=>!(v>0))))throw new RangeError('flat field shape/positive illumination');
  return im.map((r,y)=>r.map((v,x)=>v*av/plane[y][x]));
}
/** Exact valid NCC; no FFT approximation. Map coordinates are template origins. */
export function nccMap(image,template) {
  const im=rows(image),tpl=rows(template),n=tpl.length,N=im.length,size=N-n+1;
  if(size<3||im.some(r=>r.length!==N)||tpl.some(r=>r.length!==n))throw new RangeError('square image/template with search margin required');
  const av=tpl.flat().reduce((s,v)=>s+v,0)/(n*n),tp=tpl.map(r=>r.map(v=>v-av)),norm=tp.flat().reduce((s,v)=>s+v*v,0);
  if(!norm)throw new RangeError('constant template');
  const map=Array.from({length:size},()=>Array(size));let best=-Infinity,bx=0,by=0;
  for(let y=0;y<size;y++)for(let x=0;x<size;x++) {
    let sum=0,sq=0,num=0;
    for(let j=0;j<n;j++)for(let i=0;i<n;i++){const v=im[y+j][x+i];sum+=v;sq+=v*v;num+=tp[j][i]*v;}
    const variance=sq-sum*sum/(n*n),v=variance>0?num/Math.sqrt(norm*variance):-Infinity;
    map[y][x]=v;if(v>best){best=v;bx=x;by=y;}
  }
  if(!Number.isFinite(best))throw new RangeError('no image contrast');
  return {map,bx,by,best,n,N};
}
export function detect(image,options={}) {
  const c=visionOptions(options.params,options),im=c.flatten?flatten(image,c.flat_field):rows(image);
  const r=nccMap(im,c.template??render(0,0,{...c,N:c.template_size})),{map,bx,by,n,N}=r;
  if(bx===0||by===0||bx===map.length-1||by===map.length-1)throw new RangeError('NCC peak at search boundary');
  const x=bx+subpixelPeak(map[by][bx-1],map[by][bx],map[by][bx+1],c.method??'gauss')+n/2-N/2;
  const y=by+subpixelPeak(map[by-1][bx],map[by][bx],map[by+1][bx],c.method??'gauss')+n/2-N/2;
  return {x_px:x,y_px:y,score:r.best,ncc:packed(map),canvas_x:x+N/2,canvas_y:y+N/2};
}
// Legacy signature/results, including the fixed original 80 px template.
export function measure(image,method='gauss') {
  const d=detect(image,{method});return [d.x_px,d.y_px];
}
export function renderImage(dx,dy,options={}) {
  const c=visionOptions(options.params,options),base=render(dx,dy,c);
  if(c.noise_sigma>0&&!c.rng?.normal)throw new TypeError('seeded rng.normal required');
  if(!Number.isInteger(c.frames)||c.frames<1||c.noise_sigma<0)throw new RangeError('noise/frames');
  return packed(base.map((r,y)=>r.map((v,x)=>{
    const light=1+c.gradient_x*(x/c.N-.5)+c.gradient_y*(y/c.N-.5);
    if(light<=0)throw new RangeError('illumination must be positive');
    let sum=0;for(let f=0;f<c.frames;f++)sum+=Math.max(0,Math.min(c.gray_max,Math.round(v*light+(c.noise_sigma?c.rng.normal(0,c.noise_sigma):0))));
    return sum/c.frames;
  })));
}
const transform=(p,cal)=>cal.A.map((r,i)=>r[0]*p[0]+r[1]*p[1]+cal.b[i]);
/** Four local ROIs at corner marks; mark orientations remain axis aligned.
 * Rotation is inferred from mark centres, not local glyph rotation. ROI origins
 * track nominal marks; both optical channels use a shared calibrated mapping.
 */
export function alignLayer(options={}) {
  const c=visionOptions(options.params,options),rng=options.rng;
  if(!rng?.normal)throw new TypeError("seeded rng.normal from sim/rng.js required");
  let dx=c.true_dx_um??0,dy=c.true_dy_um??0,theta=c.true_theta_mrad??0;
  if(![dx,dy,theta,c.pixel_um,c.tol_um,c.tol_theta_mrad,c.max_iter,c.stage_sigma_um,c.stage_resolution_um,c.theta_sigma_mrad,c.theta_resolution_mrad,c.map_error_sigma,c.mark_spacing_um].every(Number.isFinite)||c.mark_spacing_um<=0||c.pixel_um<=0||c.tol_um<=0||c.tol_theta_mrad<=0||!Number.isInteger(c.max_iter)||c.max_iter<0||[c.stage_sigma_um,c.stage_resolution_um,c.theta_sigma_mrad,c.theta_resolution_mrad,c.map_error_sigma].some(v=>v<0))throw new RangeError('alignment inputs');
  const cal=c.calibration??{A:[[c.pixel_um,0],[0,c.pixel_um]],b:[0,0]},det=cal.A[0][0]*cal.A[1][1]-cal.A[0][1]*cal.A[1][0];
  if(!Number.isFinite(det)||det===0)throw new RangeError('singular calibration');
  const inverse=([x,y])=>[(cal.A[1][1]*x-cal.A[0][1]*y)/det,(-cal.A[1][0]*x+cal.A[0][0]*y)/det];
  const half=c.mark_spacing_um/2,marks=[[-half,-half],[half,-half],[half,half],[-half,half]],history=[];
  const template=render(0,0,{...c,N:c.template_size});
  for(let iteration=0;iteration<=c.max_iter;iteration++) {
    const a=theta/1000,cs=Math.cos(a),sn=Math.sin(a);
    const fiducials=marks.map(([x,y])=>{
      const offset=[dx+(cs-1)*x-sn*y,dy+sn*x+(cs-1)*y],p=inverse(offset);
      const upper=renderImage(...p,{...c,rng}),lower=renderImage(0,0,{...c,rng});
      const up=detect(upper,{...c,template,flatten:true}),lo=detect(lower,{...c,template,flatten:true});
      const u=transform([up.x_px,up.y_px],cal),l=transform([lo.x_px,lo.y_px],cal);
      return {nominal_um:[x,y],upper,lower,upper_detection:up,lower_detection:lo,delta_um:u.map((v,i)=>v-l[i])};
    });
    const mx=fiducials.reduce((s,f)=>s+f.delta_um[0],0)/marks.length,my=fiducials.reduce((s,f)=>s+f.delta_um[1],0)/marks.length;
    let cross=0,dot=0;for(const f of fiducials){const [x,y]=f.nominal_um,[ex,ey]=f.delta_um;cross+=x*(y+ey-my)-y*(x+ex-mx);dot+=x*(x+ex-mx)+y*(y+ey-my);}
    const mt=Math.atan2(cross,dot)*1000,converged=Math.abs(mx)<=c.tol_um&&Math.abs(my)<=c.tol_um&&Math.abs(mt)<=c.tol_theta_mrad;
    const row={iteration,fiducials,measured:{dx_um:mx,dy_um:my,theta_mrad:mt},residual:{dx_um:dx,dy_um:dy,theta_mrad:theta},converged,command:null};history.push(row);
    if(converged||iteration===c.max_iter)break;
    const quant=(v,res)=>res?Math.round(v/res)*res:v,map=1+rng.normal(0,c.map_error_sigma);
    row.command={dx_um:quant(-mx*map,c.stage_resolution_um),dy_um:quant(-my*map,c.stage_resolution_um),theta_mrad:quant(-mt,c.theta_resolution_mrad)};
    dx+=row.command.dx_um+rng.normal(0,c.stage_sigma_um);dy+=row.command.dy_um+rng.normal(0,c.stage_sigma_um);theta+=row.command.theta_mrad+rng.normal(0,c.theta_sigma_mrad);
  }
  return {history,converged:history.at(-1).converged,iterations:history.length-1,residual:history.at(-1).residual,config:Object.fromEntries(Object.keys(VISION_DEFAULTS).map(k=>[k,c[k]]))};
}
