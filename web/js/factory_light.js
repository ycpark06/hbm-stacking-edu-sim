import {sampleStage,filmSqueezeAt} from './factory_sequence.js';
const clamp=u=>Math.max(0,Math.min(1,u));
export function stageCursor(stages,current,u){
  const index=stages.findIndex(s=>s.id===current.id);
  return stages.slice(0,index).reduce((t,s)=>t+s.real_duration_s,0)+clamp(u)*current.real_duration_s;
}
export function lightRecipe(results){
  const recipe=results.representative.find(s=>s.id==='S1').results.find(r=>r.recipe.mode==='TC-NCF'&&!r.recipe.head_temp_compensation);
  if(!recipe?.thermal?.history?.length)throw Error('S1 기본 열 이력 누락');
  return recipe;
}
// A layer's heating is complete on entry to cool, not during approach/ramp/hold.
// Derive this from sequence kinds so direct seeks and reverse playback agree.
export function layerBars(recipe,current,liquidus){
  if(current.mode!=='TC-NCF')return [];
  const complete=['cool','rise','compare'].includes(current.kind);
  const count=Math.max(0,current.layer-(complete?0:1));
  return recipe.thermal_layers.slice(0,Math.max(0,count)).map((r,i)=>({
    layer:i+1,peak_C:r.peak_C,reheat_count:Math.min(r.reheat_count,Math.max(0,count-i-1)),
    color:r.bond_peak_C<liquidus?'#C2622A':'#14365A'
  }));
}
// Axis display settings only: choose a 1/2/5 × power-of-ten step.
export function niceTicks(total,targetIntervals=4){
  if(!Number.isFinite(total)||total<=0)return [0];
  const raw=total/targetIntervals,power=10**Math.floor(Math.log10(raw));
  const step=[1,2,5,10].find(n=>n*power>=raw)*power;
  return Array.from({length:Math.floor(total/step+1e-10)+1},(_,i)=>Number((i*step).toPrecision(12)));
}
export function tcPlot(data,recipe,stages,current,u){
  const layer=Math.max(1,current.layer),parts=stages.filter(s=>s.layer===layer&&['ramp','hold','cool'].includes(s.kind));
  const history=recipe.thermal.history.filter(row=>row.T.length===layer),start=history[0].t_s;
  const total=parts.reduce((t,s)=>t+s.real_duration_s,0);
  // Map stored phase progress onto the same per-phase time axis as the animation.
  const temperature=[];let offset=0;
  for(const s of parts){
    const rows=history.filter(row=>row.phase===`bond-${s.kind}`);
    const next=history.find(row=>row.t_s>rows[0]?.t_s&&row.phase!==`bond-${s.kind}`);
    const end=next?.t_s??recipe.thermal.history.find(row=>row.t_s>rows.at(-1)?.t_s)?.t_s??rows.at(-1)?.t_s;
    for(const row of rows)temperature.push([offset+(row.t_s-rows[0].t_s)/(end-rows[0].t_s||1)*s.real_duration_s,row.T[layer-1]]);
    offset+=s.real_duration_s;
  }
  const head=[],force=[],headSetpoint=recipe.head_setpoints_C[layer-1],base=data.params.tcncf_process.stage_temp.value;
  for(const s of parts)for(const f of [0,1]){const v=sampleStage(data,s,f),t=stageCursor(parts,s,f);head.push([t,s.kind==='ramp'?base+f*(headSetpoint-base):s.kind==='cool'?headSetpoint+f*(base-headSetpoint):headSetpoint]);force.push([t,v.force]);}
  let time=0;
  if(parts.some(s=>s.id===current.id))time=stageCursor(parts,current,u);
  else if(['rise','compare'].includes(current.kind))time=total;
  return {layer,total,time,temperature,head,force,sourceStart:start};
}
export function mrPlot(data,stages,current,u){
  const parts=stages.filter(s=>s.kind==='reflow'),total=parts.reduce((t,s)=>t+s.real_duration_s,0);
  let offset=0;const temperature=[];
  for(const s of parts){for(const f of [0,1])temperature.push([offset+f*s.real_duration_s,sampleStage(data,s,f).temp]);offset+=s.real_duration_s;}
  const time=current.kind==='reflow'?stageCursor(parts,current,u):['to-mold','dispense','fill','mold-cure','postcure','compare'].includes(current.kind)?total:0;
  const fill=current.kind==='fill'?clamp(u):['mold-cure','postcure','compare'].includes(current.kind)?1:0;
  return {temperature,total,time,fill,fillTime:fill*data.fill.muf.fill_time_s,capillary_s:data.fill.muf.layers[0].capillary_fill_time_s};
}
export function valueAt(points,time){
  if(!points.length)return 0;
  if(time<points[0][0])return points[0][1];
  const exact=points.findLast(point=>point[0]===time);if(exact)return exact[1];
  for(let i=1;i<points.length;i++){const [t,b]=points[i],[a,v]=points[i-1];if(time<=t)return t===a?b:v+(b-v)*(time-a)/(t-a);}
  return points.at(-1)[1];
}
// Category labels are presentation translations; provenance always comes from params.kind.
const KIND_LABELS=Object.freeze({literature:'문헌값',design:'설계값',assumption:'가정값',midterm:'중간 보고서값',observation:'관찰 항목',estimate:'역산 추정값',kpi:'원문 KPI'});
export function parameterCategory(...entries){
  return [...new Set(entries.map(entry=>{
    if(!KIND_LABELS[entry?.kind])throw Error(`알 수 없는 params kind: ${entry?.kind}`);
    return KIND_LABELS[entry.kind];
  }))].join(' / ');
}
export function lightCategories(p){
  return {
    head:parameterCategory(p.tcncf_process.head_setpoint),
    force:parameterCategory(p.tcncf_process.bond_force),
    liquidus:parameterCategory(p.solder.liquidus_snag),
    time:parameterCategory(...['approach_time','hold_time','cool_time'].map(key=>p.tcncf_process[key])),
    reflow:parameterCategory(...Object.values(p.reflow)),
    shoulder:parameterCategory(p.thermal_stack.reflow_shoulder_temp)
  };
}
const fmt=n=>Number(n.toFixed(1)).toString();
const text=(x,y,label,extra='')=>`<text x="${x}" y="${y}" ${extra}>${label}</text>`;
function chart(curves,total,max,time,{liquidus=null,forceMax=null}={}){
  const x=t=>65+t/(total||1)*465,y=v=>145-v/max*90;
  let svg='';
  for(const v of [0,max/2,max])svg+=`<path d="M65 ${y(v)}H530" class="grid"/>${text(49,y(v)+8,fmt(v),'text-anchor="end"')}`;
  svg+=text(65,27,'온도 (℃)')+text(300,212,'시간 (s)','text-anchor="middle"');
  for(const t of niceTicks(total))svg+=text(x(t),180,t,`text-anchor="${t===0?'start':t===total?'end':'middle'}"`);
  if(forceMax)svg+=text(595,27,'하중 (N)','text-anchor="end"')+text(552,63,fmt(forceMax))+text(552,145,'0');
  if(liquidus!==null){
    // Linear crossing locations are derived from the sequence profile endpoints.
    const pts=curves[0].points;
    for(let i=1;i<pts.length;i++){let [a,ta]=pts[i-1],[b,tb]=pts[i];if(ta<=liquidus&&tb<=liquidus)continue;
      if(ta<liquidus)a+=(b-a)*(liquidus-ta)/(tb-ta);
      else if(tb<liquidus)b=a+(b-a)*(liquidus-ta)/(tb-ta);
      svg+=`<rect x="${x(a)}" y="55" width="${Math.max(0,x(b)-x(a))}" height="90" fill="#E6ECF3"/>`;
    }
    svg+=`<path d="M65 ${y(liquidus)}H530" stroke="#7A8899" stroke-dasharray="6 5"/>${text(520,y(liquidus)-7,`${fmt(liquidus)} ℃`,'text-anchor="end"')}`;
  }
  for(const c of curves){const cy=v=>c.force?145-v/forceMax*90:y(v);svg+=`<polyline points="${c.points.map(([t,v])=>`${x(t)},${cy(v)}`).join(' ')}" fill="none" stroke="${c.color}" stroke-width="3" ${c.dash?'stroke-dasharray="8 5"':''}/><circle cx="${x(time)}" cy="${cy(valueAt(c.points,time))}" r="5" fill="${c.color}"/>`;}
  return svg+`<path d="M${x(time)} 50V145" stroke="#14365A" stroke-width="2" stroke-dasharray="3 4"/>`;
}
function filmSection(kind,u){
  const squeeze=filmSqueezeAt(kind,u),h=30*squeeze.thickness,w=270*squeeze.spread;
  // Both halves use the same callout layout. The stack rests on stack_chuck
  // in factory_viewer, so the grey support represents the stacking chuck.
  const half=(offset,after)=>{
    const cx=255,thickness=after?h:30,width=after?w:270,top=240-thickness;
    const bumpY=top-10,filmY=top+thickness/2;
    return `<g transform="translate(${offset} 0)"><rect x="120" y="${top-85}" width="270" height="65" rx="4" fill="#14365A"/><rect x="${cx-width/2}" y="${top}" width="${width}" height="${thickness}" fill="#F2A66E"/>${[-80,0,80].map(dx=>`<rect x="${cx+dx-16}" y="${top-20}" width="32" height="${thickness+25}" rx="5" fill="#7A8899"/>`).join('')}<rect x="120" y="240" width="270" height="65" fill="#14365A"/><rect x="100" y="305" width="310" height="30" fill="#C9D0D8"/>
      <g fill="none" stroke="#7A8899" stroke-width="2"><path d="M100 ${top-52}H135M100 275H135M90 325H115M410 ${bumpY-20}H397L335 ${bumpY}M410 ${filmY+20}H402L${cx+width/2-5} ${filmY}"/></g>
      ${text(5,top-44,'위 칩')}${text(5,283,'아래 칩')}${text(5,333,'적층 척')}${text(415,bumpY-12,'범프')}${text(415,filmY+28,'NCF 필름')}</g>`;
  };
  return `<svg viewBox="0 0 1100 430" role="img" aria-label="NCF 필름 가압 전후 개념 단면도">${text(30,50,'필름 가압 · 개념도')}${text(255,100,'눌리기 전','text-anchor="middle"')}${text(805,100,'눌린 후','text-anchor="middle"')}${half(0,false)}${half(550,true)}${text(550,410,'두께·퍼짐·간격은 표시 설정 · 치수 아님','text-anchor="middle"')}</svg>`;
}
export function createLightPanel(container,viewerContainer,data,results){
  const recipe=lightRecipe(results),p=data.params,liquidus=p.solder.liquidus_snag.value,categories=lightCategories(p);
  const panel=document.createElement('section');panel.className='light-graphs';panel.setAttribute('aria-label','실시간 공정 그래프');container.append(panel);
  const film=document.createElement('div');film.className='light-film';film.hidden=true;viewerContainer.append(film);
  let cacheKey='',cached=null;
  return {showPanel(value){
    if(typeof value!=='boolean')throw TypeError('panel: boolean');
    panel.hidden=!value;container.classList.toggle('light-panel-hidden',!value);
  },update(stages,s,u,camera){
    const tc=s.mode==='TC-NCF',key=`${s.mode}-${s.layer}-${stages[0].duration_s}`;
    if(key!==cacheKey){cached=tc?tcPlot(data,recipe,stages,s,u):null;cacheKey=key;}
    let body;
    if(tc){
      const plot=cached,parts=stages.filter(part=>part.layer===plot.layer&&['ramp','hold','cool'].includes(part.kind));
      const time=parts.some(part=>part.id===s.id)?stageCursor(parts,s,u):['rise','compare'].includes(s.kind)?plot.total:0;
      const max=Math.max(...recipe.head_setpoints_C,liquidus),y=v=>145-v/max*100;
      const barSVG=layerBars(recipe,s,liquidus).map((b,i)=>{const x=95+i*37;return `<rect x="${x}" y="${y(b.peak_C)}" width="27" height="${145-y(b.peak_C)}" fill="${b.color}" stroke="${b.layer===s.layer?'#44505F':'none'}" stroke-width="3" data-layer="${b.layer}"/>${text(x+13,174,b.layer,'text-anchor="middle"')}${text(x+13,205,b.reheat_count,'text-anchor="middle"')}`;}).join('');
      body=`<h2>층별 열압착 · ${plot.layer}층</h2><p class="light-key"><span>━ 헤드 <small>${categories.head}</small></span><span class="force-key">┄ 하중 <small>${categories.force}</small></span><span class="temp-key">━ 층 <small>S1</small></span></p><svg preserveAspectRatio="none" viewBox="0 0 600 220" role="img" aria-label="현재 층 시간별 온도와 하중">${chart([{points:plot.head,color:'#14365A'},{points:plot.force,color:'#7A8899',force:true,dash:true},{points:plot.temperature,color:'#C2622A'}],plot.total,max,time,{forceMax:p.tcncf_process.bond_force.value})}</svg><h3>층별 최고 온도</h3><p><span class="badge">S1 계산 · 실측 아님</span> <span class="badge">${categories.liquidus} · 액상선</span> <span class="badge">${categories.time} · 시간</span></p><svg preserveAspectRatio="none" viewBox="0 0 600 215" role="img" aria-label="현재 단계까지의 층별 최고 온도 및 후속 재가열 횟수">${[0,max].map(v=>text(55,y(v)+8,fmt(v),'text-anchor="end"')).join('')}${text(65,28,'온도 (℃)')}${barSVG}<path d="M65 ${y(liquidus)}H540" stroke="#7A8899" stroke-width="2" stroke-dasharray="6 5"/>${text(535,y(liquidus)-9,`${liquidus} ℃`,'text-anchor="end"')}${text(570,174,'층')}${text(5,205,'재가열')}</svg><p class="light-note">위층을 붙이며 더 받은 열 횟수</p>`;
    }else{
      const plot=mrPlot(data,stages,s,u);
      body=`<h2>일괄 접합 · 충전</h2><p><span class="badge">${categories.reflow} · 리플로우</span> <span class="badge">${categories.shoulder} · shoulder</span></p><svg preserveAspectRatio="none" viewBox="0 0 600 220" role="img" aria-label="리플로우 프로파일 및 액상선 위 구간">${chart([{points:plot.temperature,color:'#14365A'}],plot.total,p.reflow.peak_temp.value,plot.time,{liquidus})}</svg><p>음영: 액상선 위 구간</p><h3>가압 충전 진행률</h3><p><span class="badge">S5 계산 결과 · 가정 입력</span></p><strong class="light-fill">${fmt(plot.fill*100)} %</strong><progress max="1" value="${plot.fill}" aria-label="충전 시간 진행률"></progress><p>${fmt(plot.fillTime)} / ${fmt(data.fill.muf.fill_time_s)} s</p><p>모세관 충전 시간 ${fmt(plot.capillary_s)} s</p><p class="light-note">S5 가압 충전 시간 기준 경과율<br>유동 선단 길이와 구분</p>`;
    }
    panel.classList.toggle('light-tc',tc);
    panel.innerHTML=body;
    film.hidden=!(tc&&camera===4&&['ramp','hold','cool'].includes(s.kind));if(!film.hidden)film.innerHTML=filmSection(s.kind,u);
  }};
}
