// Pure process definitions. All numeric process inputs come from params/results.
// Screen weights, exploded spacing, and camera positions are display settings only.
import {mrmufSchedule} from '../../sim/thermal.js';
export const MODES = Object.freeze(['TC-NCF', 'MR-MUF']);
export const CAMERA_IDS = Object.freeze([1,2,3,4]);
export const DISPLAY = Object.freeze({totalSeconds:90, pixelRatio:2, stackMagnification:45, gapMagnification:8,
  // 표시 설정, 모델 계산값 아님: 리플로우 뒤에도 남기는 상대 어긋남.
  alignmentResidual:.25,
  // DISPLAY 표시 설정: 가장자리 프레임 크기(다이 두께+표시 간격 배수), 낮은 시선.
  filmSection:Object.freeze({size:Object.freeze([5,5,5]),direction:Object.freeze([.6,.03,1])}),
  // 표시 설정(치수·물성 아님): 필름 눌림을 구분하기 위한 상대 배율.
  filmSqueeze:Object.freeze({thickness:.45,spread:1.08}),
  // 표시 설정: 온도 색 매핑·최대 발광과 용융 솔더 띠의 상대 크기 (물성·실측 아님).
  heat:Object.freeze({orange:0xff7800,red:0xff1800,maxEmissive:1.5,
    solderColor:0xffedb0,solderEmissive:2,bandThickness:.18,bandSpread:1.02})});

// Display temperature normalization only; no additional thermal prediction.
export function heatGlow(temp,ambient,peak) {
  return Math.max(0,Math.min(1,(temp-ambient)/(peak-ambient)));
}
export function layerHeat(data,s,v,index) {
  const active=(s.mode==='MR-MUF'&&s.kind==='reflow')||
    (s.mode==='TC-NCF'&&['ramp','hold'].includes(s.kind)&&
      (index===s.layer-1||index===s.layer-2));
  return {glow:active?heatGlow(v.temp,data.params.thermal_stack.ambient_temp.value,
    data.params.reflow.peak_temp.value):0,
    molten:active&&index>0&&v.temp>=data.params.solder.liquidus_snag.value};
}
// Stateless display rule shared by both themes, including direct/reverse seeks.
export function alignmentOffsetRatio(stage,u,profileLength) {
  if(stage.mode!=='MR-MUF')return 1;
  if(['to-mold','dispense','fill','mold-cure','postcure','compare'].includes(stage.kind))return DISPLAY.alignmentResidual;
  if(stage.kind!=='reflow')return 1;
  const progress=Math.max(0,Math.min(1,(stage.segment+Math.max(0,Math.min(1,u)))/profileLength));
  return 1-(1-DISPLAY.alignmentResidual)*progress;
}
// DISPLAY: follow the current die's front edge; layer 0 uses the first layer.
export function filmSectionFrame(w,h,g,layer,offset=0) {
  const pitch=h+g;
  return {center:[offset,(Math.max(1,layer)-1)*pitch-g/2,w/2],
    size:DISPLAY.filmSection.size.map(n=>n*pitch)};
}
// Fit a bounding sphere in both perspective axes; margin is a display setting.
export function cameraFitDistance(radius, verticalFovDegrees, aspect, margin=1.12) {
  const halfVertical=verticalFovDegrees*Math.PI/360;
  const halfHorizontal=Math.atan(Math.tan(halfVertical)*aspect);
  return radius*margin/Math.sin(Math.min(halfVertical,halfHorizontal));
}
// Smooth outward travel and return, with zero velocity at both ends and peak.
export function explodedAmount(fraction) {
  return (1-Math.cos(2*Math.PI*Math.max(0,Math.min(1,fraction))))/2;
}
export function readFactoryData(params, results) {
  const scenario=id=>results.representative.find(s=>s.id===id);
  const tc=scenario('S4').results.find(r=>r.recipe.mode===MODES[0]);
  const mr=scenario('S4').results.find(r=>r.recipe.mode===MODES[1]);
  const fill=scenario('S5').results.find(r=>r.recipe.gap_um===mr.recipe.gap_um && r.recipe.inlet_pressure_MPa===params.muf.applied_pressure.value);
  if(!tc || !mr || !fill || tc.recipe.layers!==mr.recipe.layers) throw Error('S4/S5 기본 조건을 확인하세요.');
  return {params,layers:tc.recipe.layers,tc,mr,fill,profile:mrmufSchedule(mr.recipe.layers,params).filter(s=>s.phase.startsWith('reflow-'))};
}
export function buildStages(data, mode, totalSeconds=DISPLAY.totalSeconds) {
  if(!MODES.includes(mode)) throw RangeError('mode: TC-NCF / MR-MUF');
  if(!Number.isFinite(totalSeconds)||totalSeconds<60||totalSeconds>120) throw RangeError('표시 길이: 60–120 s');
  const p=data.params,q=p.tcncf_process,c=(mode===MODES[0]?data.tc:data.mr).cycle.breakdown.per_layer,stages=[];
  const add=(id,title,kind,layer=0,real=0,weight=1,extra={})=>stages.push({id,title,kind,layer,mode,real_duration_s:real,weight,...extra});
  add('overview','도면 기반 장비 전체 · 공정 경로 살펴보기','overview',0,0,3);
  add('exploded','기능별 분해 보기 · 이동·간격은 표시 연출','exploded',0,0,3);
  for(let layer=1;layer<=data.layers;layer++) {
    const prefix=`L${layer}`, title=t=>`${layer}/${data.layers}층 · ${t}`;
    add(`${prefix}-supply`,title('트레이 공급'),'supply',layer,c.xy_move_s,.45);
    add(`${prefix}-align`,title('하부 카메라 비전 정렬'),'align',layer,c.alignment_s,.45);
    add(`${prefix}-pickup`,title('진공 픽업'),'pickup',layer,c.pickup_s+c.z_move_s,.45);
    if(mode===MODES[0]) {
      add(`${prefix}-ncf`,title('NCF 필름 부착'),'ncf',layer,0,.5);
      add(`${prefix}-approach`,title('헤드 하강 · 접촉 접근'),'approach',layer,c.approach_s,.5);
      add(`${prefix}-ramp`,title('가압 · 헤드 승온'),'ramp',layer,c.ramp_s,1);
      add(`${prefix}-hold`,title('가압 · 가열 유지'),'hold',layer,c.hold_s,.7);
      add(`${prefix}-cool`,title('하중 해제 · 냉각'),'cool',layer,c.cooling_s,.45);
      add(`${prefix}-rise`,title('헤드 상승 · 적층 완료'),'rise',layer,0,.4);
    } else {
      add(`${prefix}-approach`,title('가접 접근'),'approach',layer,c.approach_s,.4);
      add(`${prefix}-tack`,title('작은 하중 · 순간 가열 가접'),'tack',layer,c.tack_s,.8);
      add(`${prefix}-rise`,title('헤드 상승 · 임시 적층'),'rise',layer,0,.4);
    }
  }
  if(mode===MODES[1]) {
    add('to-reflow','전체 스택 → 리플로우 척 · 헤드 히터 OFF','to-reflow',data.layers,0,2);
    data.profile.forEach((segment,i)=>add(`reflow-${i}`,`일괄 리플로우 · ${segment.phase.replace('reflow-','')}`,'reflow',data.layers,segment.duration_s,2,{segment:i}));
    add('to-mold','전체 스택 → 가압 충전 지그 · 척 히터 OFF','to-mold',data.layers,0,2);
    add('dispense','디스펜서 · 액상 수지 공급','dispense',data.layers,data.mr.cycle.breakdown.once.mold_dispense_s,2);
    add('fill','간격 충전 · 모세관과 가압 비교 (S5)','fill',data.layers,data.fill.muf.fill_time_s,4);
    add('mold-cure','금형 내 경화','mold-cure',data.layers,p.mrmuf_process.in_mold_cure_time.value,2);
    add('postcure','후경화 · 문헌 조건','postcure',data.layers,p.muf.cure_time.value*3600,3);
  }
  add('compare','장비 점유 시간 비교 · 본더 / 배치 후공정 분리','compare',data.layers,0,5);
  const sum=stages.reduce((a,s)=>a+s.weight,0);
  return stages.map(({weight,...s},index)=>({...s,index,duration_s:weight/sum*totalSeconds}));
}
export function sampleStage(data,s,fraction) {
  const u=Math.max(0,Math.min(1,fraction)),p=data.params,q=p.tcncf_process,tc=s.mode===MODES[0];
  let temp=tc?q.stage_temp.value:p.thermal_stack.ambient_temp.value, force=0,down=0;
  if(s.kind==='approach') down=u;
  if(['ramp','hold','tack','cool'].includes(s.kind)) down=1;
  if(s.kind==='rise') down=1-u;
  if(s.kind==='ramp') {temp+=u*(q.head_setpoint.value-temp);force=q.bond_force.value;}
  if(s.kind==='hold') {temp=q.head_setpoint.value;force=q.bond_force.value;}
  if(s.kind==='cool') temp=q.head_setpoint.value+u*(q.stage_temp.value-q.head_setpoint.value);
  if(s.kind==='tack') {temp=p.mrmuf_process.tack_temp.value;force=p.mrmuf_process.tack_force.value;}
  if(s.kind==='reflow') temp=data.profile[s.segment].input(u*s.real_duration_s).T_chuck_C;
  if(['dispense','fill','mold-cure'].includes(s.kind)) temp=p.mrmuf_process.mold_fill_temp.value;
  if(s.kind==='postcure') temp=p.muf.cure_temp.value;
  const complete=['rise','to-reflow','reflow','to-mold','dispense','fill','mold-cure','postcure','compare'].includes(s.kind);
  const count=s.layer?Math.max(0,s.layer-(complete?0:1)):0;
  const exposure=tc&&['ramp','hold','cool','rise','compare'].includes(s.kind);
  return {u,temp,force,down,count,reheats:tc?Math.max(0,s.layer-1-(exposure?0:1)):0};
}

// Stateless display interpolation: ramp and hold join continuously; cooling retains it.
export function filmSqueezeAt(kind,u) {
  const t=Math.max(0,Math.min(1,u));
  const amount=kind==='ramp'?t/2:kind==='hold'?(1+t)/2:
    ['cool','rise','compare'].includes(kind)?1:0;
  if(amount===1)return {...DISPLAY.filmSqueeze};
  return {thickness:1+(DISPLAY.filmSqueeze.thickness-1)*amount,
    spread:1+(DISPLAY.filmSqueeze.spread-1)*amount};
}
