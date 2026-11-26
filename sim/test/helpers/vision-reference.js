// Test-only numeric reference for seven image golden cases. Stage 4's production
// vision pipeline is deliberately not exported from sim/alignment.js.
// 원본 vision.py:7-29; reference_models.py:render_cross/gaussian_blur/ncc_map.
import {subpixelPeak} from '../../alignment.js';
export function render(dx,dy,{N=128,arm=60,w=6,blur=1,bright=220,dark=30}={}) {
  const overlap=(i,center,width)=>Math.max(0,Math.min(i+1-N/2,center+width/2)-Math.max(i-N/2,center-width/2));
  const img=Array.from({length:N},(_,y)=>Array.from({length:N},(_,x)=>Math.fround(bright-(bright-dark)*(overlap(x,dx,arm)*overlap(y,dy,w)+overlap(x,dx,w)*overlap(y,dy,arm)-overlap(x,dx,w)*overlap(y,dy,w)))));
  if(!blur) return img;
  const k=Math.round(8*blur+1)|1,r=(k-1)/2,g=Array.from({length:k},(_,i)=>Math.exp(-((i-r)**2)/(2*blur**2))),sum=g.reduce((s,v)=>s+v,0);
  g.forEach((v,i)=>g[i]=v/sum);
  const reflect=i=>i<0?-i:i>=N?2*N-2-i:i;
  const tmp=img.map((row,y)=>row.map((_,x)=>g.reduce((s,v,j)=>s+v*img[y][reflect(x+j-r)],0)));
  return tmp.map((row,y)=>row.map((_,x)=>g.reduce((s,v,j)=>s+v*tmp[reflect(y+j-r)][x],0)));
}
let tpl;
export function measure(img,method='gauss') {
  tpl??=render(0,0,{N:80});const n=tpl.length,N=img.length,size=N-n+1;
  const av=tpl.flat().reduce((s,v)=>s+v,0)/(n*n),tp=tpl.map(r=>r.map(v=>v-av)),norm=tp.flat().reduce((s,v)=>s+v*v,0);
  const map=Array.from({length:size},()=>Array(size));let best=-Infinity,bx=0,by=0;
  for(let y=0;y<size;y++) for(let x=0;x<size;x++) {
    let sum=0,sq=0,num=0;
    for(let j=0;j<n;j++) for(let i=0;i<n;i++) {const v=img[y+j][x+i];sum+=v;sq+=v*v;num+=tp[j][i]*v;}
    const v=num/Math.sqrt(norm*(sq-sum*sum/(n*n)));map[y][x]=v;
    if(v>best) {best=v;bx=x;by=y;}
  }
  return [bx+subpixelPeak(map[by][bx-1],map[by][bx],map[by][bx+1],method)+n/2-N/2,by+subpixelPeak(map[by-1][bx],map[by][bx],map[by+1][bx],method)+n/2-N/2];
}
