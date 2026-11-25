# 요구사항과 설계 목표 — 교육용 HBM 적층 본더

상태: 2026-11-25 사용자 확정. 가정값은 단계 3에서 조사 후 확정하고 `sim/params.json`에 기록한다.

## 1. 구분 규칙
- **원문 KPI·원문 요구:** PBL 강의자료에 적힌 수치. 판정 대상
- **설계 목표:** 이번 과제에서 근거를 두고 새로 정한 수치. 판정 대상
- **가정값:** 조사 전 임시 수치. 단계 3에서 조사 후 확정
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
| 층간 간격 | 20 μm | **가정값** | 단계 3에서 조사 후 확정 |

## 4. 판정 기준 (설계 목표)
| 항목 | 기준 | 근거 |
|---|---|---|
| 층간 정렬 오차 | 층마다 아래층 대비 3σ ≤ 1 μm | 원문 KPI ±1 μm를 층 단위로 적용 |
| 층별 휨 한도 | 층간 간격의 1/4 이하 (가정 간격 20 μm 기준 5 μm) | 휨이 간격에 가까워지면 범프 미접촉으로 미접합(Open) 발생 (1001 플립칩 37쪽). 간격 확정 시 함께 갱신 |
| 결함 면적률 (보이드 + 미충전 합산) | ≤ 1 % 양호 / 1~5 % 주의 / > 5 % 불량 | 업체 기준 비공개. 참고: MIL-STD-883 Method 2030(다이 부착)은 단일 보이드 > 15 %, 모서리 보이드 > 10 %를 불합격으로 본다. 교육용으로 그보다 엄격하게 3단계 표시 |

## 5. 관찰 항목 (판정 없음)
| 항목 | 표시 방법 |
|---|---|
| 누적 정렬 오차 (맨 위층 ↔ 맨 아래층) | 층 수에 따른 증가 그래프 |
| 사이클 시간 | 두 모드 비교 |
| 층별 열 이력 (재가열 횟수, 최고 온도) | 두 모드 비교 |

## 6. 공정 조건 (가정값, 강의 수치 기반)
| 모드 | 항목 | 값 | 출처 |
|---|---|---|---|
| TC-NCF | 본딩 온도 | 250~300 ℃ | 1008 2.5D·3D 96쪽 |
| MR-MUF | 리플로우 피크 온도 | 240~260 ℃ (SAC 녹는점 약 217 ℃) | 1001 플립칩 40쪽 |
| 공통 | 원문 KPI 범위 | 히터 400 ℃, 하중 50 N 이하 | PBL 7쪽 |

하중, 유지 시간, 임시 고정 펄스 조건, NCF·EMC 물성은 단계 3에서 조사해 `sim/params.json`에 출처와 함께 기록한다.

## 7. 시연에서 보여 줄 대표 시나리오
| 시나리오 | 조건 | 기대 결과 |
|---|---|---|
| 박형 다이 휨 | 50 μm, 12단, TC-NCF | 휨 한도 초과 알람 |
| 좁은 간격 충전 | 간격 축소, MR-MUF | 결함 면적률 주의 또는 불량 |

근거: SK하이닉스 Hot Chips 2026 발표 요지 — TC+NCF는 생산성이 높고 열저항이 낮지만 칩 휨에 민감하고, MR+MUF는 박형 다이 휨에 강하지만 열저항이 높고 충전 가능 범위가 좁다 (ServeTheHome, "SK hynix HBM Packaging at Hot Chips 2026").

## 8. 참고 자료
- PBL 강의자료 7·9쪽, 강의 0917 공정 43쪽, 1001 플립칩 37·40·42쪽, 1008 2.5D·3D 96쪽
- Semiconductor Engineering, "HBM4 Sticks With Microbumps, Postponing Hybrid Bonding": https://semiengineering.com/hbm4-sticks-with-microbumps-postponing-hybrid-bonding/
- ServeTheHome, "SK hynix HBM Packaging at Hot Chips 2026": https://www.servethehome.com/sk-hynix-hbm-packaging-at-hot-chips-2026/
- MIL-STD-883 Method 2030 기준 인용: "Method for Automated Nondestructive Analysis of Flip Chip Underfill" (SMTnet): https://www.smtnet.com/library/files/upload/Method_for_Automated_Nondestructive_Analysis_of_Flip_Chip_Underfill.pdf
