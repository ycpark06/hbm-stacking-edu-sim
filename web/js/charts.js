const palette=['#5ce0c2','#71acff','#ffbe6f','#c99aff','#fa92ad','#f5e278','#ff794d','#41c9ef','#cecece','#a8d56b','#dd70e2','#bd9974'];
export function chart(canvas,series,{xLabel='',yLabel='',lines=[],bars=false}={}) {
  const light=canvas.ownerDocument.documentElement?.dataset.theme==='light';
  const colors=light?['#14365A','#44505F','#315F83','#645187','#34685E','#715B30','#80485B','#286975','#555E69','#50682E','#744B79','#74543C']:palette;
  const text=light?'#44505F':'#adbed1',axis=light?'#7A8899':'#40516a';
  const ctx=canvas.getContext('2d'),W=1000,H=300;canvas.width=W;canvas.height=H;
  ctx.clearRect(0,0,W,H);ctx.font=light?'14px "Pretendard", "Malgun Gothic", "맑은 고딕", "Apple SD Gothic Neo", sans-serif':'14px system-ui';
  const points=series.flatMap(s=>s.points).filter(([x,y])=>Number.isFinite(x)&&Number.isFinite(y));
  if(!points.length){canvas.nextElementSibling.textContent='해당 이력 없음';ctx.fillStyle=text;ctx.fillText('이 결과에는 해당 이력이 없습니다.',60,80);return;}
  let xmin=0,xmax=1,ymin=0,ymax=1;
  for(const [x,y] of points){xmin=Math.min(xmin,x);xmax=Math.max(xmax,x);ymin=Math.min(ymin,y);ymax=Math.max(ymax,y);}
  for(const l of lines){ymin=Math.min(ymin,l.value);ymax=Math.max(ymax,l.value);}
  const X=x=>65+(x-xmin)/(xmax-xmin)*865,Y=y=>240-(y-ymin)/(ymax-ymin||1)*200;
  ctx.strokeStyle=axis;ctx.beginPath();ctx.moveTo(65,25);ctx.lineTo(65,240);ctx.lineTo(935,240);ctx.stroke();
  ctx.fillStyle=text;ctx.fillText(`${yLabel} · 계산 결과`,65,18);ctx.fillText(xLabel,850,285);
  for(let i=0;i<=4;i++){let v=ymin+(ymax-ymin)*i/4;ctx.fillText(v.toFixed(2),3,Y(v)+4);let x=xmin+(xmax-xmin)*i/4;ctx.fillText(x.toFixed(1),X(x)-10,260);}
  lines.forEach(l=>{ctx.strokeStyle=light?'#44505F':'#ffb86c';ctx.setLineDash([6,5]);ctx.beginPath();ctx.moveTo(65,Y(l.value));ctx.lineTo(935,Y(l.value));ctx.stroke();ctx.setLineDash([]);ctx.fillStyle=light?text:'#ffce94';ctx.fillText(l.label,650,Y(l.value)-5);});
  series.forEach((s,i)=>{if(bars){const [x,y]=s.points.at(-1);ctx.fillStyle=colors[i%colors.length];ctx.fillRect(X(x)-9,Y(y),18,Y(0)-Y(y));return;}ctx.strokeStyle=colors[i%colors.length];ctx.beginPath();let started=false;for(const [x,y]of s.points){if(!Number.isFinite(x)||!Number.isFinite(y)){started=false;continue;}if(!started){ctx.moveTo(X(x),Y(y));started=true;}else ctx.lineTo(X(x),Y(y));}ctx.stroke();});
  canvas.setAttribute('aria-label',`${yLabel}: ${series.map(s=>s.name).join(', ')}`);
  const doc=canvas.ownerDocument;
  canvas.nextElementSibling.replaceChildren(...series.map((s,i)=>{
    const item=doc.createElement('span'),swatch=doc.createElement('span');
    item.className='legend-item';swatch.className='legend-swatch';
    swatch.style.backgroundColor=colors[i%colors.length];swatch.setAttribute('aria-hidden','true');
    item.append(swatch,doc.createTextNode(s.name));return item;
  }));
}
