import {validateRecipe} from './recipe_limits.js';
import {chart} from './charts.js';
import {createAlarmDemo} from './alarms.js';
import {esc,labels,badge,fmt,value,resultTitle,mufRows,s5Table,displaySettings} from './hmi_display.js';
const $=id=>document.getElementById(id);
let p,worker,viewer,results=[],currentId=0,sil=null,demo;
let getRecipe=()=>({});
const showError=message=>{$('recipe-error').textContent=message;};
function busy(on){document.querySelectorAll('#run,#presets button').forEach(b=>b.disabled=on);}
function listParams(node,prefix=''){
  return Object.entries(node).flatMap(([k,v])=>k==='_meta'?[]:v&&typeof v==='object'&&('value'in v||'equipment_value'in v)?[[prefix+k,v]]:listParams(v,prefix+k+'.'));
}
function source(s){
  const pattern=/https?:\/\/[^\s;]+|\b(?:docs|calc|firmware)\/[^\s;:)]+\.(?:md|py|json)/g;
  let end=0,html='';
  for(const match of String(s).matchAll(pattern)){
    html+=esc(s.slice(end,match.index));const path=match[0];
    const url=path.startsWith('http')?path:`https://github.com/ycpark06/hbm-stacking-edu-sim/blob/main/${path}`;
    html+=`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(path)}</a>`;end=match.index+path.length;
  }
  return html+esc(s.slice(end));
}

function renderParams(){
  const query=$('search').value.toLowerCase();
  $('params').innerHTML=listParams(p).filter(([k,v])=>`${k} ${JSON.stringify(v)} ${labels[v.kind]}`.toLowerCase().includes(query)).map(([k,v])=>`<tr><td>${esc(k)}</td><td>${value(v.value??v.equipment_value,v.unit,v.kind)}</td><td>${source(v.source)}</td></tr>`).join('');
}
function setUpForm(){
  const e=p.equipment_limits;
  const fields=[
    ['mode','모드',null,['TC-NCF','MR-MUF'],'TC-NCF'],
    ['layers','층 수',p.recipe.layers,[2,4,8,12],p.recipe.layers.value],
    ['thickness_um','두께 (μm)',p.geometry.die_thickness,[100,50],p.geometry.die_thickness.value],
    ['gap_um','간격 (μm) · 시험 칩 선택 가능',p.geometry.interlayer_gap,null,p.geometry.interlayer_gap.value],
    ['bond_force_N','하중 (N)',p.tcncf_process.bond_force,null,p.tcncf_process.bond_force.value],
    ['head_temp_C','헤드 설정 (℃) · TC-NCF',p.tcncf_process.head_setpoint,null,p.tcncf_process.head_setpoint.value],
    ['inlet_pressure_MPa','입구 압력 (MPa) · MR-MUF',p.muf.applied_pressure,null,p.muf.applied_pressure.value],
    ['ramp_K_s','승온 (K/s) · TC-NCF',p.tcncf_process.ramp_rate,null,p.tcncf_process.ramp_rate.equipment_value],
    ['force_ramp_N_s','SIL 하중 램프 (N/s)',e.force_high_ramp_N_s,null,e.force_high_ramp_N_s.value],
  ];
  $('fields').innerHTML=fields.map(([key,label,meta,options,def])=>`<label>${esc(label)} ${meta?badge(meta.kind):''}${options?`<select name="${key}">${options.map(v=>`<option ${v===def?'selected':''}>${esc(v)}</option>`).join('')}</select>`:`<input name="${key}" type="number" step="any" value="${def}" required ${key==='gap_um'?'list="gaps"':''}>`}</label>`).join('')+`<label class="check"><input name="low_range" type="checkbox"> SIL 저레인지 ${badge('design')}</label><datalist id="gaps"><option value="${p.geometry.interlayer_gap.value}"><option value="20" label="시험 칩"></datalist>`;
  const form=$('recipe');
  getRecipe=()=>{const data=new FormData(form),r={};for(const [k]of fields)r[k]=k==='mode'?data.get(k):Number(data.get(k));r.head_temp_compensation=data.has('head_temp_compensation');r.low_range=data.has('low_range');return r;};
  $('limits').innerHTML=`입력 한계: 하중 ${value(e.bond_force_max_N.value,'N',e.bond_force_max_N.kind)}, 헤드 ${value(e.head_max_temp_C.value,'℃',e.head_max_temp_C.kind)}, 승온 ${value(p.tcncf_process.ramp_rate.equipment_value,'K/s',p.tcncf_process.ramp_rate.kind)}, 저레인지 램프 ${value(e.low_range_ramp_N_s.value,'N/s',e.low_range_ramp_N_s.kind)}, 간격 ${value(p.geometry.interlayer_gap.range.join('–'),'μm',p.geometry.interlayer_gap.kind)}. 압력 0은 모세관 단독 비교입니다. MR-MUF의 온도는 params 리플로우 프로파일을 사용합니다.`;
  form.addEventListener('input',()=>showError(validateRecipe(getRecipe(),p).join('\n')));
  form.addEventListener('submit',event=>{event.preventDefault();const r=getRecipe(),errors=validateRecipe(r,p);showError(errors.join('\n'));if(!errors.length)start({recipe:r});});
  $('presets').innerHTML=['열 이력','정렬','박형 다이','처리량','가압 충전'].map((name,i)=>`<button type="button" data-scenario="S${i+1}">S${i+1} ${name}</button>`).join('');
  $('presets').addEventListener('click',event=>{const id=event.target.dataset.scenario;if(id)start({scenario:id});});
}
function start(payload){
  busy(true);sil=null;viewer?.reset();$('progress').value=0;$('model-alarms').replaceChildren();
  $('status').textContent='Worker 계산 시작…';document.body.dataset.hmiState='running';
  worker.postMessage({id:++currentId,params:p,...payload});
}
function renderResults(){
  $('results').innerHTML=results.map((r,i)=>{
    const title=resultTitle(r);
    if(r.accepted===false)return `<article class="result"><h3>${esc(title)} ${badge('demo')}</h3><p class="alarm">HEAD_TEMP_LIMIT · ${esc(r.rejection.reason)}<br>층 ${value(r.rejection.layer)} · 필요 ${value(r.rejection.required_head_C,'℃')} · 한계 ${value(r.rejection.limit_C,'℃','kpi')}</p></article>`;
    const layers=r.thermal?.layers??r.thermal_layers;
    const row=(name,v,unit='')=>`<dt>${esc(name)}</dt><dd>${value(v,unit)}</dd>`;
    return `<article class="result"><h3>${esc(title)} ${badge('demo')}</h3><dl>${row('최대 절대 휨',r.warpage.max_um,'μm')}<dt>휨 / 결함 / 정렬 판정</dt><dd>${esc(r.warpage.judgement)} / ${esc(r.defect_judgement)} / ${esc(r.alignment.judgement)}</dd>${row('미충전 면적률',r.defect_area_pct,'%')}${mufRows(r)}${row('본더 점유',r.cycle.bonder_s,'s')}${row('배치 후공정',r.cycle.batch_post_s,'s')}${row('누적 정렬 X / Y',r.alignment.cumulative_um.map(fmt).join(' / '),'μm')}${r.warpage.thickness_half_ratio?row('두께 절반의 휨 증가 배율',r.warpage.thickness_half_ratio,'배'):''}</dl><details><summary>층별 접합·재가열·재용융</summary><table><thead><tr><th>층</th><th>자기 접합 최고 ℃</th><th>헤드 설정 ℃</th><th>재가열 / 액상선 교차 / 후속 재용융</th></tr></thead><tbody>${layers.map((l,j)=>`<tr><td>${value(j+1)}</td><td>${value(l.bond_peak_C,'℃')} ${l.bond_temp_ok?'접합 온도 충족':'BOND_TEMP_LOW · 접합 온도 미달'}</td><td>${value(l.head_setpoint_C,'℃')}</td><td>${value(`${l.reheat_count} / ${l.remelt_count} / ${l.subsequent_remelts}`)}</td></tr>`).join('')}</tbody></table></details><details><summary>사이클 시간 분해</summary>${Object.entries(r.cycle.breakdown.layer_totals).map(([k,v])=>`<p>${esc(k)} ${value(v,'s')}</p>`).join('')}${Object.entries(r.cycle.breakdown.once).map(([k,v])=>`<p>${esc(k)} ${value(v,'s')}</p>`).join('')}</details>${r.model_limit?`<p>${esc(r.model_limit)}</p>`:''}</article>`;
  }).join('');
  $('result-choice').innerHTML=results.map((r,i)=>`<option value="${i}">${esc(r.recipe.mode)} ${r.recipe.head_temp_compensation?'보정':''} · ${r.recipe.thickness_um} μm · ${r.recipe.gap_um} μm · ${r.recipe.inlet_pressure_MPa} MPa (입력값)</option>`).join('');
  $('s5').innerHTML=results.length>4?s5Table(results):'';
  $('model-alarms').innerHTML=results.flatMap(r=>[
    ...(r.alarms??[]).map(a=>`<p class="alarm">${esc(r.recipe.mode)} · ${esc(a.code)} ${esc(a.message)} · 층 ${value(a.layer)} · 접합 ${value(a.peak_C,'℃')} · 부족 ${value(a.shortfall_C,'℃')}</p>`),
    ...(r.accepted===false?[`<p class="alarm">HEAD_TEMP_LIMIT · 층 ${value(r.rejection.layer)} · 필요 ${value(r.rejection.required_head_C,'℃')}</p>`]:[
      `<p>${esc(r.recipe.mode)} · 휨 ${esc(r.warpage.judgement)} · 결함 ${esc(r.defect_judgement)} · 접촉 ${esc(r.contact_judgement)} ${badge('result')}</p>`,
      ...(r.muf?.warnings??[]).map(w=>`<p class="alarm">${esc(w)}</p>`),
    ])]).join('');
  drawCharts();
}
const chartTitles=['층별 온도–시간','하중–시간 · 독립 SIL','층별 최대 절대 휨','충전 전선 위치–시간','층별 미충전률','누적 정렬 오차','본더 / 배치 시간 분해'];
function initCharts(){$('charts').innerHTML=chartTitles.map((title,i)=>`<figure><figcaption>${title} ${badge('result')}</figcaption><canvas id="chart-${i}" role="img"></canvas><p class="legend"></p></figure>`).join('');}
function drawCharts(){
  const r=results[Number($('result-choice').value)||0];if(!r||r.accepted===false){initCharts();return;}
  const plot=(i,s,opts)=>chart($(`chart-${i}`),s,opts),history=r.thermal?.history??[];
  plot(0,Array.from({length:r.recipe.layers},(_,i)=>({name:`층 ${i+1}`,points:history.filter(h=>h.T[i]!==undefined).map(h=>[h.t_s,h.T[i]])})),{xLabel:'시간 (s)',yLabel:'온도 (℃)',lines:[{value:p.solder.liquidus_snag.value,label:`액상선 ${p.solder.liquidus_snag.value} ℃ · ${labels[p.solder.liquidus_snag.kind]}`}]});
  plot(1,sil?[{name:'측정 하중',points:sil.t.map((t,i)=>[t,sil.F[i]])},{name:'설정 하중',points:sil.t.map((t,i)=>[t,sil.sp[i]])}]:[],{xLabel:'시간 (s)',yLabel:'하중 (N)'});
  const wh=r.warpage.history??[],maxByLayer=Array.from({length:r.recipe.layers},(_,i)=>{const rows=wh.filter(h=>h.layer_count===i+1);return [i+1,rows.length?Math.max(...rows.map(h=>Math.abs(h.w_um))):NaN];});
  plot(2,[{name:'해당 적층 층수에서 최대 절대 휨',points:maxByLayer}],{xLabel:'적층 층수',yLabel:'휨 (μm)',lines:[{value:r.recipe.gap_um*p.judgement.warpage_caution_ratio.value,label:'주의 · 설계 목표'},{value:p.judgement.warpage_fail_um.value,label:'불량 · 설계 목표'}]});
  const fill=r.muf?.layers??[];
  plot(3,fill.map(l=>({name:`층 ${l.layer}`,points:Array.from({length:101},(_,i)=>{const t=r.muf.mold_fill_time_s*i/100;return [t,Math.min(1,Math.sqrt(t/l.fill_time_s))*l.L_m*1000];})})),{xLabel:'충전 시간 (s)',yLabel:'전선 (mm)'});
  plot(4,fill.length?[{name:'미충전 면적률',points:fill.map(l=>[l.layer,100*l.unfilled_fraction])}]:[],{xLabel:'층',yLabel:'미충전 (%)'});
  let positions=r.alignment.positions_um;if(!positions){positions=[];for(const xy of r.alignment.layer_errors_um)positions.push(xy.map((v,j)=>v+(positions.at(-1)?.[j]??0)));}
  plot(5,[0,1].map(j=>({name:j?'Y':'X',points:positions.map((xy,i)=>[i+1,xy[j]])})),{xLabel:'층',yLabel:'누적 오차 (μm)'});
  const breakdown=[...Object.entries(r.cycle.breakdown.layer_totals),...Object.entries(r.cycle.breakdown.once)];
  plot(6,breakdown.map(([name,v],i)=>({name,points:[[i+1,0],[i+1,v]]})),{xLabel:'분해 항목',yLabel:'시간 (s)',bars:true});
  viewer?.warp(r.warpage.max_um,Number($('warp-scale').value));
}
async function boot(){
  displaySettings(document);
  const response=await fetch('../sim/params.json');if(!response.ok)throw Error(`params HTTP ${response.status}`);p=await response.json();
  setUpForm();renderParams();initCharts();$('search').addEventListener('input',renderParams);$('result-choice').addEventListener('change',drawCharts);$('warp-scale').addEventListener('change',drawCharts);
  $('claims').innerHTML=Object.values(p.vendor_claims).map(c=>`<article><h3>${esc(c.company)}</h3><p>${value(c.value,c.unit,c.kind)} · 판정 없음</p><p>${esc(c.note)}</p><p>${source(c.source)}</p></article>`).join('');
  // A WebGL failure must not disable recipes, charts, or firmware alarms.
  import('./viewer.js').then(({createViewer})=>{try{viewer=createViewer($('viewer'),p,text=>$('model-state').textContent=text);}catch(error){$('model-state').textContent=`3D 사용 불가: ${error.message}`;}}).catch(error=>$('model-state').textContent=`3D 로드 실패: ${error.message}`);
  worker=new Worker(new URL('./worker.js',import.meta.url),{type:'module'});
  worker.onerror=event=>{busy(false);showError(`Worker 오류: ${event.message}`);document.body.dataset.hmiState='error';};
  worker.onmessage=({data})=>{if(data.id!==currentId)return;
    if(data.type==='status')$('status').textContent=data.message;
    if(data.type==='results'){results=data.results;$('description').textContent=data.description;renderResults();}
    if(data.type==='sil'){sil=data.sil;drawCharts();}
    if(data.type==='progress'){const e=data;$('progress').max=e.recipe.layers;$('progress').value=e.layer;$('status').innerHTML=`계산 완료 후 단계 재생 · 층 ${value(e.layer)} · ${esc(e.phase)}${e.t==null?'':` · ${value(e.t,'s')}`}`;viewer?.progress(e);$('vision-link').href=`vision.html?layer=${e.layer}`;}
    if(data.type==='done'){busy(false);$('status').textContent='계산 및 단계 재생 완료';document.body.dataset.hmiState='done';}
    if(data.type==='error'){busy(false);showError(data.message);$('status').textContent='실행 실패';document.body.dataset.hmiState='error';}
  };
  try {
    demo=await createAlarmDemo(p);const e=p.equipment_limits;
    const buttons=[['force-warning',`과하중 경고 ${e.force_warning_N.value} N`],['force-latch',`과하중 래치 ${e.force_latch_N.value} N`],['temp-warning',`과온 경고 ${e.temp_warning_C.value} ℃`],['temp-latch',`과온 래치 ${e.temp_latch_C.value} ℃`],['hardware','하드웨어 고장'],['heaters','헤드 통전 중 척 히터 요청'],['clear','고장 원인 해제'],['reset','수동 래치 리셋']];
    // Threshold provenance: equipment_limits.*.source and firmware/README.md §7 cite ch10 safety layers.
    $('fault-buttons').innerHTML=buttons.map(([action,label])=>`<button data-action="${action}">${esc(label)} ${badge(['force-warning','force-latch','temp-warning','temp-latch'].includes(action)?'midterm':'design')}</button>`).join('');
    const display=s=>$('firmware-status').innerHTML=`경고 ${value(s.warning)} · 래치 ${value(s.latched)} · ${s.dual_heater_blocked?'두 히터 동시 통전 금지 · 차단':'히터 충돌 없음'} ${badge('result')}<br>헤드 ${value(s.head_W,'W')} · 척 ${value(s.reflow_W,'W')} · 측정 하중 ${value(s.force_N,'N','demo')} · 측정 온도 ${value(s.temp_C,'℃','demo')}`;
    $('fault-buttons').addEventListener('click',event=>{const action=event.target.closest('button')?.dataset.action;if(action)display(demo.act(action));});display(demo.state());
  }catch(error){$('firmware-status').textContent=`wasm 알람 시연 사용 불가: ${error.message}`;}
  document.body.dataset.hmiReady='true';
}
boot().catch(error=>{showError(error.message);document.body.dataset.hmiState='error';});
