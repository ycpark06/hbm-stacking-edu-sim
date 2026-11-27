import {runStack,summarizeStack} from './stack.js';

const modes=['TC-NCF','MR-MUF'];
const pair=extra=>modes.map(mode=>({mode,layers:12,...extra}));
/** User-confirmed demonstration recipes (05 HANDOFF §2), not process constants.
 * Pressure selectors resolve against the supplied params, including endpoint edits.
 * All result keys are paths relative to each results[] entry.
 */
export const scenarios=[
  {id:'S1',name:'열 이력',description:'12단 층별 T(t), 본딩 후 재가열과 가접 노출·재용융을 구분',
    recipes:pair({}),display_keys:['thermal.history','thermal_layers','thermal_layers.0.reheat_count']},
  {id:'S2',name:'정렬',description:'같은 시드·초기 오차의 12단; MR은 리플로우 자기정렬 후',
    recipes:pair({}),display_keys:['initial_alignment','alignment.cumulative_um','alignment.top_to_first_die_um']},
  {id:'S3',name:'박형 다이',description:'두 모드 각각 100 → 50 μm의 최대 휨·같은 판정 기준',
    recipes:modes.flatMap(mode=>[100,50].map(thickness_um=>({mode,layers:12,thickness_um}))),
    display_keys:['warpage.max_um','warpage.judgement']},
  {id:'S4',name:'처리량',description:'12단 본더 점유와 배치 후공정 시간 분해; 라인 UPH 아님',
    recipes:pair({}),display_keys:['cycle.bonder_s','cycle.batch_post_s','cycle.breakdown']},
  {id:'S5',name:'가압 충전',description:'MR-MUF 7/15/20 μm × 모세관 단독/기본 입구 압력/범위 양끝',
    recipes:[7,15,20].flatMap(gap_um=>['capillary','default','lower','upper'].map(pressure=>({mode:'MR-MUF',layers:12,gap_um,pressure}))),
    display_keys:['muf.fill_time_s','defect_area_pct','defect_judgement','muf.filler_warning','muf.gel_warning']},
];
export function runScenario(id,params) {
  const preset=scenarios.find(s=>s.id===id);
  if(!preset)throw new RangeError(`unknown scenario: ${id}`);
  const pressure=params.muf.applied_pressure;
  const pressures={capillary:0,default:pressure.value,lower:pressure.range[0],upper:pressure.range[1]};
  const results=preset.recipes.map(({mode,pressure:selector,...recipe})=>{
    const full=runStack(mode,{...recipe,seed:params.alignment.mc_seed.value,
      ...(selector?{inlet_pressure_MPa:pressures[selector]}:{})},params);
    const result=summarizeStack(full);
    if(id==='S1')result.thermal=full.thermal;
    if(id==='S2')result.initial_alignment=full.alignment.tack;
    return result;
  });
  return {...preset,results};
}
