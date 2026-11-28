import {runStack,summarizeStack} from './stack.js';

const modes=['TC-NCF','MR-MUF'];
const pair=extra=>modes.map(mode=>({mode,layers:12,...extra}));
/** User-confirmed demonstration recipes (05 HANDOFF §2), not process constants.
 * Pressure selectors resolve against the supplied params, including endpoint edits.
 * All result keys are paths relative to each results[] entry.
 */
export const scenarios=[
  {id:'S1',name:'열 이력',description:'12단 TC-NCF 기본 vs 층별 헤드 보정 vs MR-MUF; 접합 온도 미달과 층별 재가열·재용융',
    recipes:[{mode:'TC-NCF',layers:12},{mode:'TC-NCF',layers:12,head_temp_compensation:true},{mode:'MR-MUF',layers:12}],
    display_keys:['thermal.history','thermal_layers','thermal_layers.*.bond_peak_C','thermal_layers.*.bond_temp_ok',
      'alarms','head_setpoints_C','thermal_layers.*.reheat_count','thermal_layers.*.remelt_count','thermal_layers.*.subsequent_remelts']},
  {id:'S2',name:'정렬',description:'같은 시드·초기 오차의 12단; MR은 리플로우 자기정렬 후',
    recipes:pair({}),display_keys:['initial_alignment','alignment.cumulative_um','alignment.top_to_first_die_um']},
  {id:'S3',name:'두께 절반 → 휨 증가 배율',description:'두 모드 각각 50 μm 휨 ÷ 100 μm 휨; 같은 판정 기준과 모델 한계',
    recipes:modes.flatMap(mode=>[100,50].map(thickness_um=>({mode,layers:12,thickness_um}))),
    display_keys:['warpage.max_um','warpage.judgement','warpage.thickness_half_ratio','model_limit']},
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
  if(id==='S3')for(const result of results) {
    const base=results.find(r=>r.recipe.mode===result.recipe.mode&&r.recipe.thickness_um===100);
    const thin=results.find(r=>r.recipe.mode===result.recipe.mode&&r.recipe.thickness_um===50);
    result.warpage.thickness_half_ratio=thin.warpage.max_um/base.warpage.max_um;
    result.model_limit='모델 한계: 1D 선형 탄성·상온 물성·기판·점탄성·경화 수축 미포함. 두 모드 모두 50 μm에서 불량으로, 업체 주장 "MR-MUF가 박형 휨에 유리"를 재현하지 못함';
  }
  return {...preset,results};
}
