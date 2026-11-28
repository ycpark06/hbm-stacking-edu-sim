import {PARTS} from './cad_data.js';
export const GROUPS = {
  frame: {name:'프레임 · 스테이지',role:'장비 하중을 지지하고 기판 XY 이동·광학/전장 배치를 구성합니다.'},
  head: {name:'접합 헤드',role:'Z 가이드·하중 전달·가열·콜릿으로 접합을 수행합니다.'},
  z_carriage: {name:'Z 캐리지',role:'Z축에서 헤드의 하중과 위치를 전달합니다.'},
  stack_chuck: {name:'적층 척',role:'층별 하중을 지지하고 진공으로 고정하며 석영 창으로 하부 관찰을 돕습니다.'},
  reflow_chuck: {name:'리플로우 척',role:'완성 스택의 일괄 가열·단열·강제 냉각을 담당합니다.'},
  mold_jig: {name:'가압 충전 지그',role:'독립 체결 금형의 캐비티·게이트·벤트로 수지를 안내합니다.'},
  plunger: {name:'플런저',role:'지그 보어를 따라 수지를 가압 이송합니다. 가이드 끼워맞춤은 수지 씰이 아닙니다.'},
  dispenser: {name:'수지 공급부',role:'MR-MUF 충전 전 액상 수지를 공급합니다.'},
  ncf_tray: {name:'NCF 트레이',role:'필름 부착 다이를 뒤집힌 공급 상태로 준비합니다.'},
  camera_bottom: {name:'하부 카메라',role:'석영 창을 통한 하부 광로에서 충전 유동 선단을 관찰합니다.'}
};
const MATERIALS = {granite:'화강암',al:'알루미늄',steel:'강재',macor:'MACOR',aln:'AlN',quartz:'석영',calsil:'규산칼슘',plastic:'플라스틱',cam:'카메라 대체 재질',elec:'전장 대체 재질'};
export function materialText(part) {
  const grade = {Vacuum_Chuck_200C:'A6061-T6',Reflow_Plate:'A6061-T6',Mold_Block:'SUS304',Plunger:'SUS304',Quartz_Window:'fused silica'}[part.name];
  return `${grade || MATERIALS[part.material]} (${part.material})`;
}
export function dimensionText(part) {
  const p=part.params;
  if(part.type==='box') return `${p.slice(3).join(' × ')} mm (폭 × 깊이 × 높이)`;
  const ring=part.type==='tube'?` · 내경 Ø${p[5]*2}`:'';
  return `외경 Ø${p[4]*2}${ring} × 높이 ${Number((p[3]-p[2]).toFixed(6))} mm`;
}
export const groupParts = id => PARTS.filter(p=>p.group===id);
