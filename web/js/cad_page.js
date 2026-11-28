import {setLightTitle} from './cad_light.js';
import {FOOTPRINT_LIMIT} from './cad_data.js';
import {GROUPS,groupParts,materialText,dimensionText} from './cad_parts.js';
const byId=id=>document.getElementById(id);
function el(tag,text,className){const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(className)node.className=className;return node;}
let viewer=null,selected='stack_chuck';
const visibility=new Map(Object.keys(GROUPS).map(id=>[id,true]));
const buttons=new Map(),checks=new Map();
function select(id){
  if(id==='all'){showAll();return;}
  if(!GROUPS[id])throw RangeError('unknown part group');
  selected=id;
  for(const [key,button] of buttons)button.setAttribute('aria-pressed',String(key===id));
  const panel=byId('part-info');panel.replaceChildren(el('h3',GROUPS[id].name),el('code',id),el('p',GROUPS[id].role));
  panel.append(el('p','역할 근거: 보고서 3.2·3.3 / 11.3절','source'));
  const wrap=el('div',undefined,'scroll part-table'),table=el('table');
  const caption=el('caption',`포함 부품 ${groupParts(id).length}개 · 설계 형상 치수`);table.append(caption);
  const tr=el('tr');for(const text of ['부품 · 재질','치수 · 근거 키'])tr.append(el('th',text));
  const thead=el('thead');thead.append(tr);table.append(thead);const body=el('tbody');
  for(const part of groupParts(id)){
    const row=el('tr'),name=el('td'),dimensions=el('td');
    name.append(el('strong',part.name),el('p',materialText(part)),el('span',part.kind,'badge'),el('p',part.materialSource,'source'));
    if(['Vacuum_Chuck_200C','Reflow_Plate','Mold_Block','Plunger','Quartz_Window'].includes(part.name))name.append(el('p','재질 등급: spec_stacker.py MATERIALS','source'));
    dimensions.append(el('p',dimensionText(part)),el('code',part.source),el('p',part.type==='box'?'원본 tuple [3:6]의 폭·깊이·높이':'원본 tuple의 반지름×2, z1−z0; 좌표를 치수와 구분','source'));
    row.append(name,dimensions);body.append(row);
  }
  table.append(body);wrap.append(table);panel.append(wrap);viewer?.select(id);
}
function showAll(){
  if(document.documentElement.dataset.theme!=='light')return;
  selected='all';
  for(const button of buttons.values())button.setAttribute('aria-pressed','false');
  for(const id of visibility.keys()){visibility.set(id,true);checks.get(id).checked=true;viewer?.setVisible(id,true);}
  byId('part-info').replaceChildren(el('h3','전체 색 보기'),el('p','색은 기능 구분용 표시 설정입니다. 치수·재질·운전 상태를 뜻하지 않습니다.'));
  viewer?.select('all');
}
for(const [id,group] of Object.entries(GROUPS)){
  const row=el('div',undefined,'part-row'),label=el('label'),check=el('input');check.type='checkbox';check.checked=true;check.setAttribute('aria-label',`${group.name} 보이기`);
  check.addEventListener('change',()=>{visibility.set(id,check.checked);viewer?.setVisible(id,check.checked);});label.append(check);
  const button=el('button',group.name);button.type='button';button.addEventListener('click',()=>select(id));buttons.set(id,button);checks.set(id,check);row.append(label,button);byId('part-list').append(row);
  const link=el('a',`${id}.stl`);link.href=`../cad/stacker/out/mesh/${id}.stl`;link.download='';byId('stl-links').append(link);
}
select(selected);
byId('explode').addEventListener('input',event=>{byId('explode-value').value=`${event.target.value}%`;viewer?.explode(Number(event.target.value)/100);});
byId('reset-view').addEventListener('click',()=>{
  byId('explode').value='0';byId('explode-value').value='0%';
  for(const id of visibility.keys()){visibility.set(id,true);checks.get(id).checked=true;viewer?.setVisible(id,true);}
  viewer?.explode(0);viewer?.reset();
});
async function loadSummary(){
  try{
    const response=await fetch('../cad/stacker/out/summary.json');if(!response.ok)throw new Error(`HTTP ${response.status}`);
    const s=await response.json();
    if(!Array.isArray(s.parts)||!Array.isArray(s.bbox_mm)||s.bbox_mm.length!==3)throw new Error('summary 형식 오류');
    const [x,y,z]=s.bbox_mm,limit=FOOTPRINT_LIMIT.value;
    const values=[
      ['부품 수',`${s.parts.length}개`,'모델 구성값','parts.length'],
      ['풋프린트',`${x} × ${y} mm`,'모델 구성값','bbox_mm[0:2]'],
      ['풋프린트 판정',`${x<=limit&&y<=limit&&s.footprint_KPI_pass?'충족':'검토 필요'} · 가로·세로 ≤ ${limit} mm`,'원문 KPI','footprint_KPI_pass; spec_stacker.py LIMITS.footprint'],
      ['형상 간섭',s.interference_count>=0?`${s.interference_count}건`:'검사 미완료','관찰 항목 · 저장 자세','interference_count'],
      ['높이',`${z} mm`,'참고값','bbox_mm[2]'],
      ['밀도 기반 질량',`${s.mass_kg} kg`,'참고값','mass_kg'],
      ['Fusion 재질 질량',`${s.fusion_mass_kg} kg`,'참고값 · 대체 재질 영향','fusion_mass_kg']
    ];
    byId('summary').replaceChildren(...values.map(([label,value,kind,key])=>{const card=el('article');card.append(el('h3',label),el('strong',value),el('span',kind,'badge'),el('p',`summary.json ${key}`,'source'));return card;}));
  }catch(error){byId('summary').replaceChildren(el('p',`실행 결과를 읽지 못했습니다 (${error.message}). 위 summary.json 링크에서 원본을 확인하세요.`,'alarm'));}
}
loadSummary();
// Keep the catalog and drawings usable even if WebGL or the 3D module fails.
try{
  const {createCADViewer}=await import('./cad_viewer.js');
  viewer=await createCADViewer(byId('cad-viewer'),select,message=>{byId('cad-status').textContent=message;});
  for(const [id,visible] of visibility)viewer.setVisible(id,visible);
  viewer.explode(Number(byId('explode').value)/100);viewer.select(selected);
}catch(error){byId('cad-status').textContent=`3D를 표시할 수 없습니다 (${error.message}). 아래 부품 목록·비교 이미지·도면을 이용하세요.`;}

window.cadPage={select,showAll,setViewOnly(value){if(typeof value!=='boolean')throw TypeError('viewOnly: boolean');if(document.documentElement.dataset.theme==='light')document.body.classList.toggle('cad-view-only',value);},setTitle(text){if(document.documentElement.dataset.theme==='light')setLightTitle(byId('cad-viewer'),text);}};
