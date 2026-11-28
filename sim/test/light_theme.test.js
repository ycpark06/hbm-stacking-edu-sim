import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {readFactoryData,buildStages,sampleStage} from '../../web/js/factory_sequence.js';
import {stageCursor,lightRecipe,layerBars,tcPlot,mrPlot,valueAt,createLightPanel,lightCategories,niceTicks} from '../../web/js/factory_light.js';
const read=p=>JSON.parse(readFileSync(new URL(p,import.meta.url)));
const params=read('../params.json'),results=read('./stage4_results.json'),data=readFactoryData(params,results),recipe=lightRecipe(results);
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-7,`${a} != ${b}`);
test('light bars and reheat counts advance only after heating ends, using sequence kinds',()=>{
  assert.equal(recipe.recipe.head_temp_compensation,false);
  const stages=buildStages(data,'TC-NCF');
  // Reverse traversal also checks that the result does not depend on playback history.
  for(const current of [...stages,...stages.toReversed()]){
    const complete=['cool','rise','compare'].includes(current.kind);
    const count=Math.max(0,current.layer-(complete?0:1));
    const bars=layerBars(recipe,{...current,id:'arbitrary-stage-id'},params.solder.liquidus_snag.value);
    assert.equal(bars.length,count,current.id);
    bars.forEach((bar,i)=>{
      const source=recipe.thermal_layers[i];
      assert.equal(bar.layer,i+1);
      assert.equal(bar.peak_C,source.peak_C);
      assert.equal(bar.reheat_count,Math.min(source.reheat_count,count-i-1));
      assert.equal(bar.color,source.bond_peak_C<params.solder.liquidus_snag.value?'#C2622A':'#14365A');
    });
  }
  for(const current of buildStages(data,'MR-MUF'))assert.deepEqual(layerBars(recipe,current,params.solder.liquidus_snag.value),[]);
});
test('bar colors use own-bond peaks and the supplied liquidus, including equality',()=>{
  const sample={thermal_layers:[
    {peak_C:300,bond_peak_C:220,reheat_count:1},
    {peak_C:300,bond_peak_C:221,reheat_count:0}
  ]};
  assert.deepEqual(layerBars(sample,{mode:'TC-NCF',layer:2,kind:'cool'},221).map(b=>b.color),['#C2622A','#14365A']);
  assert.deepEqual(layerBars(sample,{mode:'TC-NCF',layer:2,kind:'cool'},222).map(b=>b.color),['#C2622A','#C2622A']);
});
test('nice time ticks use 1/2/5 steps within the original axis range',()=>{
  assert.deepEqual(niceTicks(17),[0,5,10,15]);
  assert.deepEqual(niceTicks(8),[0,2,4,6,8]);
  assert.deepEqual(niceTicks(4),[0,1,2,3,4]);
  assert.deepEqual(niceTicks(.8),[0,.2,.4,.6,.8]);
  assert.deepEqual(niceTicks(610),[0,200,400,600]);
  for(const total of [0,-1,Infinity,NaN])assert.deepEqual(niceTicks(total),[0]);
  for(const mode of ['TC-NCF','MR-MUF']){
    const stages=buildStages(data,mode),stage=stages.find(s=>s.kind===(mode==='TC-NCF'?'hold':'reflow'));
    const plot=mode==='TC-NCF'?tcPlot(data,recipe,stages,stage,.5):mrPlot(data,stages,stage,.5);
    const ticks=niceTicks(plot.total),step=ticks[1];
    assert.ok(ticks.at(-1)<=plot.total);
    assert.ok([1,2,5].some(n=>Math.abs(n-step/10**Math.floor(Math.log10(step)))<1e-7));
  }
});
test('TC cursor follows phase start + progress × original duration; thermal values come from S1',()=>{
  const stages=buildStages(data,'TC-NCF');
  for(let layer=1;layer<=data.layers;layer++){
    const parts=stages.filter(s=>s.layer===layer&&['ramp','hold','cool'].includes(s.kind));
    for(const s of parts)for(const u of [0,.25,.8,1]){
      const plot=tcPlot(data,recipe,stages,s,u);
      near(plot.time,parts.slice(0,parts.indexOf(s)).reduce((t,p)=>t+p.real_duration_s,0)+u*s.real_duration_s);
      assert.ok(plot.temperature.every(([,temp])=>recipe.thermal.history.some(row=>row.T.length===layer&&row.T[layer-1]===temp)));
      near(valueAt(plot.head,plot.time),sampleStage(data,s,u).temp);
    }
  }
});
test('MR cursor covers every sequence segment and S5 fill advances by elapsed time',()=>{
  const stages=buildStages(data,'MR-MUF'),parts=stages.filter(s=>s.kind==='reflow');
  for(const s of parts)for(const u of [0,.5,1]){
    const plot=mrPlot(data,stages,s,u);near(plot.time,stageCursor(parts,s,u));near(valueAt(plot.temperature,plot.time),sampleStage(data,s,u).temp);
  }
  const fill=stages.find(s=>s.kind==='fill');
  for(const u of [0,.25,.5,1]){const plot=mrPlot(data,stages,fill,u);near(plot.fill,u);near(plot.fillTime,data.fill.muf.fill_time_s*u);}
  near(mrPlot(data,stages,stages.at(-1),0).fill,1);
});

test('cursor interpolation clamps endpoints and uses the new command at phase boundaries',()=>{
  const points=[[0,40],[10,40],[10,0],[12,0]];
  assert.equal(valueAt(points,-1),40);
  assert.equal(valueAt(points,10),0);
  assert.equal(valueAt(points,20),0);
  assert.equal(valueAt([[0,100],[10,300]],5),200);
});

// Exercise rendered badges as well as the kind mapping, including changed and
// mixed categories, so a hardcoded label cannot pass against today's params.
function renderPanel(p,mode='TC-NCF',stageId=null,u=.5){
  const previous=globalThis.document,children=[],films=[];
  globalThis.document={createElement:()=>({setAttribute(){},classList:{toggle(){}}})};
  try{
    const d=readFactoryData(p,results),stages=buildStages(d,mode);
    const panel=createLightPanel({append:node=>children.push(node)},{append:node=>films.push(node)},d,results);
    panel.update(stages,stageId?stages.find(s=>s.id===stageId):stages.find(s=>s.kind===(mode==='TC-NCF'?'hold':'reflow')),u,4);
    return {html:children[0].innerHTML,film:films[0].innerHTML};
  }finally{globalThis.document=previous;}
}
test('rendered light badge categories follow the corresponding params kind',()=>{
  const labels={literature:'문헌값',design:'설계값',assumption:'가정값',midterm:'중간 보고서값',observation:'관찰 항목',estimate:'역산 추정값',kpi:'원문 KPI'};
  const groups={head:[params.tcncf_process.head_setpoint],force:[params.tcncf_process.bond_force],liquidus:[params.solder.liquidus_snag],time:['approach_time','hold_time','cool_time'].map(k=>params.tcncf_process[k]),reflow:Object.values(params.reflow),shoulder:[params.thermal_stack.reflow_shoulder_temp]};
  for(const [key,entries] of Object.entries(groups))assert.equal(lightCategories(params)[key],[...new Set(entries.map(q=>labels[q.kind]))].join(' / '));
  for(const kind of Object.keys(labels)){
    const p=structuredClone(params);
    p.tcncf_process.head_setpoint.kind=p.tcncf_process.bond_force.kind=p.solder.liquidus_snag.kind=kind;
    for(const k of ['approach_time','hold_time','cool_time'])p.tcncf_process[k].kind=kind;
    for(const q of Object.values(p.reflow))q.kind=kind;
    p.thermal_stack.reflow_shoulder_temp.kind=kind;
    const tc=renderPanel(p).html,mr=renderPanel(p,'MR-MUF').html;
    for(const name of ['헤드','하중'])assert.ok(tc.includes(`${name} <small>${labels[kind]}</small>`));
    for(const name of ['액상선','시간'])assert.ok(tc.includes(`${labels[kind]} · ${name}</span>`));
    for(const name of ['리플로우','shoulder'])assert.ok(mr.includes(`${labels[kind]} · ${name}</span>`));
  }
  const mixed=structuredClone(params);mixed.tcncf_process.hold_time.kind='design';mixed.reflow.peak_temp.kind='assumption';
  assert.ok(renderPanel(mixed).html.includes('문헌값 / 설계값 · 시간'));
  assert.ok(renderPanel(mixed,'MR-MUF').html.includes('문헌값 / 가정값 · 리플로우'));
});

test('rendered bars leave the heating layer empty and delay reheat numbers until cool',()=>{
  const stages=buildStages(data,'TC-NCF');
  for(const current of stages)for(const u of [0,.5,1]){
    const count=Math.max(0,current.layer-(['cool','rise','compare'].includes(current.kind)?0:1));
    const html=renderPanel(params,'TC-NCF',current.id,u).html;
    const bars=[...html.matchAll(/<rect[^>]*data-layer="(\d+)"[^>]*\/>/g)];
    assert.equal(bars.length,count,`${current.id} at ${u}`);
    bars.forEach(([rect,layer])=>{
      assert.ok(Number(layer)<=count);
      const expected=recipe.thermal_layers[Number(layer)-1].bond_peak_C<params.solder.liquidus_snag.value?'#C2622A':'#14365A';
      assert.ok(rect.includes(`fill="${expected}"`));
      assert.ok(rect.includes(`stroke="${Number(layer)===current.layer?'#44505F':'none'}"`));
    });
    const reheatLabels=[...html.matchAll(/<text x="[^"]+" y="205" text-anchor="middle">(\d+)<\/text>/g)].map(m=>Number(m[1]));
    assert.deepEqual(reheatLabels,layerBars(recipe,current,params.solder.liquidus_snag.value).map(b=>b.reheat_count));
    assert.ok(html.includes('위층을 붙이며 더 받은 열 횟수'));
  }
});
