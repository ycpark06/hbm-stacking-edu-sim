export const esc=v=>String(v??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const labels={kpi:'원문 KPI',design:'설계 목표·설계값',literature:'문헌값',estimate:'역산 추정값',assumption:'가정값',midterm:'중간 보고서',observation:'관찰 항목',result:'계산 결과',demo:'시연 입력'};
export const badge=kind=>`<span class="badge">${labels[kind]??esc(kind)}</span>`;
export const fmt=v=>typeof v==='number'?(Number.isFinite(v)?Number(v.toPrecision(6)).toString():'—'):esc(v);
export const value=(v,unit='',kind='result')=>`${fmt(v)} ${esc(unit)} ${badge(kind)}`;
const pressureLabel=v=>`${fmt(v)} MPa${v===0?'(모세관 단독)':''}`;

export function resultTitle(r){
  const recipe=r.recipe;
  return `${recipe.mode}${recipe.head_temp_compensation?' · 헤드 보정':''} · 두께 ${recipe.thickness_um} μm · 간격 ${recipe.gap_um} μm · 입구 ${pressureLabel(recipe.inlet_pressure_MPa)}`;
}
export function mufRows(r){
  if(!r.muf)return '';
  return `<dt>충전 시간</dt><dd>${value(r.muf.fill_time_s,'s')}</dd><dt>필러 경고</dt><dd>${r.muf.filler_warning?'필러 막힘 위험':'없음'} ${badge('result')}</dd><dt>겔 경고</dt><dd>${r.muf.gel_warning?'충전 시간 > 겔 시간':'없음'} ${badge('result')}</dd>`;
}
export function s5Table(results){
  const gaps=[...new Set(results.map(r=>r.recipe.gap_um))].sort((a,b)=>a-b);
  const pressures=[...new Set(results.map(r=>r.recipe.inlet_pressure_MPa))].sort((a,b)=>a-b);
  return `<table class="s5-matrix"><caption>간격 × 입구 압력 · 미충전 면적률과 결함 판정 ${badge('result')} · 조건 ${badge('demo')}</caption><thead><tr><th scope="col">간격 / 입구 압력</th>${pressures.map(pressure=>`<th scope="col">${pressureLabel(pressure)}</th>`).join('')}</tr></thead><tbody>${gaps.map(gap=>`<tr><th scope="row">${fmt(gap)} μm</th>${pressures.map(pressure=>{
    const r=results.find(r=>r.recipe.gap_um===gap&&r.recipe.inlet_pressure_MPa===pressure);
    return r?`<td>${value(r.defect_area_pct,'%')}<br>${esc(r.defect_judgement)}</td>`:'<td>—</td>';
  }).join('')}</tr>`).join('')}</tbody></table>`;
}
export function displaySettings(doc){
  // Static HTML is outside this change's write scope; update its display label.
  const setting=doc.getElementById('warp-scale').closest('label').querySelector('.badge');
  setting.className='display-setting';setting.textContent='표시 설정';
  const legend=doc.createElement('p');legend.className='badge-legend';
  legend.innerHTML=`구분 범례: ${Object.keys(labels).map(badge).join(' ')}. 시연 입력은 고장 주입·시뮬레이션에 사용한 입력값입니다.`;
  doc.getElementById('sources').querySelector('h2').after(legend);
}
