const palette=['#5ce0c2','#71acff','#ffbe6f','#c99aff','#fa92ad','#f5e278'];
export function chart(canvas,series,{xLabel='',yLabel='',lines=[],bars=false}={}) {
  const ctx=canvas.getContext('2d'),W=1000,H=300;canvas.width=W;canvas.height=H;
  ctx.clearRect(0,0,W,H);ctx.font='14px system-ui';
  const points=series.flatMap(s=>s.points).filter(([x,y])=>Number.isFinite(x)&&Number.isFinite(y));
  if(!points.length){canvas.nextElementSibling.textContent='해당 이력 없음';ctx.fillStyle='#adbed1';ctx.fillText('이 결과에는 해당 이력이 없습니다.',60,80);return;}
  let xmin=0,xmax=1,ymin=0,ymax=1;
  for(const [x,y] of points){xmin=Math.min(xmin,x);xmax=Math.max(xmax,x);ymin=Math.min(ymin,y);ymax=Math.max(ymax,y);}
  for(const l of lines){ymin=Math.min(ymin,l.value);ymax=Math.max(ymax,l.value);}
  const X=x=>65+(x-xmin)/(xmax-xmin)*865,Y=y=>240-(y-ymin)/(ymax-ymin||1)*200;
  ctx.strokeStyle='#40516a';ctx.beginPath();ctx.moveTo(65,25);ctx.lineTo(65,240);ctx.lineTo(935,240);ctx.stroke();
  ctx.fillStyle='#adbed1';ctx.fillText(`${yLabel} · 계산 결과`,65,18);ctx.fillText(xLabel,850,285);
  for(let i=0;i<=4;i++){let v=ymin+(ymax-ymin)*i/4;ctx.fillText(v.toFixed(2),3,Y(v)+4);let x=xmin+(xmax-xmin)*i/4;ctx.fillText(x.toFixed(1),X(x)-10,260);}
  lines.forEach(l=>{ctx.strokeStyle='#ffb86c';ctx.setLineDash([6,5]);ctx.beginPath();ctx.moveTo(65,Y(l.value));ctx.lineTo(935,Y(l.value));ctx.stroke();ctx.setLineDash([]);ctx.fillStyle='#ffce94';ctx.fillText(l.label,650,Y(l.value)-5);});
  series.forEach((s,i)=>{if(bars){const [x,y]=s.points.at(-1);ctx.fillStyle=palette[i%palette.length];ctx.fillRect(X(x)-9,Y(y),18,Y(0)-Y(y));return;}ctx.strokeStyle=palette[i%palette.length];ctx.beginPath();let started=false;for(const [x,y]of s.points){if(!Number.isFinite(x)||!Number.isFinite(y)){started=false;continue;}if(!started){ctx.moveTo(X(x),Y(y));started=true;}else ctx.lineTo(X(x),Y(y));}ctx.stroke();});
  canvas.setAttribute('aria-label',`${yLabel}: ${series.map(s=>s.name).join(', ')}`);
  canvas.nextElementSibling.textContent=series.map((s,i)=>`${s.name} (${palette[i%palette.length]})`).join(' · ');
}
