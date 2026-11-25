# 요구사항과 설계 목표 — 교육용 HBM 적층 본더

상태: 2026-11-25 사용자 확정 (단계 3에서 층간 간격·휨·하중·승온 속도 갱신)

## 1. 구분 규칙
- **원문 KPI·원문 요구:** PBL 강의자료에 적힌 수치. 판정 대상
- **설계 목표:** 이번 과제에서 근거를 두고 새로 정한 수치. 판정 대상
- **문헌값:** 공개 문헌 수치. 판정 대상 아님, 시뮬레이션 입력
- **설계값:** 사용자 확정 장비·공정 설정. 원문 KPI와 구분
- **가정값:** 공개 수치가 없어 근거를 붙인 교육용 입력. `sim/params.json`에 모아 기록
- **관찰 항목:** 판정하지 않고 표시·비교만 하는 값
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
| 항목 | 기준 | 근거 |
|---|---|---|
| 층간 정렬 오차 | 층마다 아래층 대비 3σ ≤ 1 μm | 원문 KPI ±1 μm를 층 단위로 적용 |
| 층별 휨 한도 (주의) | 절대 휨이 층간 간격의 1/4 초과 (15 μm 기준 3.75 μm), 조기 경고 | 휨이 간격에 가까워지면 범프 미접촉으로 미접합(Open) 발생 (1001 플립칩 37쪽). 1/4은 설계 목표 |
| 층별 휨 한도 (불량) | ±20 μm 초과 (절대 휨 > 20 μm) | SK hynix MR 접합 안정 범위 ±20 μm, 220 ℃ 측정 ([Lee et al., ECTC 2023](https://conferences.computer.org/ectc/pdfs/ECTC2023-1NkkviSxgDnmPjptC1ysqm/349800a878/349800a878.pdf)). 문헌 안정 범위를 교육용 불량 판정에 적용 |
| 결함 면적률 (보이드 + 미충전 합산) | ≤ 1 % 양호 / 1~5 % 주의 / > 5 % 불량 | 업체 기준 비공개. 참고: MIL-STD-883 Method 2030(다이 부착)은 단일 보이드 > 15 %, 모서리 보이드 > 10 %를 불합격으로 본다. 교육용으로 그보다 엄격하게 3단계 표시 |

## 5. 관찰 항목 (판정 없음)
| 항목 | 표시 방법 |
|---|---|
| 누적 정렬 오차 (맨 위층 ↔ 맨 아래층) | 층 수에 따른 증가 그래프 |
| 사이클 시간 | 두 모드 비교 |
| 층별 열 이력 (재가열 횟수, 최고 온도) | 두 모드 비교 |

## 6. 공정 조건 (강의 수치·문헌값·설계값·가정값 구분)
| 모드 | 항목 | 값 | 출처 |
|---|---|---|---|
| TC-NCF | 본딩 온도 | 250~300 ℃ | 1008 2.5D·3D 96쪽 |
| TC-NCF | 기본 본딩 하중 | 40 N (선택 25~50 N), 설계값 | 사용자 확정 2026-11-25 (HANDOFF 1절 #4). [Henkel 백서](https://dm.henkel-dam.com/is/content/henkel/Whitepaper_Formulating_NCP_and_NCF_for_Optimal_Results_final) 문헌 25~75 N. 원문 KPI 최대 50 N, 소프트웨어 경고 52 N까지 여유 12 N |
| TC-NCF | 승온 속도 | 20 K/s (장비 능력, 시뮬레이션 사용) / 문헌 80 ℃/s (비교값) | 중간 보고서 7장 히터 최대 22 K/s 및 10장 20 K/s 프로파일. [Henkel 백서](https://dm.henkel-dam.com/is/content/henkel/Whitepaper_Formulating_NCP_and_NCF_for_Optimal_Results_final). 교육 장비의 한계이며 히터 재설계는 범위 밖 |
| MR-MUF | 리플로우 피크 온도 | 240~260 ℃ (SAC 녹는점 약 217 ℃) | 1001 플립칩 40쪽 |
| 공통 | 원문 KPI 범위 | 히터 400 ℃, 하중 50 N 이하 | PBL 7쪽 |

하중, 유지 시간, 임시 고정 펄스 조건, NCF·EMC 물성은 `sim/params.json`에 출처와 함께 기록했다 (단계 3). 공개되지 않은 조건은 근거 문장이 있는 가정값으로 구분한다.

## 7. 시연에서 보여 줄 대표 시나리오
기대 결과는 **예상**이다. 단계 3 모델 결과가 다르면 결과대로 적고, 시나리오는 단계 4에서 실제 결과를 보고 확정한다.

| 시나리오 | 조건 | 예상 결과 |
|---|---|---|
| 박형 다이 휨 | 50 μm, 12단, TC-NCF | 휨 한도 초과 알람 |
| 좁은 간격 충전 | 간격 축소, MR-MUF | 결함 면적률 주의 또는 불량 |

근거: SK하이닉스 Hot Chips 2026 발표 요지 — TC+NCF는 생산성이 높고 열저항이 낮지만 칩 휨에 민감하고, MR+MUF는 박형 다이 휨에 강하지만 열저항이 높고 충전 가능 범위가 좁다 (ServeTheHome, "SK hynix HBM Packaging at Hot Chips 2026").

업체 주장은 판정에 쓰지 않고 회사·출처와 함께 표시한다: SK hynix는 MR-MUF 접합 온도가 TC-NCF보다 14 ℃ 낮다고 주장한다 ([Lee et al., ECTC 2023](https://conferences.computer.org/ectc/pdfs/ECTC2023-1NkkviSxgDnmPjptC1ysqm/349800a878/349800a878.pdf)). Samsung 인용 시뮬레이션은 TC-NCF 접합부 열저항이 MR-MUF보다 35 % 낮다고 주장한다 ([Chip Scale Review 2024, p.47](https://chipscalereview.com/wp-content/uploads/flipbook/38/files/basic-html/page47.html), 임의 단위 A.U.). 조사 자료 7절과 `sim/params.json`의 `vendor_claims`에 기록했다.

## 8. 참고 자료
- PBL 강의자료 7·9쪽, 강의 0917 공정 43쪽, 1001 플립칩 37·40·42쪽, 1008 2.5D·3D 96쪽
- Semiconductor Engineering, "HBM4 Sticks With Microbumps, Postponing Hybrid Bonding": https://semiengineering.com/hbm4-sticks-with-microbumps-postponing-hybrid-bonding/
- ServeTheHome, "SK hynix HBM Packaging at Hot Chips 2026": https://www.servethehome.com/sk-hynix-hbm-packaging-at-hot-chips-2026/
- MIL-STD-883 Method 2030 기준 인용: "Method for Automated Nondestructive Analysis of Flip Chip Underfill" (SMTnet): https://www.smtnet.com/library/files/upload/Method_for_Automated_Nondestructive_Analysis_of_Flip_Chip_Underfill.pdf

- Lee et al., "A Study on the Advanced Chip to Wafer Stack for Better Thermal Dissipation of HBM", [ECTC 2023](https://conferences.computer.org/ectc/pdfs/ECTC2023-1NkkviSxgDnmPjptC1ysqm/349800a878/349800a878.pdf)
- 조사 원문 `research.md` 이관본: [docs/research/params_research.md](research/params_research.md) (inbox/04_params_research, Chat 조사, 2026-11-25)
