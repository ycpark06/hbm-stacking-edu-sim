import {MODES,DISPLAY,readFactoryData,buildStages,sampleStage} from './factory_sequence.js';
import {createFactoryViewer} from './factory_viewer.js';
const $=id=>document.getElementById(id),fmt=(v,d=1)=>Number(v).toLocaleString('ko-KR',{maximumFractionDigits:d});
const kinds={design:'설계값',literature:'문헌값',assumption:'가정값',midterm:'중간 보고서값',kpi:'원문 KPI',inferred:'역산 추정값'};
const badge=q=>`<span class="badge">${kinds[q.kind]||q.kind}</span>`;
async function json(path){const response=await fetch(path);if(!response.ok)throw Error(`${path}: HTTP ${response.status}`);return response.json();}
try {
  const [params,results]=await Promise.all([json('../sim/params.json'),json('../sim/test/stage4_results.json')]);
  const data=readFactoryData(params,results),p=params,q=p.tcncf_process;
  let mode=MODES[0],seconds=DISPLAY.totalSeconds,stages=buildStages(data,mode,seconds),index=0,elapsed=0,playing=false,speed=1,camera=1,viewOnly=false;
  const listeners=new Set();
  const viewer=createFactoryViewer($('viewer'),data,status=>$('model-status').textContent=status);
  const refs=['tcncf_process.bond_force','tcncf_process.head_setpoint','tcncf_process.ramp_rate','tcncf_process.hold_time','tcncf_process.cool_time','mrmuf_process.tack_force','mrmuf_process.tack_temp','mrmuf_process.tack_time','muf.applied_pressure','mrmuf_process.mold_pressure_applied','muf.cure_temp','muf.cure_time'];
  $('sources').innerHTML=refs.map(key=>{const entry=key.split('.').reduce((a,k)=>a[k],p);return `<p><code>${key}</code><br>${entry.value??entry.equipment_value} ${entry.unit} ${badge(entry)}</p>`;}).join('');
  $('temp-meter').max=p.equipment_limits.head_max_temp_C.value;$('force-meter').max=p.equipment_limits.bond_force_max_N.value;
  $('recipe-info').innerHTML=`${data.layers}단 <span class="badge">S1·S4 조건</span><br>다이 ${p.geometry.die_size.value} mm / 두께 ${p.geometry.die_thickness.value} μm / 간격 ${p.geometry.interlayer_gap.value} μm<br>승온 ${q.ramp_rate.equipment_value} K/s ${badge(q.ramp_rate)}<br>유지 ${q.hold_time.value} s ${badge(q.hold_time)} / 냉각 ${q.cool_time.value} s ${badge(q.cool_time)}`;
  $('pressure').innerHTML=`입구 ${p.muf.applied_pressure.value} MPa ${badge(p.muf.applied_pressure)}<br>금형 ${p.mrmuf_process.mold_pressure_applied.value} MPa ${badge(p.mrmuf_process.mold_pressure_applied)}`;
  const cap=data.fill.muf.layers[0].capillary_fill_time_s,pressure=data.fill.muf.fill_time_s;
  $('fill-info').innerHTML=`간격 ${data.fill.recipe.gap_um} μm: 모세관 ${fmt(cap,0)} s / 가압 ${fmt(pressure)} s <span class="badge">S5 계산 결과</span>`;
  $('profile-info').textContent=`피크 ${p.reflow.peak_temp.value} ℃ · 예열 ${p.reflow.preheat_start.value}→${p.reflow.preheat_end.value} ℃ / ${p.reflow.soak_time.value} s · 승온 ${p.reflow.ramp_up.value} K/s · 냉각 ${p.reflow.ramp_down.value} K/s · 액상선 위 ${p.reflow.time_above_liquidus.value} s / 피크 유지 ${p.reflow.time_near_peak.value} s (문헌; shoulder 체류 구성은 가정)`;
  const max=Math.max(data.tc.cycle.bonder_s,data.mr.cycle.bonder_s);
  const bar=(name,val,limit,cls='')=>`<div class="bar-row"><span>${name}</span><div class="bar-track"><div class="bar ${cls}" style="width:${100*val/limit}%"></div></div><strong>${fmt(val,0)} s</strong></div>`;
  $('bars').innerHTML=`<figure><figcaption>본더 점유 · 축 0–${fmt(max,0)} s</figcaption>${bar('TC-NCF',data.tc.cycle.bonder_s,max)}${bar('MR-MUF',data.mr.cycle.bonder_s,max,'mr')}</figure><figure><figcaption>MR-MUF 배치 후공정 · 별도 축 0–${fmt(data.mr.cycle.batch_post_s,0)} s</figcaption>${bar('MR-MUF',data.mr.cycle.batch_post_s,data.mr.cycle.batch_post_s,'post')}<p class="small">후경화 ${p.muf.cure_time.value} h 포함 · ${p.muf.cure_temp.value} ℃ ${badge(p.muf.cure_time)}</p></figure><p class="small">실제 ${fmt(data.tc.cycle.bonder_s,0)} s는 화면 본더 장면에 나누어 표시합니다. 두 그림의 막대 길이는 서로 비교하지 않습니다.</p>`;
  const profileTotal=data.profile.reduce((a,s)=>a+s.duration_s,0),peak=p.reflow.peak_temp.value;
  const x=t=>38+t/profileTotal*540,y=t=>156-t/peak*130;
  let t=0,points=[];for(const segment of data.profile){points.push(`${x(t)},${y(segment.input(0).T_chuck_C)}`);t+=segment.duration_s;points.push(`${x(t)},${y(segment.input(segment.duration_s).T_chuck_C)}`);}
  $('profile').innerHTML=`<path d="M38 18V156H580" fill="none" stroke="#607985"/><polyline points="${points.join(' ')}" fill="none" stroke="#c5f17b" stroke-width="3"/><text x="5" y="20" fill="#cadadc" font-size="12">${peak} ℃</text><text x="38" y="179" fill="#cadadc" font-size="12">0</text><text x="490" y="179" fill="#cadadc" font-size="12">${fmt(profileTotal)} s</text><circle id="profile-dot" cx="38" cy="156" r="5" fill="#f4b16e"/>`;
  function choices(){ $('stage').replaceChildren(...stages.map((s,i)=>new Option(`${i} · ${s.title}`,i)));$('stage').value=index; }
  function state(){const stage=stages[index];return {ready:true,mode,stage:index,id:stage.id,title:stage.title,elapsed_s:elapsed,stage_progress:elapsed/stage.duration_s,playing,speed,camera,viewOnly,screen_duration_s:seconds,complete:index===stages.length-1&&elapsed===stage.duration_s};}
  function notify(){const snapshot=Object.freeze(state());for(const cb of listeners){try{cb(snapshot);}catch(error){console.error('factory.onStage callback',error);}}}
  function draw(){const s=stages[index],v=sampleStage(data,s,elapsed/s.duration_s);
    viewer.update(s,v);$('stage').value=index;$('caption').textContent=s.title;$('stage-number').textContent=`${mode} / ${index+1} of ${stages.length}`;
    const before=stages.slice(0,index).reduce((a,s)=>a+s.duration_s,0);$('progress').value=(before+elapsed)/seconds;$('clock').textContent=`화면 ${fmt(before+elapsed)} / ${seconds} s · ${speed}×${playing?' 재생 중':' 일시정지'}`;
    $('timing').textContent=s.real_duration_s>0?`실제 ${fmt(s.real_duration_s,3)} s → 화면 ${fmt(s.duration_s,2)} s (${fmt(s.real_duration_s/s.duration_s,2)}:1, ${speed}×에서 ${fmt(s.duration_s/speed,2)} s) · 실제 시간이 아닌 압축·확대 표시`:`표시 연출 ${fmt(s.duration_s,2)} s · 이 장면의 별도 실제 공정 시간은 산정하지 않음`;
    $('station').textContent=['reflow','to-reflow'].includes(s.kind)?'리플로우 척':['to-mold','dispense','fill','mold-cure','postcure'].includes(s.kind)?'가압 충전 지그':'적층 스테이션';
    $('temperature').textContent=`${fmt(v.temp)} ℃`;$('temp-meter').value=v.temp;$('force').textContent=`${fmt(v.force)} N`;$('force-meter').value=v.force;
    const thermal=s.kind==='reflow'?p.reflow.peak_temp:s.kind==='postcure'?p.muf.cure_temp:['dispense','fill','mold-cure'].includes(s.kind)?p.mrmuf_process.mold_fill_temp:mode===MODES[0]?q.head_setpoint:p.mrmuf_process.tack_temp;
    $('temp-label').textContent=s.kind==='reflow'?'척 프로파일 설정':['dispense','fill','mold-cure','postcure'].includes(s.kind)?'경화·금형 설정':'헤드 설정';$('temp-source').innerHTML=badge(thermal);$('force-source').innerHTML=badge(mode===MODES[0]?q.bond_force:p.mrmuf_process.tack_force);
    $('layer-label').textContent=`완료 ${v.count}/${data.layers}층 · 스택 ${camera===3?DISPLAY.stackMagnification:7}× / 간격 추가 ${DISPLAY.gapMagnification}× 확대`;
    $('reheats').textContent=mode===MODES[0]?`최하부 층 후속 재가열 ${v.reheats}/${data.layers-1}회 (N−1). 재용융 횟수와 다름.`:'가접은 작은 하중·순간 가열(가정값). 리플로우 중 자기정렬은 개념 표시.';
    const fillTime=s.kind==='fill'?v.u*pressure:['mold-cure','postcure','compare'].includes(s.kind)&&mode===MODES[1]?pressure:0;
    $('capillary').value=Math.min(1,Math.sqrt(fillTime/cap));$('pressured').value=Math.min(1,Math.sqrt(fillTime/pressure));
    let time=0;if(s.kind==='reflow')time=data.profile.slice(0,s.segment).reduce((a,s)=>a+s.duration_s,0)+v.u*s.real_duration_s;
    else if(['to-mold','dispense','fill','mold-cure','postcure','compare'].includes(s.kind)&&mode===MODES[1])time=profileTotal;
    const segment=s.kind==='reflow'?data.profile[s.segment]:null;
    $('profile-dot').setAttribute('cx',x(time));$('profile-dot').setAttribute('cy',y(segment?v.temp:p.thermal_stack.ambient_temp.value));
    $('comparison').classList.toggle('active-comparison',s.kind==='compare');
  }
  function setMode(m){if(!MODES.includes(m))throw RangeError('mode');mode=m;stages=buildStages(data,mode,seconds);index=0;elapsed=0;playing=false;$('mode').value=mode;choices();draw();notify();return state();}
  function setStage(n,fraction=0){const i=typeof n==='string'?stages.findIndex(s=>s.id===n):n;if(!Number.isInteger(i)||i<0||i>=stages.length||!Number.isFinite(fraction)||fraction<0||fraction>1)throw RangeError('stage / fraction');index=i;elapsed=stages[i].duration_s*fraction;draw();notify();return state();}
  function play(){if(state().complete)setStage(0);playing=true;draw();return state();}
  function pause(){playing=false;draw();return state();}
  function setSpeed(x){if(![.5,1,2].includes(x))throw RangeError('speed');speed=x;$('speed').value=x;draw();return state();}
  function setCamera(k){if(![1,2,3].includes(Number(k)))throw RangeError('camera');camera=Number(k);viewer.setCamera(camera);$('camera').value=camera;draw();return state();}
  function setViewOnly(value){if(typeof value!=='boolean')throw TypeError('viewOnly: boolean');viewOnly=value;document.body.classList.toggle('view-only',value);return state();}
  await viewer.ready;
  window.factory={setMode,setStage,play,pause,setSpeed,setCamera,setViewOnly,stages:()=>stages.map(s=>({...s})),onStage(cb){if(typeof cb!=='function')throw TypeError('callback');listeners.add(cb);return ()=>listeners.delete(cb);},state};
  choices();draw();['play','pause','stage'].forEach(id=>$(id).disabled=false);
  $('play').onclick=play;$('pause').onclick=pause;$('mode').onchange=e=>setMode(e.target.value);$('stage').onchange=e=>setStage(Number(e.target.value));$('speed').onchange=e=>setSpeed(Number(e.target.value));$('camera').onchange=e=>setCamera(e.target.value);
  $('length').onchange=e=>{seconds=Number(e.target.value);stages=buildStages(data,mode,seconds);elapsed=0;choices();draw();notify();};
  document.addEventListener('keydown',e=>{if(e.target.closest('input,select,textarea,button,summary')||e.ctrlKey||e.metaKey||e.altKey)return;if(['1','2','3'].includes(e.key))setCamera(e.key);if(e.code==='Space'){e.preventDefault();playing?pause():play();}});
  let last=performance.now();
  function frame(now){const dt=Math.min((now-last)/1000,.1);last=now;if(playing){elapsed+=dt*speed;while(elapsed>=stages[index].duration_s){if(index===stages.length-1){elapsed=stages[index].duration_s;playing=false;break;}elapsed-=stages[index].duration_s;index++;notify();}draw();}viewer.render(now);requestAnimationFrame(frame);}
  requestAnimationFrame(frame);window.dispatchEvent(new Event('factory-ready'));
} catch(error){console.error(error);$('caption').textContent=`초기화 실패 · ${error.message}`;$('model-status').textContent='데이터·GLB 경로 확인 필요';$('timing').textContent='저장소 루트에서 HTTP 서버를 열고 web/factory.html에 접속하세요. 배포본에는 sim/test/stage4_results.json 복사가 필요합니다.';}
