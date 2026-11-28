import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import {validateRecipe,recipeParams} from '../../web/js/recipe_limits.js';
import {VISION_DEFAULTS,visionOptions} from '../vision.js';
import {createAlarmDemo} from '../../web/js/alarms.js';
import {chart} from '../../web/js/charts.js';
import {labels,value,resultTitle,mufRows,s5Table,displaySettings} from '../../web/js/hmi_display.js';
import {runScenario} from '../scenarios.js';
const p=JSON.parse(readFileSync(new URL('../params.json',import.meta.url)));
const recipe={mode:'TC-NCF',layers:12,thickness_um:100,gap_um:p.geometry.interlayer_gap.value,
  bond_force_N:p.tcncf_process.bond_force.value,head_temp_C:p.tcncf_process.head_setpoint.value,
  ramp_K_s:p.tcncf_process.ramp_rate.equipment_value,force_ramp_N_s:p.equipment_limits.force_high_ramp_N_s.value,
  inlet_pressure_MPa:p.muf.applied_pressure.value,head_temp_compensation:false,low_range:false};
test('HMI accepts device boundaries and capillary comparison, blocks each out-of-range setting',()=>{
  assert.deepEqual(validateRecipe(recipe,p),[]);
  for(const changes of [{bond_force_N:p.equipment_limits.bond_force_max_N.value,head_temp_C:p.equipment_limits.head_max_temp_C.value},
    {inlet_pressure_MPa:0},{gap_um:7},{gap_um:30},{gap_um:20},{low_range:true,force_ramp_N_s:p.equipment_limits.low_range_ramp_N_s.value}])assert.deepEqual(validateRecipe({...recipe,...changes},p),[]);
  for(const changes of [{bond_force_N:51},{head_temp_C:401},{head_temp_C:p.tcncf_process.stage_temp.value},{ramp_K_s:21},{low_range:true,force_ramp_N_s:2},{gap_um:6},{gap_um:31},{inlet_pressure_MPa:-1},{inlet_pressure_MPa:4},{inlet_pressure_MPa:.05},{layers:3},{thickness_um:75},{mode:'bad'},{head_temp_compensation:'true'},{gap_um:NaN},{ramp_K_s:0}])assert.ok(validateRecipe({...recipe,...changes},p).length,JSON.stringify(changes));
  const shifted=structuredClone(p);shifted.equipment_limits.bond_force_max_N.value=39;
  assert.ok(validateRecipe(recipe,shifted).length,'uses supplied params rather than literal 50');
});
test('HMI adapter applies accepted temperature/ramp without mutating shared params',()=>{
  const before=structuredClone(p),r={...recipe,head_temp_C:310,ramp_K_s:10};const adapted=recipeParams(r,p);
  assert.equal(adapted.tcncf_process.head_setpoint.value,310);assert.equal(adapted.tcncf_process.ramp_rate.equipment_value,10);assert.deepEqual(p,before);
  assert.throws(()=>recipeParams({...recipe,head_temp_C:500},p),RangeError);
});
test('24 vision params retain exact defaults/provenance; supplied params take precedence',()=>{
  assert.equal(Object.keys(VISION_DEFAULTS).length,24);
  for(const [key,entry]of Object.entries(VISION_DEFAULTS))assert.deepEqual(p.alignment[key],entry,key);
  assert.equal(Object.values(VISION_DEFAULTS).filter(v=>v.kind==='midterm').length,21);
  assert.equal(visionOptions({alignment:{pixel_um:{value:2}}}).pixel_um,2);
  assert.equal(visionOptions(p,{pixel_um:3}).pixel_um,3);
});
test('HMI uses real wasm warning, latch persistence, manual reset and mutual heater exclusion',async()=>{
  const wasmBinary=readFileSync(new URL('../../firmware/build/controller.wasm',import.meta.url));
  const d=await createAlarmDemo(p,{wasmBinary});
  assert.equal(d.act('force-warning').warning,1);assert.equal(d.state().latched,0);
  assert.equal(d.act('force-latch').latched,1);assert.equal(d.act('reset').latched,1);
  assert.equal(d.act('clear').latched,1);assert.equal(d.act('reset').latched,0);
  assert.equal(d.act('temp-warning').warning,1);assert.equal(d.act('temp-latch').latched,1);
  d.act('clear');d.act('reset');assert.equal(d.act('hardware').latched,1);
  d.act('clear');d.act('reset');const s=d.act('heaters');assert.ok(s.head_W>0);assert.equal(s.reflow_W,0);assert.equal(s.dual_heater_blocked,1);
});

test('S5 cards expose each condition and computed warnings; matrix retains all 12 results',()=>{
  const results=runScenario('S5',p).results;
  assert.equal(new Set(results.map(resultTitle)).size,12);
  assert.match(resultTitle(results[0]),/간격 7 μm · 입구 0 MPa\(모세관 단독\)/);
  for(const r of results){
    const rows=mufRows(r);
    assert.ok(rows.includes(value(r.muf.fill_time_s,'s')));
    assert.match(rows,/필러 경고/);assert.match(rows,/겔 경고/);
    assert.equal(rows.includes('필러 막힘 위험'),r.muf.filler_warning);
    assert.equal(rows.includes('충전 시간 > 겔 시간'),r.muf.gel_warning);
  }
  const table=s5Table(results);
  assert.equal((table.match(/scope="row"/g)??[]).length,3);
  assert.equal((table.match(/<td>/g)??[]).length,12);
  for(const r of results)assert.ok(table.includes(`${value(r.defect_area_pct,'%')}<br>${r.defect_judgement}`));
  assert.match(table,/0 MPa\(모세관 단독\)/);
});

test('HMI query enables only explicit light, using the same bootstrap as factory and CAD',()=>{
  const html=readFileSync(new URL('../../web/index.html',import.meta.url),'utf8');
  const script=html.match(/<script>(.*?)<\/script>/s)[1];
  for(const page of ['factory','cad'])assert.ok(readFileSync(new URL(`../../web/${page}.html`,import.meta.url),'utf8').includes(`<script>${script}</script>`));
  for(const search of ['', '?theme=dark', '?theme=LIGHT', '?theme=', '?other=light', '?theme=light', '?scenario=S1&theme=light']){
    const document={documentElement:{dataset:{}}};
    runInNewContext(script,{document,location:{search},URLSearchParams});
    assert.equal(document.documentElement.dataset.theme,new URLSearchParams(search).get('theme')==='light'?'light':undefined);
  }
});

for(const theme of [undefined,'light'])test(`chart ${theme??'default'} legend matches 12 distinct layer colors and clears old entries`,()=>{
  const element=()=>({children:[],style:{},setAttribute(){},append(...nodes){this.children.push(...nodes);},replaceChildren(...nodes){this.children=nodes;}});
  const legend=element(),strokes=[];
  const ctx={clearRect(){},fillText(){},beginPath(){},moveTo(){},lineTo(){},setLineDash(){},stroke(){strokes.push(this.strokeStyle);}};
  const canvas={getContext:()=>ctx,ownerDocument:{documentElement:{dataset:{theme}},createElement:element,createTextNode:text=>({textContent:text})},nextElementSibling:legend,setAttribute(){}};
  const series=Array.from({length:12},(_,i)=>({name:`층 ${i+1}`,points:[[0,0],[1,i+1]]}));
  chart(canvas,series);
  assert.equal(legend.children.length,12);
  const colors=legend.children.map((item,i)=>{
    assert.equal(item.children[1].textContent,`층 ${i+1}`);
    const color=item.children[0].style.backgroundColor;
    assert.equal(color,strokes[i+1]);return color;
  });
  assert.equal(new Set(colors).size,12);
  if(theme==='light'){
    // Every series needs visible contrast against the white chart surface.
    for(const color of colors){
      const rgb=color.slice(1).match(/../g).map(c=>parseInt(c,16)/255).map(c=>c<=.04045?c/12.92:((c+.055)/1.055)**2.4);
      const luminance=rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722;
      assert.ok(1.05/(luminance+.05)>=4.5,color);
    }
    assert.equal(ctx.fillStyle,'#44505F');assert.match(ctx.font,/Pretendard/);
  }else{
    assert.equal(colors[0],'#5ce0c2');assert.equal(ctx.fillStyle,'#adbed1');assert.equal(ctx.font,'14px system-ui');
  }
  chart(canvas,series.slice(0,2));assert.equal(legend.children.length,2);
  chart(canvas,[]);assert.equal(legend.textContent,'해당 이력 없음');
});

test('display settings remove the classification badge and legend explains demo inputs',()=>{
  const setting={className:'badge',textContent:'관찰 항목'};
  let legend;
  const doc={getElementById:id=>id==='warp-scale'?{closest:()=>({querySelector:()=>setting})}:{querySelector:()=>({after:node=>{legend=node;}})},createElement:()=>({})};
  displaySettings(doc);
  assert.equal(setting.textContent,'표시 설정');assert.equal(setting.className,'display-setting');
  for(const label of Object.values(labels))assert.ok(legend.innerHTML.includes(label));
  assert.match(value(0,'N','demo'),/시연 입력/);
  assert.match(value(100,'℃','demo'),/시연 입력/);
});
