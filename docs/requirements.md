# 요구사항과 설계 목표 — 교육용 HBM 적층 본더

상태: 2026-11-27 단계 4 모델 보정 반영 (05 HANDOFF 사용자 확정 사항 유지)

## 1. 구분 규칙
- **원문 KPI·원문 요구:** PBL 강의자료에 적힌 수치. 판정 대상
- **설계 목표:** 이번 과제에서 근거를 두고 새로 정한 수치. 판정 대상. 문헌 수치를 판정 기준으로 채택하면 설계 목표로 구분하고 근거에 문헌값을 적는다
- **문헌값:** 공개 문헌 수치. 판정 대상 아님, 시뮬레이션 입력
- **설계값:** 사용자 확정 장비·공정 설정. 원문 KPI와 구분
- **역산 추정값:** 문헌의 측정 온도차 등에서 모델로 역산한 값. 직접 측정값이 아님 (`estimate`)
- **가정값:** 공개 수치가 없어 근거를 붙인 교육용 입력. `sim/params.json`에 모아 기록
- **관찰 항목:** 판정하지 않고 표시·비교만 하는 값. 업체 주장은 관찰 항목(표시만)으로 두며 판정·계산 입력에 쓰지 않는다
- **참고값:** 질량, 높이 (판정 대상 아님)

## 2. 원문 KPI·요구 (중간 과제 해석 유지)
| 항목 | 값 | 출처 |
|---|---|---|
| 정합 반복정밀도 | ±1 μm | PBL 7쪽 |
| 펄스 히터 최고 온도 | 400 ℃ | PBL 7쪽 |
| 최대 본딩 하중 | 50 N | PBL 7쪽 |
| 풋프린트 (가로·세로) | ≤ 600 mm | PBL 7쪽 |
| 피드백 주기 | 10 ms | PBL 9쪽 |

## 3. 시편 조건
| 항목 | 값 | 구분 | 근거 |
|---|---|---|---|
| 더미 다이 크기 | 5 × 5 mm | 설계 목표 | 중간 과제 DoE와 같은 크기 |
| 다이 두께 (기본) | 100 μm | 설계 목표 | 중간 보고서의 최소 취급 두께 (이젝터 핀 크랙 회피, 0917 공정 43쪽) |
| 다이 두께 (비교용 선택) | 50 μm | 설계 목표 | 실제 HBM 코어 다이는 30~50 μm 수준 (Semiconductor Engineering, "HBM4 Sticks With Microbumps", 2026). 박형 다이 휨 비교용 |
| 범프 | Cu pillar + 솔더 캡 | 설계 목표 | 1001 플립칩 42쪽, 중간 보고서 4.9절 |
| 층 수 | 2 / 4 / 8 / 12 (최대 12) | 설계 목표 | 현재 양산 HBM 12단. 휨·열 이력 누적을 보이기 위함 |
| 층간 간격 | 기본 15 μm, 선택 범위 7~30 μm, 20 μm는 "시험 칩" 선택지 | 문헌값 | [Lee et al., ECTC 2023](https://conferences.computer.org/ectc/pdfs/ECTC2023-1NkkviSxgDnmPjptC1ysqm/349800a878/349800a878.pdf): SK hynix MR-MUF 8단 15 μm. [Samsung TC-NCF 12단](https://news.samsung.com/global/samsung-develops-industry-first-36gb-hbm3e-12h-dram): 7 μm. 조사 자료 1절 (`docs/research/params_research.md`) |

## 4. 판정 기준 (설계 목표)
| 항목 | 기준 | 구분 | 근거 |
|---|---|---|---|
| 층간 정렬 오차 | 층마다 아래층 대비 3σ ≤ 1 μm | 설계 목표 | 원문 KPI ±1 μm를 층 단위로 적용 |
| 층별 휨 한도 (주의) | 절대 휨이 층간 간격의 1/4 초과 (15 μm 기준 3.75 μm), 조기 경고 | 설계 목표 | 휨이 간격에 가까워지면 범프 미접촉으로 미접합(Open) 발생 (1001 플립칩 37쪽). 1/4은 설계 목표 |
| 층별 휨 한도 (불량) | ±20 μm 초과 (절대 휨 > 20 μm) | 설계 목표 (근거: 문헌값, SK hynix ECTC 2023) | SK hynix MR 접합 안정 범위 ±20 μm, 220 ℃ 측정 ([Lee et al., ECTC 2023](https://conferences.computer.org/ectc/pdfs/ECTC2023-1NkkviSxgDnmPjptC1ysqm/349800a878/349800a878.pdf)). 문헌 안정 범위를 교육용 불량 판정에 적용 |
| 결함 면적률 (보이드 + 미충전 합산) | ≤ 1 % 양호 / 1~5 % 주의 / > 5 % 불량 | 설계 목표 | 업체 기준 비공개. 참고: MIL-STD-883 Method 2030(다이 부착)은 단일 보이드 > 15 %, 모서리 보이드 > 10 %를 불합격으로 본다. 교육용으로 그보다 엄격하게 3단계 표시 |

## 5. 관찰 항목 (판정 없음)
| 항목 | 표시 방법 |
|---|---|
| 누적 정렬 오차 (맨 위층 ↔ 맨 아래층) | 층 수에 따른 증가 그래프 |
| 사이클 시간 | 두 모드 비교 |
| 층별 열 이력 (재가열 횟수, 최고 온도) | 두 모드 비교 |
| 업체 주장 (SK hynix / Samsung 인용) | 회사·출처와 함께 표시만, 판정 없음 |

## 6. 공정 조건 (강의 수치·문헌값·설계값·가정값 구분)
| 모드 | 항목 | 값 | 출처 |
|---|---|---|---|
| TC-NCF | 본딩 온도 | 250~300 ℃ | 1008 2.5D·3D 96쪽 |
| TC-NCF | 기본 본딩 하중 | 40 N (선택 25~50 N), 설계값 | 사용자 확정 2026-11-25 (HANDOFF 1절 #4). [Henkel 백서](https://dm.henkel-dam.com/is/content/henkel/Whitepaper_Formulating_NCP_and_NCF_for_Optimal_Results_final) 문헌 25~75 N. 원문 KPI 최대 50 N, 소프트웨어 경고 52 N까지 여유 12 N |
| TC-NCF | 승온 속도 | 20 K/s (장비 능력, 시뮬레이션 사용) / 문헌 80 ℃/s (비교값) | 중간 보고서 7장 히터 최대 22 K/s 및 10장 20 K/s 프로파일. [Henkel 백서](https://dm.henkel-dam.com/is/content/henkel/Whitepaper_Formulating_NCP_and_NCF_for_Optimal_Results_final). 교육 장비의 한계이며 히터 재설계는 범위 밖 |
| MR-MUF | 리플로우 피크 온도 | 240~260 ℃ (SAC 녹는점 약 217 ℃) | 1001 플립칩 40쪽 |
| 공통 | 원문 KPI 범위 | 히터 400 ℃, 하중 50 N 이하 | PBL 7쪽 |

하중, 유지 시간, 임시 고정 펄스 조건, NCF·EMC 물성은 `sim/params.json`에 출처와 함께 기록했다 (단계 3). 공개되지 않은 조건은 근거 문장이 있는 가정값으로 구분한다.

### MUF 몰딩 조건 (단계 4)

| 항목 | 값 | 구분 | params 키·근거 |
|---|---|---|---|
| 금형 온도 | 175 ℃ | 문헌값 | `mrmuf_process.mold_fill_temp` |
| 금형 압력 | 3 MPa | 문헌값 | `mrmuf_process.mold_pressure_applied` |
| 이송 시간 (충전 허용 시간) | 10 s | 문헌값 | `cycle.mold_fill_time` |
| 겔 시간 (충전 상한 경고) | 25 s | 문헌값 | `muf.gel_time` |
| 금형 내 경화 | 100 s | 문헌값 | `mrmuf_process.in_mold_cure_time` |
| 후경화 | 175 ℃ · 4 h | 문헌값 | `muf.cure_temp / muf.cure_time` |
| 간격 입구 유효 압력 | 1 MPa, 범위 0.1~3 MPa (0은 비교용) | 가정값 | `muf.applied_pressure` |
| 최대 필러 | 3 μm | 문헌값 | `muf.filler_max_size` |
| 간격/최대 필러 | ≥ 4 권고, < 4 경고, < 3 불량 | 문헌값 기반 교육용 규칙 | `muf.gap_to_filler_min_ratio` |
| 진공 절대압 | 19 kPa | 가정값 (문헌+가정) | `mrmuf_process.vacuum_level_abs` |

출처 URL·range·한국어 원구분은 `sim/params.json`, 변경 내역은 [단계 4 모델 보정 결과](stage4_model_update.md)에 기록했다. 금형 압력과 간격 입구 압력은 서로 다른 물리량이며, 충전 모델에는 간격 입구 유효 압력을 쓴다.

## 7. 시연에서 보여 줄 대표 시나리오
이번 재실행 결과를 그대로 기록했다. 층별 T(t) 전체 표본과 민감도·단계 3 비교는 [단계 4 모델 보정 결과](stage4_model_update.md)와 `sim/test/stage4_results.json`에 있다.

| 장면 | 비교 | 보여 줄 값 | 결과 |
|---|---|---|---|
| S1 열 이력 | 12단 두 모드 | 층별 T(t), 아래층 재가열 | TC-NCF 아래층 재가열 11회, 가접 노출 0회 / MR-MUF 아래층 재가열 0회, 가접 노출 11회; TC-NCF 층별 최고 온도 (208.54, 215.848, 222.069, 227.429, 232.093, 236.19, 239.815, 243.046, 245.944, 248.556, 250.924, 253.079) ℃; MR-MUF 층별 최고 온도 (250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250) ℃ |
| S2 정렬 | 12단, 같은 시드 초기 오차 | 누적 정렬 (MR 자기정렬 후) | TC-NCF 누적 (0.243771, -1.15648) μm / MR-MUF 누적 (0.0414668, 0.0118175) μm |
| S3 박형 다이 | 두 모드 100 → 50 μm | 최대 휨·판정 | TC-NCF 100 μm: 7.41317 μm 주의 / TC-NCF 50 μm: 30.7156 μm 불량 / MR-MUF 100 μm: 5.40673 μm 주의 / MR-MUF 50 μm: 22.1991 μm 불량 |
| S4 처리량 | 12단 | 본더/배치 후공정 분해 | TC-NCF 239.886/0 s / MR-MUF 40.686/14825.75 s; MR 후경화 14,400 s 포함 |
| S5 가압 충전 | MR 7/15/20 μm × 0/기본1/범위0.1·3 MPa | 충전 시간·미충전률·판정·필러/겔 경고 | 다음 표의 12개 실행값 |

S5 상세 결과 (면적률은 미충전만; 갇힌 보이드 정량 모델 없음):

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

MR의 가접 열 노출은 재가열 횟수와 구분한다. 두 모드에 4절의 같은 휨 기준을 적용했다. 업체의 박형 휨 우열은 이 선형 모델로 보장되지 않으며 장면은 실제 결과를 유지했다. 본더 점유 시간은 라인 UPH가 아니다.

근거: SK하이닉스 Hot Chips 2026 발표 요지 — TC+NCF는 생산성이 높고 열저항이 낮지만 칩 휨에 민감하고, MR+MUF는 박형 다이 휨에 강하지만 열저항이 높고 충전 가능 범위가 좁다 (ServeTheHome, "SK hynix HBM Packaging at Hot Chips 2026").

업체 주장은 **관찰 항목(표시만)**으로 구분하고, 판정·계산 입력에 쓰지 않으며 회사·출처와 함께 표시한다: SK hynix는 MR-MUF 접합 온도가 TC-NCF보다 14 ℃ 낮다고 주장한다 ([Lee et al., ECTC 2023](https://conferences.computer.org/ectc/pdfs/ECTC2023-1NkkviSxgDnmPjptC1ysqm/349800a878/349800a878.pdf)). Samsung 인용 시뮬레이션은 TC-NCF 접합부 열저항이 MR-MUF보다 35 % 낮다고 주장한다 ([Chip Scale Review 2024, p.47](https://chipscalereview.com/wp-content/uploads/flipbook/38/files/basic-html/page47.html), 임의 단위 A.U.). 조사 자료 7절과 `sim/params.json`의 `vendor_claims`에 기록했다.

## 8. 참고 자료
- PBL 강의자료 7·9쪽, 강의 0917 공정 43쪽, 1001 플립칩 37·40·42쪽, 1008 2.5D·3D 96쪽
- Semiconductor Engineering, "HBM4 Sticks With Microbumps, Postponing Hybrid Bonding": https://semiengineering.com/hbm4-sticks-with-microbumps-postponing-hybrid-bonding/
- ServeTheHome, "SK hynix HBM Packaging at Hot Chips 2026": https://www.servethehome.com/sk-hynix-hbm-packaging-at-hot-chips-2026/
- MIL-STD-883 Method 2030 기준 인용: "Method for Automated Nondestructive Analysis of Flip Chip Underfill" (SMTnet): https://www.smtnet.com/library/files/upload/Method_for_Automated_Nondestructive_Analysis_of_Flip_Chip_Underfill.pdf

- Lee et al., "A Study on the Advanced Chip to Wafer Stack for Better Thermal Dissipation of HBM", [ECTC 2023](https://conferences.computer.org/ectc/pdfs/ECTC2023-1NkkviSxgDnmPjptC1ysqm/349800a878/349800a878.pdf)
- 조사 원문 `research.md` 이관본: [docs/research/params_research.md](research/params_research.md) (inbox/04_params_research, Chat 조사, 2026-11-25)
