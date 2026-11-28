# 단계 4 모델 보정 결과

기준: 2026-11-27, `feat/muf-pressure`. 단계 3 기준 HEAD `7b382ede3ee387dce5c0e2a4077c8ad4f5d5e217`의 기존 `scenario_results.json`을 `sim/test/stage3_baseline_results.json`에 보존했다. 모든 입력 변경은 05 HANDOFF 사용자 확정값과 19개 패치에 따른 것이다. 결과에 맞춘 보정은 없다.

## 파라미터 변경 19개

| 패치 키 → 실제 키 | 기존 값 → 새 값 (단위) | kind / source_kind | 출처 |
|---|---|---|---|
| R_contact_head_die → `thermal_stack.tool_contact_R_area` | 1e-05 m2*K/W → 0.0002 m2K/W | estimate / 역산+가정 | https://dspacemainprd01.lib.uwaterloo.ca/server/api/core/bitstreams/c5245d7b-a455-48da-9f03-070fce6eab7b/content ; https://www.jcetglobal.com/uploads/pdf/20200319153130_20609.pdf ; https://imapsource.org/api/v1/articles/56216-high-productivity-thermo-compression-flip-chip-bonding.pdf |
| R_contact_die_stage → `thermal_stack.chuck_contact_R_area` | 1e-05 m2*K/W → 0.0002 m2K/W | estimate / 계산+가정 | https://patents.google.com/patent/US5548470A/esLanguage ; https://www.swtest.org/swtw_library/2016proc/PDF/S03_01_Armstrong_SWTW2016.pdf |
| T_head_minus_T_die_check → `thermal_stack.T_head_minus_T_die_check` | 없음 → 50 degC | literature / 문헌 | https://uwspace.uwaterloo.ca/handle/10012/12523 ; https://imapsource.org/api/v1/articles/56216-high-productivity-thermo-compression-flip-chip-bonding.pdf ; https://www.jcetglobal.com/uploads/pdf/20200319153130_20609.pdf |
| muf_viscosity_fill → `muf.viscosity_at_fill` | 2 Pa*s → 5 Pa.s | assumption / 문헌(간접)+가정 | https://www.techscience.com/cmc/v84n1/61779/html ; https://www.electronics.org/system/files/technical_resource/E18&S31-2.pdf ; 교육용 가정 근거: LMC viscosity at molding temperature not found. Uses surrogate-oil range and granular EMC U-curve minimum of 6.5 Pa.s at 175 C. |
| muf_gel_time → `muf.gel_time` | 없음 → 25 s | literature / 문헌 | https://www.electronics.org/system/files/technical_resource/E18&S31-2.pdf ; https://www.eesemi.com/moldcomp.htm |
| mold_temperature → `mrmuf_process.mold_fill_temp` | 150 C → 175 degC | literature / 문헌 | course lecture ; https://imapsource.org/article/129614-low-warpage-liquid-compression-molded-underfill-for-wafer-level-packaging.pdf ; https://patents.google.com/patent/WO2012133384A1/en |
| mold_pressure_applied → `mrmuf_process.mold_pressure_applied` | 없음 → 3 MPa | literature / 문헌 | https://www.techscience.com/cmc/v84n1/61779/html ; https://patents.google.com/patent/WO2012133384A1/en |
| gap_inlet_pressure_eff → `muf.applied_pressure` | 0 Pa → 1 MPa | assumption / 가정 | 사용자 확정 2026-11-26 (05 HANDOFF 1절 1번): 간격 입구 유효 압력은 공개 수치가 없어 기본 1 MPa, 범위 0.1~3 MPa로 둔다. 금형 압력 3 MPa(문헌)의 손실 후 값 |
| transfer_time → `cycle.mold_fill_time` | 10 s → 10 s | literature / 문헌 | https://www.techscience.com/cmc/v84n1/61779/html ; course lecture |
| in_mold_cure_time → `mrmuf_process.in_mold_cure_time` | 없음 → 100 s | literature / 문헌 | https://www.electronics.org/system/files/technical_resource/E18&S31-2.pdf ; https://imapsource.org/article/129614-low-warpage-liquid-compression-molded-underfill-for-wafer-level-packaging.pdf |
| pmc_temperature → `muf.cure_temp` | 175 C → 175 degC | literature / 문헌 | course lecture ; https://patents.google.com/patent/WO2012133384A1/en ; https://imapsource.org/article/129614-low-warpage-liquid-compression-molded-underfill-for-wafer-level-packaging.pdf |
| pmc_time → `muf.cure_time` | 7200 s → 4 h | literature / 문헌 | course lecture ; https://imapsource.org/article/129614-low-warpage-liquid-compression-molded-underfill-for-wafer-level-packaging.pdf |
| muf_max_filler → `muf.filler_max_size` | 3 um → 3 um | literature / 문헌 | https://conferences.computer.org/ectc/pdfs/ECTC2023-1NkkviSxgDnmPjptC1ysqm/349800a878/349800a878.pdf ; https://imapsource.org/article/129614-low-warpage-liquid-compression-molded-underfill-for-wafer-level-packaging.pdf |
| gap_to_filler_min_ratio → `muf.gap_to_filler_min_ratio` | 없음 → 4 - | literature / 문헌 | https://www.electronicdesign.com/boards/use-underfill-encapsulants-enhance-flip-chip-assembly-reliability ; https://conferences.computer.org/ectc/pdfs/ECTC2023-1NkkviSxgDnmPjptC1ysqm/349800a878/349800a878.pdf |
| chip_gap_height → `geometry.interlayer_gap` | 15 um → 15 um | literature / 문헌 | https://conferences.computer.org/ectc/pdfs/ECTC2023-1NkkviSxgDnmPjptC1ysqm/349800a878/349800a878.pdf ; https://www.3dincites.com/2024/06/why-are-hbm-manufacturers-choosing-liquid-mold-underfill/ |
| vacuum_level_abs → `mrmuf_process.vacuum_level_abs` | 없음 → 19 kPa | assumption / 문헌+가정 | https://www.techscience.com/cmc/v84n1/61779/html ; https://patents.google.com/patent/WO2012133384A1/en ; 교육용 가정 근거: SK hynix used its minimum vacuum level but gave no number. |
| muf_surface_tension → `muf.surface_tension` | 0.04 N/m → 0.0298 N/m | assumption / 문헌(추정)+가정 | https://www.techscience.com/cmc/v84n1/61779/html ; 교육용 가정 근거: Paper's estimate for EMC at 175 C. |
| muf_contact_angle → `muf.contact_angle` | 10 deg → 20 deg | literature / 문헌 | https://www.techscience.com/cmc/v84n1/61779/html |
| fill_model → `muf.fill_model` | 없음 → pressure_driven_hele_shaw_plus_capillary - | literature / 문헌+계산 | https://conferences.computer.org/ectc/pdfs/ECTC2023-1NkkviSxgDnmPjptC1ysqm/349800a878/349800a878.pdf ; https://www.techscience.com/cmc/v84n1/61779/html |

접촉 저항은 직접 측정값이 아닌 `estimate`이며, 정의는 “역산 추정값: 문헌의 측정 온도차 등에서 모델로 역산한 값. 직접 측정값이 아님”이다. 가정값에는 근거 문장을 추가했고 원래 URL을 유지했다. 한국어 구분은 `source_kind`로 보존했다. 전체 params의 kind·source·range는 테스트로 검사한다.

같은 물리량은 기존 키에 덮어썼다. `geometry.interlayer_gap`의 기본값은 15 μm이고, 사용자 확정 선택 범위 7~30 μm는 유지했다. 패치의 문헌 범위 15~20 μm는 같은 객체의 `literature_range`에 보존했다. 기본값을 중복 키로 만들지 않았다.

`muf.applied_pressure`는 금형 압력이 아니라 간격 입구 유효 압력(MPa)이다. SI 유동 계산에서 ×10⁶으로 환산한다. `muf.cure_time`은 기존 7,200 s 후경화 역할을 유지하면서 패치의 4 h를 저장하며, `cycle.js`와 `runStack`의 기존 기계 단계 어댑터에서 ×3,600으로 환산한다. 금형 내 경화 100 s는 별도 키다. `muf.cure_temp`는 후경화 175 ℃, 기존 `mrmuf_process.mold_fill_temp`는 금형 온도 175 ℃에 연결했다.

## 모델과 웹 호출 계약

- `pressureFillTime(mu,L,gap,{gamma,theta_deg,dP_app_Pa})` 기존 SI 시그니처 유지. ΔP = ΔP_inlet + 2γcosθ/h, t = 6μL²/(h²ΔP). 입구 압력 0이면 3μL²/(γhcosθ)로 기존 Washburn과 같다.
- `runStack` recipe에 `inlet_pressure_MPa` 추가. 생략하면 params 기본값, 0이면 모세관 단독. 충전 허용 시간은 기존 `cycle.mold_fill_time`(10 s). 겔 시간 25 s는 경고에만 쓰며 허용 시간을 잘라내지 않는다.
- 미충전률은 한 변 유입 전선의 max(0, 1 − sqrt(t_allow/t_fill)). 각 층과 전체 결과에 모세관 단독 충전·겔 경고를 함께 기록한다.
- 간격/최대 필러 < params 권고값 4이면 “필러 막힘 위험”, < params range 하한 3이면 결함 판정을 “불량(필러 막힘)”으로 덮어쓴다. 계산된 미충전 면적률에는 경험적 필러 면적을 더하지 않는다. 경계 자체(4 또는 3)는 엄격한 미만 조건에 걸리지 않는다.
- `sim/scenarios.js`의 `scenarios`는 id/name/description/recipes/display_keys를 내보내고 `runScenario(id, params)`는 동기 계산으로 `{...preset, results}`를 반환한다. Node API·외부 패키지 없음. S1은 각 결과의 `thermal.history`에 전체 T(t), S2는 `initial_alignment`에 동일 시드 초기 오차를 포함한다. 나머지는 `summarizeStack` 형식이다. S5의 pressure 선택자는 전달받은 params의 기본값·range에 연결된다.

## 단계 3 → 단계 4: 16개 조합

표의 수치는 기본 6유효자리로 표시하며 JSON에는 전체 정밀도를 보존했다. 층별 값은 아래층부터 순서대로 표시한다. 온도 ℃, 휨·정렬 μm, 결함 %, 시간 s. `—`는 NCF 정량 결함 모델 없음이다. Tpeak와 재가열은 기존 C1의 본딩/가접/리플로우 열 이력이며, 금형·후경화 온도-시간을 추가한 그래프가 아니다. 후경화는 배치 시간과 기존 기계 휨 끝점에 반영한다.

| 모드/층/두께 | 층별 최고 온도 3 → 4 | 층별 본딩 후 재가열 3 → 4 | 최대 휨·판정 3 → 4 | 결함 면적률·판정 3 → 4 | 누적 정렬 x,y 3 → 4 | 본더/배치 3 → 4 |
|---|---|---|---|---|---|---|
| TC-NCF/2/100 | 264.468, 278.544 → 208.54, 215.848 | 1,0 → 1,0 | 9.92795 주의 → 7.41317 주의 | — 정량 모델 없음 (경향: 낮은 경향) → — 정량 모델 없음 (경향: 낮은 경향) | (-0.114689, -0.756135) → (-0.114689, -0.756135) | 39.981/0 → 39.981/0 |
| TC-NCF/2/50 | 264.84, 278.744 → 208.554, 215.816 | 1,0 → 1,0 | 42.5142 불량 → 30.7156 불량 | — 정량 모델 없음 (경향: 낮은 경향) → — 정량 모델 없음 (경향: 낮은 경향) | (-0.114689, -0.756135) → (-0.114689, -0.756135) | 39.981/0 → 39.981/0 |
| TC-NCF/4/100 | 264.468, 278.544, 284.63, 288.026 → 208.54, 215.848, 222.069, 227.429 | 3,2,1,0 → 3,2,1,0 | 9.92795 주의 → 7.41317 주의 | — 정량 모델 없음 (경향: 낮은 경향) → — 정량 모델 없음 (경향: 낮은 경향) | (-0.409004, -0.747141) → (-0.409004, -0.747141) | 79.962/0 → 79.962/0 |
| TC-NCF/4/50 | 264.84, 278.744, 284.767, 288.129 → 208.554, 215.816, 222.007, 227.346 | 3,2,1,0 → 3,2,1,0 | 42.5142 불량 → 30.7156 불량 | — 정량 모델 없음 (경향: 낮은 경향) → — 정량 모델 없음 (경향: 낮은 경향) | (-0.409004, -0.747141) → (-0.409004, -0.747141) | 79.962/0 → 79.962/0 |
| TC-NCF/8/100 | 264.468, 278.544, 284.63, 288.026, 290.191, 291.693, 292.795, 293.638 → 208.54, 215.848, 222.069, 227.429, 232.093, 236.19, 239.815, 243.046 | 7,6,5,4,3,2,1,0 → 7,6,5,4,3,2,1,0 | 9.92795 주의 → 7.41317 주의 | — 정량 모델 없음 (경향: 낮은 경향) → — 정량 모델 없음 (경향: 낮은 경향) | (0.339682, -1.00533) → (0.339682, -1.00533) | 159.924/0 → 159.924/0 |
| TC-NCF/8/50 | 264.84, 278.744, 284.767, 288.129, 290.275, 291.764, 292.857, 293.693 → 208.554, 215.816, 222.007, 227.346, 231.998, 236.088, 239.711, 242.943 | 7,6,5,4,3,2,1,0 → 7,6,5,4,3,2,1,0 | 42.5142 불량 → 30.7156 불량 | — 정량 모델 없음 (경향: 낮은 경향) → — 정량 모델 없음 (경향: 낮은 경향) | (0.339682, -1.00533) → (0.339682, -1.00533) | 159.924/0 → 159.924/0 |
| TC-NCF/12/100 | 264.468, 278.544, 284.63, 288.026, 290.191, 291.693, 292.795, 293.638, 294.304, 294.844, 295.289, 295.663 → 208.54, 215.848, 222.069, 227.429, 232.093, 236.19, 239.815, 243.046, 245.944, 248.556, 250.924, 253.079 | 11,10,9,8,7,6,5,4,3,2,1,0 → 11,10,9,8,7,6,5,4,3,2,1,0 | 9.92795 주의 → 7.41317 주의 | — 정량 모델 없음 (경향: 낮은 경향) → — 정량 모델 없음 (경향: 낮은 경향) | (0.243771, -1.15648) → (0.243771, -1.15648) | 239.886/0 → 239.886/0 |
| TC-NCF/12/50 | 264.84, 278.744, 284.767, 288.129, 290.275, 291.764, 292.857, 293.693, 294.354, 294.889, 295.331, 295.703 → 208.554, 215.816, 222.007, 227.346, 231.998, 236.088, 239.711, 242.943, 245.843, 248.461, 250.834, 252.997 | 11,10,9,8,7,6,5,4,3,2,1,0 → 11,10,9,8,7,6,5,4,3,2,1,0 | 42.5142 불량 → 30.7156 불량 | — 정량 모델 없음 (경향: 낮은 경향) → — 정량 모델 없음 (경향: 낮은 경향) | (0.243771, -1.15648) → (0.243771, -1.15648) | 239.886/0 → 239.886/0 |
| MR-MUF/2/100 | 250, 250 → 250, 250 | 0,0 → 0,0 | 6.72345 주의 → 5.40673 주의 | 80.1525 불량 → 0 양호 | (-0.00815524, -0.00576198) → (-0.00815524, -0.00576198) | 6.781/7525.75 → 6.781/14825.75 |
| MR-MUF/2/50 | 250, 250 → 250, 250 | 0,0 → 0,0 | 27.6734 불량 → 22.1991 불량 | 80.1525 불량 → 0 양호 | (-0.00892536, -0.0179166) → (-0.00892536, -0.0179166) | 6.781/7525.75 → 6.781/14825.75 |
| MR-MUF/4/100 | 250, 250, 250, 250 → 250, 250, 250, 250 | 0,0,0,0 → 0,0,0,0 | 6.72345 주의 → 5.40673 주의 | 80.1525 불량 → 0 양호 | (-0.0237722, 0.00261119) → (-0.0237722, 0.00261119) | 13.562/7525.75 → 13.562/14825.75 |
| MR-MUF/4/50 | 250, 250, 250, 250 → 250, 250, 250, 250 | 0,0,0,0 → 0,0,0,0 | 27.6734 불량 → 22.1991 불량 | 80.1525 불량 → 0 양호 | (-0.025899, -0.00978812) → (-0.025899, -0.00978812) | 13.562/7525.75 → 13.562/14825.75 |
| MR-MUF/8/100 | 250, 250, 250, 250, 250, 250, 250, 250 → 250, 250, 250, 250, 250, 250, 250, 250 | 0,0,0,0,0,0,0,0 → 0,0,0,0,0,0,0,0 | 6.72345 주의 → 5.40673 주의 | 80.1525 불량 → 0 양호 | (-0.00562371, 0.0299348) → (-0.00562371, 0.0299348) | 27.124/7525.75 → 27.124/14825.75 |
| MR-MUF/8/50 | 250, 250, 250, 250, 250, 250, 250, 250 → 250, 250, 250, 250, 250, 250, 250, 250 | 0,0,0,0,0,0,0,0 → 0,0,0,0,0,0,0,0 | 27.6734 불량 → 22.1991 불량 | 80.1525 불량 → 0 양호 | (-0.0138201, 0.0287262) → (-0.0138201, 0.0287262) | 27.124/7525.75 → 27.124/14825.75 |
| MR-MUF/12/100 | 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250 → 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250 | 0,0,0,0,0,0,0,0,0,0,0,0 → 0,0,0,0,0,0,0,0,0,0,0,0 | 6.72345 주의 → 5.40673 주의 | 80.1525 불량 → 0 양호 | (0.0414668, 0.0118175) → (0.0414668, 0.0118175) | 40.686/7525.75 → 40.686/14825.75 |
| MR-MUF/12/50 | 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250 → 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250 | 0,0,0,0,0,0,0,0,0,0,0,0 → 0,0,0,0,0,0,0,0,0,0,0,0 | 27.6734 불량 → 22.1991 불량 | 80.1525 불량 → 0 양호 | (0.023428, 0.012047) → (0.023428, 0.012047) | 40.686/7525.75 → 40.686/14825.75 |

## 판정이 바뀐 셀

| 모드/층/두께 | 항목 | 단계 3 → 단계 4 |
|---|---|---|
| MR-MUF/2/100 | defect | 불량 → 양호 |
| MR-MUF/2/50 | defect | 불량 → 양호 |
| MR-MUF/4/100 | defect | 불량 → 양호 |
| MR-MUF/4/50 | defect | 불량 → 양호 |
| MR-MUF/8/100 | defect | 불량 → 양호 |
| MR-MUF/8/50 | defect | 불량 → 양호 |
| MR-MUF/12/100 | defect | 불량 → 양호 |
| MR-MUF/12/50 | defect | 불량 → 양호 |

나열하지 않은 판정 셀은 변하지 않았다. 누적 정렬은 표본 관찰값이고, 정렬 판정은 기존 층별 축 3σ 설계 목표다.

## S1~S5 결과

### S1 열 이력

| 모드 | 층별 최고 온도 ℃ | 아래층 재가열 / 가접 노출 / 리플로우 / 재용융 |
|---|---|---|
| TC-NCF | 208.54, 215.848, 222.069, 227.429, 232.093, 236.19, 239.815, 243.046, 245.944, 248.556, 250.924, 253.079 | 11 / 0 / 0 / 0 |
| MR-MUF | 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250 | 0 / 11 / 1 / 1 |

T(t) 전체 표본은 `stage4_results.json`의 S1 results[].thermal.history에 있다. 재가열 횟수는 온도 임계값과 무관한 본딩 이벤트 수다. 재용융은 액상선 상향 통과 횟수(첫 통과 포함)이며 가접 노출과 구분한다.

### S2 정렬

| 모드 | 누적 x,y μm | 맨 위 ↔ 첫 다이 x,y μm | 최대 층간 축 3σ μm / 판정 |
|---|---|---|---|
| TC-NCF | 0.243771, -1.15648 | 0.276961, -0.885815 | 0.882496 / 양호 |
| MR-MUF | 0.0414668, 0.0118175 | 0.0688492, 0.0209931 | 0.0528094 / 양호 |

두 모드의 initial_alignment가 같은지는 테스트에서 전체 객체 동등성으로 검증한다.

### S3 박형 다이

| 모드 | 두께 μm | 최대 휨 μm | 판정 |
|---|---|---|---|
| TC-NCF | 100 | 7.41317 | 주의 |
| TC-NCF | 50 | 30.7156 | 불량 |
| MR-MUF | 100 | 5.40673 | 주의 |
| MR-MUF | 50 | 22.1991 | 불량 |

### S4 처리량

| 모드 | 본더 s | 배치 후공정 s | 배치 분해 s |
|---|---|---|---|
| TC-NCF | 239.886 | 0 |  |
| MR-MUF | 40.686 | 14825.75 | reflow_s=305.75, mold_dispense_s=10, mold_fill_s=10, mold_cure_s=100, postcure_s=14400 |

후경화 14,400 s는 본더 점유가 아닌 배치 후공정이다. 배치 크기·열승온 대기·라인 UPH는 가정하지 않았다.

### S5 가압 충전

| 간격 μm | 입구 MPa | 충전 s | 미충전 % | 판정 | 필러 경고 | 겔 경고 |
|---|---|---|---|---|---|---|
| 7 | 0 | 1913.07 | 92.7701 | 불량(필러 막힘) | 필러 막힘 위험 | 충전 시간 > 겔 시간 |
| 7 | 1 | 15.1846 | 18.8483 | 불량(필러 막힘) | 필러 막힘 위험 | 없음 |
| 7 | 0.1 | 141.722 | 73.4368 | 불량(필러 막힘) | 필러 막힘 위험 | 충전 시간 > 겔 시간 |
| 7 | 3 | 5.08847 | 0 | 불량(필러 막힘) | 필러 막힘 위험 | 없음 |
| 15 | 0 | 892.767 | 89.4165 | 불량 | 없음 | 충전 시간 > 겔 시간 |
| 15 | 1 | 3.32093 | 0 | 양호 | 없음 | 없음 |
| 15 | 0.1 | 32.1336 | 44.2146 | 불량 | 없음 | 충전 시간 > 겔 시간 |
| 15 | 3 | 1.10973 | 0 | 양호 | 없음 | 없음 |
| 20 | 0 | 669.575 | 87.7792 | 불량 | 없음 | 충전 시간 > 겔 시간 |
| 20 | 1 | 1.86976 | 0 | 양호 | 없음 | 없음 |
| 20 | 0.1 | 18.2392 | 25.9549 | 불량 | 없음 | 없음 |
| 20 | 3 | 0.624417 | 0 | 양호 | 없음 | 없음 |

### 장면 의도와 모델 한계

S1은 TC-NCF의 반복 본딩 재가열과 MR-MUF의 일괄 리플로우를 구분한다. MR에도 가접 열 노출이 있으므로 “열 노출 한 번뿐”이라는 설명은 맞지 않는다. S2는 같은 초기 오차에서 자기정렬 후 잔여를 비교한다. S4는 짧은 본더 점유와 긴 후경화가 함께 나타나며 라인 생산성 우열로 해석할 수 없다. S5는 압력 효과를 보이지만, 7 μm는 충전률이 좋아져도 필러 규칙으로 계속 불량이다.

S3은 100 → 50 μm에서 TC-NCF 7.41317 → 30.7156 μm, MR-MUF 5.40673 → 22.1991 μm로 모두 주의 → 불량이다. 따라서 “MR은 박형 다이에서도 양호”라는 대비는 나오지 않는다. 업체의 “MR-MUF는 박형 휨에 강함”이라는 일반 주장을 보장하지 않는다. 1D 선형 탄성·상온 물성·기판/점탄성/경화 수축 미포함 모델이며, 두 모드에 같은 주의=간격/4·불량=20 μm 기준을 유지했다. 장면을 변경하거나 결과를 조정하지 않았다. NCF는 보이드 정량 모델이 없고, MR 미충전 모델은 범프 투과도·필러 여과·갇힌 공기를 정량화하지 않는다. 진공·금형 압력 등 메타데이터가 직접 결함 계산에 들어가지는 않는다.

## 민감도: 판정을 바꾸는 가정 순서

단계 3과 같은 A(12단 TC 50 μm), B(MR 7 μm, 기본 8단), C(12단 TC 100 μm), D(12단 MR 100 μm)를 비교한다. 한 번에 입력 하나만 params range 양끝으로 바꾼다. 모든 수치 range가 있는 assumption·estimate와, 명시 요청한 문헌 이송 시간을 포함했다. 변화 수는 4개 판정 항목 × 끝점 × 사례에서 바뀐 셀 수다. 정렬/휨/접촉/결함 판정을 고정한 테스트는 없다.

| 입력 | kind | 범위 (단위) | 바뀐 판정 셀 수 | 바뀐 사례: 끝점 → 항목·판정 |
|---|---|---|---|---|
| `thermal_stack.tool_contact_R_area` | estimate | 2e-05, 0.001 (m2K/W) | 8 | A:0.001 → warpage 주의, defect 정량 모델 없음 (경향: 미접합 위험, 낮은 경향), contact 미접촉/접촉 전 겔화; B:0.001 → warpage 양호; C:0.001 → warpage 양호, defect 정량 모델 없음 (경향: 미접합 위험, 낮은 경향), contact 미접촉/접촉 전 겔화; D:0.001 → warpage 양호 |
| `thermal_stack.chuck_contact_R_area` | estimate | 5e-05, 0.002 (m2K/W) | 3 | A:5e-05 → warpage 주의; B:5e-05 → warpage 양호; D:5e-05 → warpage 양호 |
| `muf.applied_pressure` | assumption | 0.1, 3 (MPa) | 1 | D:0.1 → defect 불량 |
| `geometry.cu_pillar_height` | assumption | 5, 25 (um) | 0 | 없음 |
| `geometry.solder_cap_height` | assumption | 3, 15 (um) | 0 | 없음 |
| `geometry.die_size` | assumption | 5, 5 (mm) | 0 | 없음 |
| `ncf.viscosity_activation_energy` | assumption | 50, 80 (kJ/mol) | 0 | 없음 |
| `ncf.gel_time_at_250C` | assumption | 1, 10 (s) | 0 | 없음 |
| `ncf.thermal_conductivity` | assumption | 0.2, 0.6 (W/m/K) | 0 | 없음 |
| `ncf.density` | assumption | 1400, 1600 (kg/m3) | 0 | 없음 |
| `ncf.specific_heat` | assumption | 1000, 1300 (J/kg/K) | 0 | 없음 |
| `ncf.gel_conversion` | assumption | 0.4, 0.8 (1) | 0 | 없음 |
| `ncf.castro_A` | assumption | 1, 3 (1) | 0 | 없음 |
| `ncf.cure_activation_energy` | assumption | 40, 80 (kJ/mol) | 0 | 없음 |
| `ncf.low_viscosity_window` | assumption | 0.5, 2 (s) | 0 | 없음 |
| `muf.viscosity_at_fill` | assumption | 1, 10 (Pa.s) | 0 | 없음 |
| `muf.surface_tension` | assumption | 0.025, 0.035 (N/m) | 0 | 없음 |
| `muf.thermal_conductivity` | assumption | 0.6, 4 (W/m/K) | 0 | 없음 |
| `muf.specific_heat` | assumption | 800, 1100 (J/kg/K) | 0 | 없음 |
| `solder.molten_height_for_alignment` | assumption | 3, 15 (um) | 0 | 없음 |
| `mrmuf_process.tack_temp` | assumption | 220, 260 (C) | 0 | 없음 |
| `mrmuf_process.tack_time` | assumption | 0.5, 3 (s) | 0 | B:3 입력 충돌; D:3 입력 충돌 |
| `mrmuf_process.tack_force` | assumption | 0.5, 10 (N) | 0 | 없음 |
| `mrmuf_process.vacuum_level_abs` | assumption | 1, 100 (kPa) | 0 | 없음 |
| `materials.snag_E` | assumption | 40, 55 (GPa) | 0 | 없음 |
| `cycle.mrmuf_tack_cycle_per_die` | assumption | 1.5, 5 (s) | 0 | 없음 |
| `cycle.xy_distance` | assumption | 25, 100 (mm) | 0 | 없음 |
| `cycle.z_distance` | assumption | 2, 10 (mm) | 0 | 없음 |
| `cycle.pickup_time` | assumption | 0.2, 1 (s) | 0 | 없음 |
| `cycle.alignment_frame_time` | assumption | 0.02, 0.1 (s) | 0 | 없음 |
| `cycle.mold_dispense_time` | assumption | 5, 20 (s) | 0 | 없음 |
| `alignment.damping` | assumption | 0.001, 0.1 (N*s/m) | 0 | 없음 |
| `alignment.resist_force` | assumption | 0.0001, 0.01 (N) | 0 | 없음 |
| `recipe.layers` | assumption | 2, 12 (count) | 0 | 없음 |
| `cycle.mold_fill_time` | literature | 5, 30 (s) | 0 | 없음 |

끝점별 휨·미충전률·정렬 3σ·접촉층 수·층별 열 통계·본더/배치 수치는 `scenario_results.json` sensitivity[].rows에 보존했다. 범위가 없는 가정은 임의의 범위를 만들지 않고 같은 파일의 unswept에 나열했다. 고정 범위(예: 다이 크기 5~5)는 한 번만 실행한다. params를 바꾸어도 recipe에 명시된 층 수, 현재 계산에 쓰이지 않는 물성·관찰용 공정 메타데이터는 결과가 변하지 않을 수 있다.

가접 시간 상한 3 s는 기존 총 가접 사이클 3 s와 충돌한다(냉각/취급 시간이 양수여야 함). 이 끝점의 MR B/D 2개는 계산 불가로 기록했으며 다른 값을 함께 바꾸거나 범위를 축소하지 않았다.

## 검증과 작업 상태

`PATH=/opt/homebrew/bin:$PATH node --test sim/test` 실행. 실제 통과 개수·golden 요약은 아래에 기록한다. 압력 해석해 상대 오차 1e-12, 미소 입구 압력의 Washburn 수렴, 압력 두 배의 시간 1/2, 필러 경계·겔 경고·params 검사를 포함한다. 시나리오 판정을 예상값으로 고정하지 않는다. 기존 golden·정렬·helpers·web·펌웨어·CAD는 수정하지 않았다. 기존 c1/c2 결과 파일 대신 새 stage4_c1_results.json/stage4_c2_results.json에 결과를 쓴다.

커밋 시도 `git add sim/params.json && git commit -m 'feat: params에 MUF 몰딩·접촉 열저항 조사값 반영'`는 다음 권한 오류로 실패했다. 우회·push·PR 생성은 하지 않았다.

```text
fatal: Unable to create '/Users/hyunbin/Desktop/MSE489/기말보고서/repo/.git/worktrees/wt-muf/index.lock': Operation not permitted
```

실제 전체 테스트 출력 요약:

```text
SUMMARY total=111 golden_pass=103 float_exception_pass=8 failures=0
tests 142
suites 0
pass 142
fail 0
cancelled 0
skipped 0
todo 0
duration_ms 80549.262667
```

`node --test sim/test/models.test.js sim/test/params.test.js`의 선행 검증도 27개 통과, 실패 0이다. `git diff --check`는 출력 없이 통과했다. `git log --oneline origin/main..HEAD`는 출력이 없다(새 커밋 없음).

| 완료 기준 | 상태 |
|---|---|
| 전체 테스트와 golden 111 유지 | 충족 (142/142, golden 111/111) |
| 압력 충전 해석해·Washburn 수렴·필러 경계 | 충족 |
| params 19개 표·kind/source·범위 검사 | 충족 |
| 16개 비교·판정 변화·S1~S5·민감도 | 충족, 기존 가접 사이클과 충돌한 끝점 2개 별도 기록 |
| requirements 1·6·7절 반영, 같은 휨 기준 유지 | 충족 |
| 허용 경로만 변경 | 충족 |
| 기능별 커밋 | 미충족: index.lock 쓰기 권한 오류 |

HANDOFF와 다르게 처리한 점은 간격의 기존 선택 range를 유지하고 패치 range를 literature_range로 저장한 것, 기존 C1/C2 결과를 덮어쓰지 않고 새 결과 파일로 출력한 것, 상충하는 민감도 끝점 2개를 계산 불가로 기록한 것이다. 사용자 확정값·장면·같은 휨 기준은 변경하지 않았다.

공용 파일 반영 요청: 없음. 허용된 params와 requirements는 이 작업 트리에 반영했다. README 모델 한계 서술은 W5 담당이므로, S3에서 두 모드 50 μm 모두 불량이라는 결과와 본 문서의 모델 한계를 후속 문서 작업에서 참고할 수 있다.


## 접합 온도 미달과 헤드 온도 보정 (Issue #29)

2026-11-28 사용자 확정 사항을 반영했다. 이 절의 S1·S3 정의가 앞의 초기 단계 4 장면 정의를 대체한다. 접촉 열저항, 기본 헤드 300 ℃, 기존 물성·공정 파라미터는 변경하지 않았다. 새 params 키는 `judgement.bond_temp_margin_C`(10 ℃, `design`, 사용자 확정 설계값)와 `equipment_limits.head_max_temp_C`(400 ℃, 새 kind `kpi` = 원문 KPI, 출처 PBL 7쪽)뿐이다. 기존 400 ℃ 키 `head_drift.target_temp`는 중간 보고서의 가열 실험 조건이므로 장비 한계와 별도 키로 구분했다.

### 판정과 웹 호출 계약

`runStack`의 `thermal.layers[i]`와 `summarizeStack`의 `thermal_layers[i]`에 `bond_peak_C`, `bond_temp_ok`, `liquidus_C`, `shortfall_C`, `head_setpoint_C`를 추가했다. TC-NCF의 자기 접합 최고는 해당 층 추가 시 본딩 승온·유지·냉각 전체 구간의 최고(양 끝 포함)다. 나중에 다른 층을 본딩할 때 발생한 최고 온도로 미달을 구제하지 않는다. 기존 `peak_C`는 전체 이력 최고로 그대로 유지한다. MR-MUF는 가접을 제외한 리플로우 전체 구간 최고로 같은 검사 결과만 기록한다.

경계는 **최고 온도 < 액상선 221 ℃이면 미달**, 같으면 통과다. 반올림 전 실수로 판정하며 부족분은 `max(0, 액상선 − 자기 접합 최고)`다. 통과는 온도 조건만의 통과이며 접합 품질 전체를 보증하지 않는다. MR-MUF에서는 미달이어도 알람을 만들지 않는다. TC-NCF의 전체 `alarms`는 `{code:'BOND_TEMP_LOW', message:'접합 온도 미달', layer:1부터 시작하는 층 번호, peak_C, shortfall_C, liquidus_C}` 객체 배열이다.

`recipe.head_temp_compensation` 기본값은 false다. true인 TC-NCF에서만 아래층부터 순서대로 이전 설정을 고정하여 접두 스택 열 이력을 재계산한다. 이분법 목표는 **액상선 + 10 ℃ = 231 ℃**이며, 종료 조건은 헤드 설정 구간 폭 ≤ 0.05 ℃(요구 0.1 ℃ 이하), 구간 확장·이분법 각각 최대 64회다. 목표와 400 ℃는 params에서 읽는다. 구간 폭과 반복 상한은 물성·공정값이 아닌 수치 알고리즘 설정이며 `head_compensation`에 반환한다. 승온 속도 20 K/s와 유지·냉각 시간은 그대로여서 설정 온도에 따라 승온 시간만 바뀐다.

400 ℃에서 목표에 도달하는지 직접 검사하며, 정확히 한계에서 도달하면 허용한다. 넘으면 `accepted:false`, `rejection:{code:'HEAD_TEMP_LIMIT', reason, layer, required_head_C, limit_C}`를 반환하고 정상 실행 결과(`thermal`, `cycle` 등)는 반환하지 않는다. 거부된 필요 온도는 0.05 ℃ 이하 구간의 상한 추정값이다. 성공은 `accepted:true`, `rejection:null`이다. `head_setpoints_C`(MR은 null), `head_compensation.layers`의 층별 필요 설정·여유·반복 횟수를 HMI에서 바로 사용할 수 있다. MR에서 옵션을 요청해도 리플로우 조건은 바뀌지 않으며 `enabled:false`와 설명을 기록한다.

보정 시 `cycle.breakdown.by_layer`에 실제 층별 시간을 추가하고 기존 `per_layer`·`per_layer_s` 형식은 층 평균으로 유지한다. `layer_totals`와 본더 총 시간은 실제 설정으로 합산한다. S1 `display_keys`의 `*`는 모든 층 배열 원소를 뜻한다.

### S1: TC-NCF 12단 기본 vs 보정, MR-MUF 12단

100 μm, 기본 간격 15 μm. 아래 표의 각 쌍은 **기본 / 보정**이다. 이 경우 층별 자기 접합 최고와 전체 이력 최고는 같다. 기본 헤드는 전 층 300 ℃다.

| 층 | 보정 필요 헤드 ℃ | 400 ℃까지 여유 ℃ | 자기 접합 최고 ℃ (기본 / 보정) | 온도 판정 | 재가열 횟수 | 재용융 횟수 | 첫 통과 제외 추가 횟수 |
|---|---|---|---|---|---|---|---|
| 1 | 341.39 | 58.61 | 208.540 / 231.002 | 미달 / 통과 | 11 / 11 | 0 / 1 | 0 / 0 |
| 2 | 326.15 | 73.85 | 215.848 / 230.999 | 미달 / 통과 | 10 / 10 | 0 / 1 | 0 / 0 |
| 3 | 314.62 | 85.38 | 222.069 / 230.993 | 통과 / 통과 | 9 / 9 | 1 / 1 | 0 / 0 |
| 4 | 305.61 | 94.39 | 227.429 / 231.003 | 통과 / 통과 | 8 / 8 | 1 / 1 | 0 / 0 |
| 5 | 298.36 | 101.64 | 232.093 / 231.009 | 통과 / 통과 | 7 / 7 | 2 / 1 | 1 / 0 |
| 6 | 292.39 | 107.61 | 236.190 / 231.005 | 통과 / 통과 | 6 / 6 | 3 / 1 | 2 / 0 |
| 7 | 287.41 | 112.59 | 239.815 / 231.009 | 통과 / 통과 | 5 / 5 | 3 / 2 | 2 / 1 |
| 8 | 283.16 | 116.84 | 243.046 / 230.997 | 통과 / 통과 | 4 / 4 | 4 / 2 | 3 / 1 |
| 9 | 279.53 | 120.47 | 245.944 / 231.003 | 통과 / 통과 | 3 / 3 | 4 / 2 | 3 / 1 |
| 10 | 276.39 | 123.61 | 248.556 / 231.007 | 통과 / 통과 | 2 / 2 | 3 / 2 | 2 / 1 |
| 11 | 273.60 | 126.40 | 250.924 / 230.993 | 통과 / 통과 | 1 / 1 | 2 / 2 | 1 / 1 |
| 12 | 271.19 | 128.81 | 253.079 / 231.011 | 통과 / 통과 | 0 / 0 | 1 / 1 | 0 / 0 |

기본 레시피 알람은 1층 208.540 ℃(부족 12.460 ℃), 2층 215.848 ℃(부족 5.152 ℃)다. 보정에서는 알람이 없으며 최고 온도는 230.9926~231.0112 ℃로 목표 ±0.5 ℃ 안이다. 보정 기본 12단에서 거부 층은 없고 최소 헤드 여유는 1층의 58.61 ℃다.

재가열은 이후 본딩 이벤트 수이며 온도 임계값과 무관하다. **재용융 횟수(`remelt_count`)는 첫 용융을 포함한 액상선 상향 통과 수**이고, `subsequent_remelts`는 첫 통과를 뺀 추가 횟수다. 기본 5~9층의 재용융은 2/3/3/4/4회(추가 1/2/2/3/3회)로 확인된다. 보정은 앞부분 헤드를 높이지만 뒤쪽 헤드를 낮추므로 전체적으로 재용융이 늘지는 않는다. 재가열 이벤트 수는 같고, 5~9층 재용융은 1/1/2/2/2회가 된다. 결과에 맞춰 입력을 바꾸지 않았다.

MR-MUF 12단은 모든 층 리플로우 최고 약 250 ℃, 온도 통과, 알람 없음이다. 층별 재가열은 모두 0회, 재용융은 모두 1회(추가 0회), 리플로우 1회다. 가접 노출은 아래층부터 11/10/9/8/7/6/5/4/3/2/1/0회다. 본더 시간은 TC 기본 239.886 s → 보정 237.376 s, MR 40.686 s다. 뒤쪽 층 설정 하향으로 보정 전체 승온 시간의 합은 소폭 줄었다.

기본 TC-NCF 2/4/8층에서도 각각 미달 2개 층(1·2층)이다. 이 수치는 관찰 결과이며 테스트로 미달 층 번호를 고정하지 않는다. 50 μm의 보정 목표 ±0.5 ℃ 및 이전 층 설정 고정도 테스트했다.

### 거부 검증 사례

기존 params 추정 범위 상한인 툴–다이 접촉 열저항 1e-3 m²K/W를 **검증용 복제 입력**에만 넣으면, 1층 필요 헤드 약 782.21 ℃로 거부한다(400 ℃ 대비 약 382.21 ℃ 초과). 저장된 params 값은 2e-4 m²K/W로 유지한다. 400 ℃ 경계 자체에서 목표에 도달하는 경우는 허용하는 테스트도 통과했다.

### S3: 두께 절반 → 휨 증가 배율

배율은 모드마다 50 μm 최대 절대 휨 ÷ 100 μm 최대 절대 휨이다. S3 결과의 `warpage.thickness_half_ratio`와 `model_limit`에 배율·설명을 반환한다.

| 모드 | 100 μm 휨 / 판정 | 50 μm 휨 / 판정 | 휨 증가 배율 |
|---|---|---|---|
| TC-NCF | 7.41317 μm / 주의 | 30.71565 μm / 불량 | 4.14339배 |
| MR-MUF | 5.40673 μm / 주의 | 22.19910 μm / 불량 | 4.10583배 |

**모델 한계:** 1D 선형 탄성·상온 물성·기판·점탄성·경화 수축 미포함. 두 모드 모두 50 μm에서 불량이므로 업체 주장 “MR-MUF가 박형 휨에 유리”를 재현하지 못한다. 두 모드에 같은 주의=간격/4 초과·불량=20 μm 초과 기준을 유지했다(05 HANDOFF 1절 2번). 절대 휨의 크기 차이를 업체 주장 재현으로 해석하지 않는다.

### 재실행과 기본 결과 불변 확인

`stage4_bond_baseline_results.json`에 작업 시작 HEAD `f4c2d67`(PR #28 병합)의 기본 16개 결과와 기존 params를 보존했다. 16개 조합을 재실행하여 **기존 모든 결과 필드가 정확히 같음**을 검사했다. 새 판정·옵션 메타데이터만 추가됐고, 옵션 생략과 명시적 false의 결과도 정확히 같다. params는 기존 키 전체를 재귀 비교하여 변경이 없음을 검사한다. 기존 S2·S4·S5 및 기본 S1/S3 수치도 유지되었다.

재실행 결과는 `scenario_results.json`(16개·민감도), `stage4_results.json`(S1~S5, S1 전체 T(t)), `bond_temp_results.json`(S1 비교·S3 배율·2/4/8층 미달 수·거부 사례)에 기록했다. 테스트는 액상선 경계, 자기 접합 구간 분리, 두 두께의 보정 목표, 이전 설정 고정, 400 ℃ 경계·초과 거부, MR 결과만 기록, 기본 결과·기존 params 불변을 확인한다. golden 파일은 변경하지 않았다.

W6 최종 검증: `PATH=/opt/homebrew/bin:$PATH node --test 'sim/test/*.test.js'` → tests 153, pass 153, fail 0 (87,225.75225 ms). Golden 요약은 `total=111 golden_pass=103 float_exception_pass=8 failures=0`으로 기존 111개를 유지했다. `git diff --check` 통과. PR #28의 `stage4_results.json`과도 새 필드를 제외한 기존 S1~S5 결과를 재귀 비교했고, 기본 S1의 전체 열 이력까지 정확히 같았다. `git log --oneline origin/main..HEAD` 출력 없음. 커밋·push·PR·Issue 변경 없음.
