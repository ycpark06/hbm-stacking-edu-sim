출처: inbox/04_params_research, Chat 조사, 2026-11-25

# HBM 적층 본더 시뮬레이션 파라미터 조사 (TC-NCF vs MR-MUF)

작성일: 2026-11-25 / 대상: UNIST MSE489 기말 PBL 브라우저 시뮬레이션
원칙: 모든 수치에는 출처 URL을 붙였다. 출처가 없으면 "미확인"으로 적고 범위를 "가정"으로 따로 표시했다. 인용은 짧게 의역했다.

신뢰도 기준
- 높음: 동료심사 논문, 학회 논문(ECTC/IMAPS), 회사 공식 뉴스룸, 표준 및 정부기관 DB(NIST), 제조사 TDS
- 중간: 전문 매체(SemiEngineering, Chip Scale Review, ServeTheHome, TrendForce), 대학 강의용 물성 DB
- 낮음: 마케팅 페이지, 판독이 불확실한 표, 개념 시뮬레이션(A.U.)

---

## 1. HBM 층간 간격, 마이크로범프, 다이 두께

| 항목 | 값(범위) | 단위 | 조건 | 출처(제목+URL) | 신뢰도 | 비고 |
|---|---|---|---|---|---|---|
| 칩 간 간격(gap), TC-NCF 양산 | 7 | μm | Samsung HBM3E 12H, "업계 최소 간격"이라 밝힘 | Samsung Develops Industry-First 36GB HBM3E 12H DRAM, https://news.samsung.com/global/samsung-develops-industry-first-36gb-hbm3e-12h-dram | 높음 | NCF 두께도 줄였다고 하나 수치 없음 |
| 칩 간 간격, MR-MUF | 15 | μm | SK hynix 8Hi HBM, 패키지 높이 720 μm | Lee et al., "A Study on the Advanced Chip to Wafer Stack for Better Thermal Dissipation of HBM", ECTC 2023, https://conferences.computer.org/ectc/pdfs/ECTC2023-1NkkviSxgDnmPjptC1ysqm/349800a878/349800a878.pdf | 높음 | 이번 조사의 핵심 근거 |
| 범프 적층 일반 간격 | 약 30 | μm | 범프 기반 적층의 일반적 다이 간 간격(세대 미지정) | Interconnect Innovations In HBM: Part 1, https://semiengineering.com/interconnect-innovations-in-high-bandwidth-memory-part-1/ | 중간 | 오래된 세대나 일반론으로 보임 |
| 16단 간격 변화 | 기존 대비 약 1/2 | - | SK hynix HBM4 16H | SK hynix HBM Packaging at Hot Chips 2026, https://www.servethehome.com/sk-hynix-hbm-packaging-at-hot-chips-2026/ | 중간 | 절대값 없음 |
| 마이크로범프 피치 | 약 40 (과거) → HBM4에서 더 작아짐 | μm | 업계 일반 | HBM4 Sticks With Microbumps, https://semiengineering.com/hbm4-sticks-with-microbumps-postponing-hybrid-bonding/ | 중간 | |
| 마이크로범프 피치 하한(리플로) | 20 | μm | 솔더 리플로 μbump 적층의 도달 가능 피치 | Chip Scale Review Mar-Apr 2024 p.48, https://chipscalereview.com/wp-content/uploads/flipbook/38/files/basic-html/page48.html | 중간 | |
| 시험용 TSV 적층 범프(TV-II) | 피치 55, Cu 기둥 지름 25, 기둥 높이 25, 솔더 높이 5 | μm | Dow NCF 평가용 시험 칩 | Anzures et al., "NCF Underfill: Materials, Performance, and Evolution...", IMAPS Device Packaging 2016, https://imapsource.org/article/67660.pdf | 높음 | 패드 지름 25~30 μm |
| 시험용 범프(TV-I) | 피치 80(주변)/300(중앙), 기둥 지름 50, 높이 25, 솔더 15, 다이 두께 100 | μm | 위와 동일 | 위와 동일 | 높음 | |
| 무연 μbump 지름/접합 후 높이 | 약 25 / 평균 16 | μm | IBM 3D 칩 적층 열저항 측정 | Measured Thermal Resistance of Microbumps in 3D Chip Stacks, https://www.electronics-cooling.com/2013/03/measured-thermal-resistance-of-microbumps-in-3d-chip-stacks/ | 높음 | 피치 50/71/100 μm |
| NCF/NCP 적용 영역 | 간격 <30, 피치 <80, 기둥 지름 <25 | μm | Henkel 응용 기준 | Henkel 백서 "Formulating NCP and NCF for Optimal Results", https://dm.henkel-dam.com/is/content/henkel/Whitepaper_Formulating_NCP_and_NCF_for_Optimal_Results_final | 높음 | |
| DRAM 다이 두께 | 약 60 (2020년 기준), 향후 약 50 | μm | TSMC 발표 소개 | Thermo-Compression Bonding for Large Stacked HBM Die, https://semiwiki.com/semiconductor-manufacturers/tsmc/287473-thermo-compression-bonding-for-large-stacked-hbm-die | 중간 | |
| DRAM 다이 두께 | 30~50 | μm | 현재 업계(Brewer Science 발언) | https://semiengineering.com/hbm4-sticks-with-microbumps-postponing-hybrid-bonding/ | 중간 | |
| DRAM 다이 두께(16단) | 30 | μm | SK hynix HBM4 16H | TrendForce 2026-01-13, https://www.trendforce.com/news/2026/01/13/news-sk-hynix-may-stick-with-mr-muf-for-hbm4-16-high-despite-asmpt-tc-bonder-orders/ | 중간 | |
| 12단 다이 두께 감소 | 8단 대비 40% 얇음 | - | SK hynix HBM3 12H | Rulebreaker Revolutions: MR-MUF, https://news.skhynix.com/en/rulebreaker-revolutions-mr-muf-unlocks-hbm-heat-control/ | 높음 | |
| 패키지 높이 한계 | 720 → 775 | μm | JEDEC(HBM4에서 완화) | https://semiengineering.com/hbm4-sticks-with-microbumps-postponing-hybrid-bonding/ | 중간 | |

정리: 양산 HBM3/3E의 층간 간격은 7 μm(TC-NCF, Samsung)에서 15 μm(MR-MUF, SK hynix 8Hi) 사이로 공개되어 있다. 시험 칩과 교육용 수준에서는 16~30 μm가 흔하다.

## 2. NCF (비전도성 필름)

| 항목 | 값(범위) | 단위 | 조건 | 출처 | 신뢰도 | 비고 |
|---|---|---|---|---|---|---|
| 필름 두께 | 20 | μm | Dow TV-II 라미네이션 필름 | Anzures et al., IMAPS 2016, https://imapsource.org/article/67660.pdf | 높음 | 솔더 캡 위로 3~5 μm 남도록 설계 |
| 최저 용융 점도 | 30,000 (130 ℃) | Pa·s | Dow GEN-1 | 위와 동일 | 높음 | 같은 논문에서 일반 NCF는 10³~10⁴ Pa·s(100~160 ℃) |
| 최저 용융 점도 | 1,727 (138 ℃) | Pa·s | Henkel NCF | Henkel 백서(위 URL) | 높음 | |
| 경화(DSC) | 시작 141, 피크 166 | ℃ | Dow GEN-1, 10 ℃/min | Anzures et al. | 높음 | 160 ℃ 이상에서 빠르게 경화 |
| 경화(DSC) | 시작 207, 피크 250 | ℃ | Dow GEN-2(저점도형) | Anzures et al. | 높음 | 저점도형은 보이드가 더 많았다고 보고 |
| 경화 반응속도 상수(Kamal 등) | 미확인 | - | - | - | - | 가정 필요 |
| 본딩 힘 | 90 | N | Dow TV-I, 헤드 300 ℃, 스테이지 100 ℃, 다이 250 ℃(가장자리 235 ℃) | Anzures et al. | 높음 | 다이 크기 미기재 |
| 본딩 힘 | 100~400 | N | Dow TV-II(약 36,000 I/O) | Anzures et al. | 높음 | 범프당 약 2.8~11 mN(계산값) |
| 본딩 힘 | 25/50/75 시험, 25 N 초과 권장 | N | Henkel NCF TCB 연구 | Henkel 백서 | 높음 | |
| 본딩 단계 시간 | 접근 3.2, 승온 2.5, 유지 3.2, 냉각 1.7 (합계 10 s 미만 목표) | s | Dow TV-I, 승온 80 ℃/s | Anzures et al. | 높음 | |
| 승온 속도 | 60~100 시험, 80 권장 | ℃/s | Henkel NCF | Henkel 백서 | 높음 | 80 ℃/s 미만에서 보이드 적음 |
| 접촉 온도 | 130~210 시험, 약 170 이하 권장 | ℃ | Henkel NCF | Henkel 백서 | 높음 | 보이드에 큰 영향 없음 |
| 스테이지 온도 | 100 | ℃ | Dow TV-I | Anzures et al. | 높음 | |
| 정렬 온도 | 100~150 | ℃ | NCF 사용 시 | Kulicke & Soffa, "High Productivity Thermo-Compression Flip Chip Bonding", IMAPS, https://imapsource.org/api/v1/articles/56216-high-productivity-thermo-compression-flip-chip-bonding.pdf | 높음 | 필름이 너무 묽어지지 않게 |
| 라미네이션 | 75~80 ℃, 0.5 MPa, 진공 30 s, 가압 30~60 s | - | Dow | Anzures et al. | 높음 | Henkel은 50 ℃, 0.5 MPa |
| 필러 함량 | 40 | wt% | Henkel NCF | Henkel 백서 | 높음 | |
| CTE1 / CTE2 | 40 / 137 | ppm/℃ | Henkel NCF | Henkel 백서 | 높음 | |
| CTE | 28 (GEN-1), 25 (GEN-2) | ppm/℃ | Dow | Anzures et al. | 높음 | |
| 저장탄성률 | 6.7 (25 ℃), 0.13 (250 ℃) | GPa | Henkel NCF | Henkel 백서 | 높음 | |
| 탄성률 | 5.8 (GEN-1), 7.5 (GEN-2) | GPa | Dow | Anzures et al. | 높음 | |
| Tg | 166 (Henkel), 122/92 (Dow GEN-1/2) | ℃ | - | 위 두 출처 | 높음 | |
| CTE(무필러 NCF) | 18~22 | ppm/℃ | AI Technology 제품 | https://www.aitechnology.com/non-conductive-film-nfc-adhesive-for-thermo-compression-tc-bonding-soldering-underfilling-and-stress-management/ | 낮음 | 마케팅 자료 |
| NCF 열전도도 | 미확인 | W/m·K | - | - | - | 가정 0.2~0.5 |
| 스퀴즈 흐름 모델 | 기존 스퀴즈 흐름 이론을 NCF 틱소트로피 포함해 적용, 측정 간격 변화와 일치 | - | 3D TSV NCF 본딩 | Choi et al., J. Electron. Mater. 43 (2014) 4214, https://link.springer.com/10.1007/s11664-014-3319-7 | 높음 | 수치는 본문 유료 |

## 3. MR-MUF / 액상 EMC / 모세관 언더필

| 항목 | 값(범위) | 단위 | 조건 | 출처 | 신뢰도 | 비고 |
|---|---|---|---|---|---|---|
| MUF 필러 함량 | 77 | % | SK hynix 개선 MUF | Lee et al., ECTC 2023(위 URL) | 높음 | |
| MUF 최대 필러 크기 | 3 | μm | 위와 동일 | 위와 동일 | 높음 | 간격 15 μm와 정합 |
| MUF CTE(α1) | 18 | ppm/℃ | 위와 동일 | 위와 동일 | 높음 | |
| MUF 탄성률 | 11 | GPa | 위와 동일 | 위와 동일 | 높음 | |
| MUF용 수지 후보(LMC C 채택) | Tg 152, α1 8, α2 21, 탄성률 12.5 | ℃, ppm/℃, GPa | 위와 동일 | 위와 동일 | 높음 | |
| 상용 MUF | Tg 145~170, CTE1 9~20, CTE2 38~64, 굽힘탄성률 16~26, 최대 필러 10~20 | ℃, ppm/℃, GPa, μm | Panasonic LEXCM CF 시리즈 | https://industrial.panasonic.com/sa/products/pt/adv-sc-pkg-em/ecommuf | 높음 | 점도, 경화 조건은 미공개 |
| MUF 필러 함량 일반 | 80 이상 | wt% | 리뷰 | Plachý et al., "Underfill: A Review...", Polymers 17 (2025) 2206, https://mdpi.com/2073-4360/17/16/2206 | 높음 | CUF는 약 70 wt% 이하 |
| 필러 최대 크기 규칙 | 간격의 1/3 이하 | - | MUF 및 보드 언더필 | 위와 동일 | 높음 | |
| 예열 효과 | 70~100 ℃ 예열로 점도 크게 감소 | - | CUF 일반 | 위와 동일 | 높음 | 수치 없음 |
| 유동 시간 식 | t = 3μL²/(hγcosθ) (Schwiebert 1996) | - | 평행판 모세관 | 위와 동일 | 높음 | 범프 장애물 무시 |
| CUF 점도 | 13 (25 ℃, 5 rpm) | Pa·s | Henkel UF 8807 | https://datasheets.tdx.henkel.com/LOCTITE-ECCOBOND-UF-8807-en_GL.pdf | 높음 | 열전도도 0.6 W/m·K, CTE 28/83, Tg ≥130 ℃ |
| CUF 점도 | 22.1 (5 rpm, 온도 미기재) | Pa·s | Henkel UF 8830S | https://datasheets.tdx.henkel.com/LOCTITE-ECCOBOND-UF-8830S-en_GL.pdf | 높음 | CTE 25/100, Tg 118, 25~30 μm 협간격용 |
| CUF 경화 | 150 ℃ 2 h (UF 8830S), 165 ℃ 30 min (UF 8807) | - | TDS 권장 | 위 두 TDS | 높음 | |
| 언더필 표면장력 | 0.04 | N/m | 언더필 3D 유동 해석 입력값 | Hsu et al., "3D Simulation of Fine Pitch Underfill Encapsulation" (Moldex3D), https://www.moldex3d.com/assets/2011/09/3D-Simulation-of-Fine-Pitch-Underfill-Encapsulation.pdf | 중간 | 해석용 입력값 |
| 언더필 접촉각 | 10 | ° | 위와 동일 | 위와 동일 | 중간 | |
| 액상 MUF 열전도도 | 4 (BN), 8 (다이아몬드) | W/m·K | AI Technology 제품 | https://www.aitechnology.com/molding-underfill-muf-for-mass-reflow-mr-liquid-underfilling-encapsulation-with-thermal-dissipation-enhancement/ | 낮음 | 마케팅 자료 |
| SK hynix 신규 EMC 방열 | 기존 MR-MUF EMC 대비 1.6배 | - | Advanced MR-MUF | Rulebreaker Revolutions(위 URL) | 높음 | 열전도도 값은 미공개 |
| MUF 점도(충전 온도) | 미확인 | Pa·s | - | - | - | 가정 필요 |
| MUF 표면장력/접촉각 | 미확인 | - | - | - | - | CUF 값으로 대체 |
| MR-MUF "칩 제어" 순간 가열 | 쌓을 때마다 순간 고열로 위 칩 범프를 아래 칩의 얇은 패드에 융착해 고정하고 휨을 억제 | - | Advanced MR-MUF | Rulebreaker Revolutions(위 URL) | 높음 | 온도, 시간, 힘은 미공개 |
| MR 공정 압력 | 매스 리플로 본딩은 본딩 압력을 쓰지 않음 | - | SK hynix | Lee et al., ECTC 2023 | 높음 | |
| 칩 휨 허용 | ±20 (기본), ±30 (평면 실장 순서 적용) | μm | 220 ℃에서 휨 측정, MR 접합 안정 범위 | Lee et al., ECTC 2023 | 높음 | |

## 4. 매스 리플로 프로파일, 솔더 표면장력, 자기정렬

| 항목 | 값(범위) | 단위 | 조건 | 출처 | 신뢰도 | 비고 |
|---|---|---|---|---|---|---|
| 예열/소크 | 150~200 ℃, 60~120 s | - | 무연 분류 프로파일 | Microchip, Pb-free Solder Reflow, https://www.microchip.com/content/dam/mchp/documents/FPGA/ProductDocuments/PackagingSpecifications/solder_reflow_leadfree.pdf | 높음 | J-STD-020 계열 분류 프로파일 |
| 승온 속도(소크 끝→피크) | 최대 3 | ℃/s | 위와 동일 | 위와 동일 | 높음 | |
| 액상선(TL) | 217 | ℃ | SAC 기준 | 위와 동일 | 높음 | |
| 액상선 위 시간(TAL) | 60~150 | s | 위와 동일 | 위와 동일 | 높음 | |
| 피크 온도 | 245~260 | ℃ | 패키지 두께, 부피에 따라 다름(1.6 mm 미만은 260) | 위와 동일 | 높음 | |
| 피크 ±5 ℃ 유지 | 30 | s | 위와 동일 | 위와 동일 | 중간 | 허용오차 판독 불명확 |
| 냉각 속도 | 최대 6 | ℃/s | 위와 동일 | 위와 동일 | 높음 | |
| 25 ℃→피크 총 시간 | 최대 8 | min | 위와 동일 | 위와 동일 | 높음 | |
| Sn-3.5Ag 융점 | 221 (공정점) | ℃ | - | NIST Sn-Ag Overview, https://www.msed.nist.gov/solder/clech/Sn-Ag_Overview.htm | 높음 | |
| SAC305 용융 범위 | 217~220 | ℃ | - | Kappalloy SAC305 TDS, https://www.kappalloy.com/pub/media/pdf/TDS%20280%20SAC305%20Tin%20Silver%20Copper.pdf | 높음 | |
| Sn-3.5Ag 표면장력 | 0.431 (공기), 0.493 (질소) | N/m | 액상선 +50 ℃ | NIST Sn-Ag Other Properties, https://www.msed.nist.gov/solder/clech/Sn-Ag_Other.htm | 높음 | Glazer(1994) 인용 |
| 자기정렬 복원력 모델 | 소변위(u≪h)에서 k ≈ 2γL/h, F = −2γL·u/√(h²+u²) | - | 정사각 패드 한 쌍 사이 메니스커스 | Mastrangeli et al., EPFL, https://infoscience.epfl.ch/record/205124/files/Mastrangeli-MufNaf2014.pdf?version=1 | 높음 | 후보식 k≈2γw/h가 이 결과와 같음. 변위가 커지면 강성이 절반, 그 뒤 0이 되는 3단계 |
| 자기정렬 모델 가정 | 준정적, 중력 무시, 일정 간격과 부피, 접촉각 <90° | - | 위와 동일 | 위와 동일 | 높음 | 접합 전 용융 상태에만 적용 |

## 5. 열 및 휨 해석용 물성

| 재료 | 항목 | 값 | 단위 | 출처 | 신뢰도 | 비고 |
|---|---|---|---|---|---|---|
| Si | CTE | 2.6 | ppm/K | CERN SSD, General Characteristics of Silicon, https://ssd-rd.web.cern.ch/Data/Si-General.html | 높음 | 다른 자료는 약 2.5 |
| Si | 영률 | 130 [100], 170 [110], 185 [111] | GPa | Ioffe Si mechanical, https://www.ioffe.ru/SVA/NSM/Semicond/Si/mechanic.html | 높음 | |
| Si | 포아송비 | 0.28 [100] | - | 위와 동일 | 높음 | |
| Si | 밀도 | 2329 | kg/m³ | 위와 동일 | 높음 | |
| Si | 열전도도 | 140~163 (자료별), 150 | W/m·K | Kiel 대학 강의자료, https://www.tf.uni-kiel.de/matwis/amat/semi_en/kap_3/backbone/r3_1_3.html / CERN(위) | 높음 | 얇은 다이는 더 낮을 수 있음 |
| Si | 비열 | 703 (25 ℃) | J/kg·K | Kiel(위) | 높음 | CERN은 678 |
| Cu | 영률 / 포아송비 | 130 / 0.34 | GPa / - | MIT 6.777 Material DB, https://www.mit.edu/~6.777/matprops/copper.htm | 중간 | 원출처 Freund & Suresh |
| Cu | 밀도 / 열전도도 / 비열 | 8960 / 401 / 385 | kg/m³, W/m·K, J/kg·K | 위와 동일 | 중간 | 원출처 CRC Handbook |
| Cu | CTE | 17 | ppm/K | HyperPhysics 20 ℃ 열팽창 표, https://hyperphysics.gsu.edu/hbase/Tables/thexp.html | 중간 | |
| Sn-3.5Ag | CTE / 포아송비 / 밀도 | 21.5 / 0.4 / 7500 | ppm/℃, -, kg/m³ | NIST Sn-Ag Other(위) | 높음 | |
| Sn-3.5Ag | 영률 | 미확인(그래프만) | GPa | NIST Sn-Ag Other(위) | - | 가정 40~55 |
| SAC(Castin) | 열전도도 | 57.26 | W/m·K | NIST Sn-Ag-Cu Other, https://www.msed.nist.gov/solder/clech/Sn-Ag-Cu_Other.htm | 높음 | IBM 측정 모델은 솔더 35 W/m·K 사용 |
| SAC305 | 비열 / 밀도 | 232 / 7370 | J/kg·K, kg/m³ | Kappalloy TDS(위) | 높음 | |
| NCF | CTE, 탄성률, Tg | 2장 표 참고 | - | Henkel, Dow | 높음 | |
| NCF | 밀도, 비열, 열전도도 | 미확인 | - | - | - | 가정: 1.4~1.6 g/cm³, 1000~1300 J/kg·K, 0.2~0.5 W/m·K |
| CUF | 비중 / 열전도도 | 1.6 / 0.6 | -, W/m·K | Henkel UF 8830S, UF 8807 TDS | 높음 | NCF 대용 근거 |
| EMC(일반 몰드) | 비중, 열전도도, CTE1/2, 굽힘탄성률, 필러 | 2.02, 0.9, 8/31, 24.9, 약 89~90 wt% | - | Hitachi CEL-9220HF10 TDS, https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/196/TDS-of-CEL_2D00_9220HF10.pdf | 낮음 | 표 판독이 섞여 있어 재확인 필요 |
| MUF(HBM) | CTE, 탄성률 | 18 ppm/℃, 11 GPa | - | SK hynix ECTC 2023 | 높음 | |
| μbump+언더필층 | 단위 열저항 | 8.0 (피치 50), 15.5 (71), 19.0 (100) | ℃·mm²/W | IBM 측정, electronics-cooling(위) | 높음 | 범프 지름 25 μm, 높이 16 μm, 언더필 0.55 W/m·K |
| μbump+언더필층 | 유효 열전도도(계산) | 약 2.0 | W/m·K | 위 값으로 계산(16 μm / 8 ℃·mm²/W) | 중간 | 계산값이며 논문 수치는 아님 |

## 6. 처리량과 사이클 시간

| 항목 | 값(범위) | 단위 | 조건 | 출처 | 신뢰도 | 비고 |
|---|---|---|---|---|---|---|
| TCB 열사이클(현행 장비) | 7~15 | s/배치 | 플립칩 TCB | K&S IMAPS(위 URL) | 높음 | 일반 플립칩보다 크게 느림 |
| TCB 최소 사이클 | 약 1.2 (180→260→180 ℃) | s | 200 ℃/s 승온, 100 ℃/s 냉각 | 위와 동일 | 높음 | |
| TCB 측정 사이클 | 약 2.5 (160→280→160, 유지 1 s), 약 4 (60→280→60) | s | 위와 동일 | 위와 동일 | 높음 | |
| TCB 처리량 | 300~400 (현행 듀얼 헤드), 목표 1000~2000 | UPH | 위와 동일 | 위와 동일 | 높음 | |
| NCF TCB 1회 | 10 s 미만 목표 | s | Dow TV-I | Anzures et al. | 높음 | |
| 매스 리플로 1회 | 25 ℃→피크 최대 8 min | min | 분류 프로파일 | Microchip(위) | 높음 | 배치 단위로 웨이퍼 전체를 한 번에 처리 |
| MR-MUF 칩당 가접 시간 | 미확인 | s | - | - | - | 가정 0.5~2 s |
| MR-MUF 효율 주장 | 전체 적층을 한 번에 가열·접합해 칩마다 필름을 쓰는 TC-NCF보다 효율적 | - | SK hynix 주장 | Rulebreaker Revolutions(위) | 높음 | 정량값 없음 |

## 7. TC-NCF vs MR-MUF 공개 비교

| 주장 | 내용 | 출처 | 신뢰도 | 비고 |
|---|---|---|---|---|
| 열(SK hynix) | Advanced CoW MR-MUF 구조에서 메모리 칩 평균 최대 접합온도가 TC-NCF보다 14 ℃ 낮음 | Lee et al., ECTC 2023 | 높음 | 같은 회사 내부 비교 |
| 열(SK hynix) | EMC가 NCF보다 방열 우수, 열 더미 범프를 TC-NCF 대비 최대 4배까지 늘림 | Rulebreaker Revolutions | 높음 | |
| 열(Samsung 계열 시뮬레이션) | 접합부 열저항은 MR-MUF가 가장 높고 TCB-NCF는 35% 낮으며 하이브리드 본딩이 가장 낮음 | Chip Scale Review Mar-Apr 2024 p.47(Samsung ECTC 2023 인용), https://chipscalereview.com/wp-content/uploads/flipbook/38/files/basic-html/page47.html | 낮음~중간 | 임의 단위(A.U.) 시뮬레이션. SK hynix 주장과 반대 |
| 종합(Hot Chips 2026 SK hynix 발표 보도) | TC+NCF는 생산성이 높고 열저항이 낮지만 칩 휨에 민감함. MR+MUF는 얇은 다이 휨에 강하지만 열저항이 더 높고 갭 충전 공정창이 좁음 | ServeTheHome(위 URL) | 중간 | 매체가 슬라이드를 요약한 것 |
| 휨 | TC-NCF는 칩이 얇아지고 적층이 조밀해지면서 한계 요인이 됨 | Rulebreaker Revolutions | 높음 | SK hynix 관점 |
| 휨(Samsung) | 얇은 다이의 휨을 TC-NCF가 완화하고 층수가 많을수록 이점이 크다고 주장 | Samsung 뉴스룸(위) | 높음 | Samsung 관점 |
| 하이브리드 본딩 | HCB 열저항이 TCB-NCF보다 15~30% 낮음, 8Hi에서 MR+MUF보다 22% 낮음 | Chip Scale Review p.48 | 중간 | 참고용 |

해석: 열 성능 비교는 회사마다 결론이 다르다. SK hynix 자료는 MR-MUF가 유리하다고 하고(EMC 소재 개선과 더미 범프 증가 효과 포함), Samsung 측 시뮬레이션은 같은 조건이면 NCF 쪽 접합 열저항이 낮다고 한다. 시뮬레이션에서는 이 두 주장을 모두 "출처별 주장"으로 보여 주고, 실제 열저항은 층간 간격, 범프 밀도, 충전재 열전도도로 계산하게 두는 편이 공정하다.

---

## 시뮬레이션 기본값 제안

| 그룹 | 파라미터 | 기본값 | 범위 | 구분 | 근거 |
|---|---|---|---|---|---|
| 형상 | 층간 간격 | 15 μm | 7~30 | 문헌값 | SK hynix MR-MUF 15 μm(ECTC 2023). 7 μm(Samsung 최소)와 약 30 μm(일반 범프 적층) 사이. 교육용 장비는 20 μm 옵션을 유지해도 됨 |
| 형상 | 범프 지름 | 25 μm | 15~50 | 문헌값 | Dow TV-II, IBM |
| 형상 | 범프 피치 | 55 μm | 40~80 | 문헌값 | Dow TV-II 55 μm, 업계 약 40 μm |
| 형상 | Cu 기둥 높이 | 9 μm | 5~25 | 가정 | 간격 15 μm에서 솔더 6 μm를 뺀 값. Dow TV-II 비율(기둥:솔더 = 25:5)보다 솔더 비중을 높임 |
| 형상 | 솔더 캡 높이(접합 후) | 6 μm | 3~15 | 가정 | Dow TV-II 5 μm, TV-I 15 μm |
| 형상 | 다이 두께 | 100 μm (옵션 50) | 30~100 | 문헌값 | 시험 칩 100 μm(Dow), 양산 30~60 μm |
| NCF | 필름 두께 | 간격+4 μm (=19 μm) | 간격+3 ~ +5 | 문헌값(비율) | Dow: 솔더 캡 위로 3~5 μm |
| NCF | 최저 용융 점도 | 1,727 Pa·s @138 ℃ | 1,000~30,000 | 문헌값 | Henkel, Dow |
| NCF | 점도-온도 | Arrhenius 감소 + 경화 증가 | 활성화에너지 50~80 kJ/mol | 가정 | 실측 곡선 미공개 |
| NCF | 경화 시작 / 피크 | 141 / 166 ℃ | 141~207 / 166~250 | 문헌값 | Dow DSC |
| NCF | 250 ℃에서 겔화 시간 | 3 s | 1~10 | 가정 | Dow 유지 시간 3.2 s, 160 ℃ 이상 빠른 경화 |
| NCF | CTE1 / CTE2 / E(25 ℃) / Tg | 40 ppm / 137 ppm / 6.7 GPa / 166 ℃ | CTE1 25~40, E 5.8~7.5 | 문헌값 | Henkel, Dow |
| NCF | 열전도도 | 0.4 W/m·K | 0.2~0.6 | 가정 | CUF 0.6, IBM 측정용 언더필 0.55 |
| MUF | 충전 온도 점도 | 2 Pa·s | 0.5~20 | 가정 | 25 ℃ CUF 13~22 Pa·s, 예열 시 크게 감소 |
| MUF | 표면장력 | 0.04 N/m | 0.03~0.05 | 문헌값(해석 입력) | Moldex3D |
| MUF | 접촉각 | 10° | 5~40 | 문헌값(해석 입력) | Moldex3D |
| MUF | 필러 함량 / 최대 크기 | 77% / 3 μm | 70~90 / 3~20 | 문헌값 | SK hynix ECTC 2023, Panasonic |
| MUF | CTE1 / E | 18 ppm / 11 GPa | 8~20 / 11~26 | 문헌값 | SK hynix, Panasonic |
| MUF | 열전도도 | 1.0 W/m·K | 0.6~4 | 가정 | 일반 EMC 0.9, 마케팅 4~8 |
| MUF | 경화 | 175 ℃, 2 h | 150~180 ℃, 1~4 h | 가정 | MR-MUF 경화 조건 미공개. EMC 겔화 측정 175 ℃, CUF 150 ℃ 2 h 참고 |
| 솔더 | 액상선 | 221 ℃ (SnAg) | 217~221 | 문헌값 | NIST, Kappalloy |
| 솔더 | 표면장력 | 0.49 N/m | 0.43~0.49 | 문헌값 | NIST(질소/공기) |
| 솔더 | 자기정렬 강성(범프당) | k = 2γd/h | 소변위에서만 | 문헌값(모델) | Mastrangeli. d=25 μm, h=6 μm(용융 솔더 높이)이면 범프당 약 4 N/m |
| 리플로 | 예열 / 소크 | 150→200 ℃, 90 s | 60~120 s | 문헌값 | Microchip |
| 리플로 | 피크 | 250 ℃ | 245~260 | 문헌값 | Microchip, 강의 240~260 |
| 리플로 | TAL | 90 s | 60~150 | 문헌값 | Microchip |
| 리플로 | 승온 / 냉각 | 2 / 4 ℃/s | ≤3 / ≤6 | 문헌값(상한) | Microchip |
| TC-NCF | 헤드 설정 / 다이 온도 | 300 / 250 ℃ | 250~300 | 문헌값 | Dow, 강의 |
| TC-NCF | 스테이지 | 100 ℃ | 80~150 | 문헌값 | Dow, K&S |
| TC-NCF | 힘 | 50 N (5×5 mm) | 25~100 | 문헌값 기반 | Henkel 25~75 N, Dow 90 N |
| TC-NCF | 승온 속도 | 80 ℃/s | 60~200 | 문헌값 | Henkel, K&S |
| TC-NCF | 층당 본딩 시간 | 10 s | 5~15 | 문헌값 | Dow <10 s, K&S 7~15 s |
| MR-MUF | 가접 온도 / 시간 / 힘 | 240 ℃ / 1 s / 2 N | 220~260 ℃ / 0.5~3 s / 0.5~10 N | 가정 | 방식만 공개, 조건 미공개 |
| MR-MUF | 웨이퍼 매스 리플로 | 위 리플로 기본값 | - | 문헌값 | 일반 무연 프로파일 차용 |
| MR-MUF | 휨 허용 | ±20 μm | ±20~30 | 문헌값 | SK hynix ECTC 2023 |
| 사이클 | 리플로 1회 총 시간 | 6 min | 4~8 | 문헌값(상한 8 min) | Microchip |
| 열 | μbump층 유효 k | 2.0 W/m·K | 1~3 | 문헌값 기반 계산 | IBM 측정 8 ℃·mm²/W |

검산 예시(모델 감각 확인용, 문헌값 아님)
- Washburn 평행판: μ=2 Pa·s, L=5 mm, h=15 μm, γ=0.04 N/m, θ=10°이면 t = 3·2·(5e-3)²/(15e-6·0.04·0.985) ≈ 254 s. 점도 20 Pa·s(상온 CUF)이면 약 42분이므로 예열이 필요하다는 결론과 맞는다.
- Stefan 스퀴즈(원판 등가 반경 R=2.82 mm): μ=1,727 Pa·s, F=50 N, 간격 23→19 μm이면 t = 3πμR⁴/(4F)·(1/h₁²−1/h₀²) ≈ 4.5 s. 범프 저항을 무시한 값이며, Dow의 승온+유지 시간(2.5+3.2 s)과 비슷한 크기다. 실제로는 승온 중 점도가 최저점보다 높으므로 더 길어질 수 있다.

## 미확인 항목
1. 세대별(HBM2E/3/3E/4) 공식 μbump 지름, 피치, Cu 기둥과 솔더 캡 높이. 공개 자료는 시험 칩 값이 대부분이다.
2. 양산 HBM용 NCF의 두께, 점도-온도 곡선, 경화 반응속도 상수(Kamal/Castro-Macosko 계수).
3. 양산 TC-NCF의 층당 본딩 힘, 시간, 헤드·스테이지 온도(Samsung 미공개).
4. MR-MUF 가접(칩 제어) 펄스의 온도, 시간, 힘. 매스 리플로 프로파일과 MUF 몰딩 온도, 압력, 경화 조건(SK hynix 미공개).
5. MUF의 충전 온도 점도, 표면장력, 접촉각.
6. NCF와 MUF의 밀도, 비열, 열전도도(양산 재료).
7. Sn-3.5Ag 영률 수치(NIST는 그래프만 제공).
8. 양산 처리량(UPH), 웨이퍼당 MR 배치 시간.

## 주의: 공개되지 않은 정보
- Samsung과 SK hynix는 공정 이름, 흐름, 일부 결과(간격 7 μm, 접합온도 14 ℃ 감소, 방열 1.6배 등)만 공개한다. 온도, 힘, 시간, 재료 배합 같은 공정 조건은 영업비밀이다.
- 이 문서의 공정 조건 수치는 시험 칩 논문(Dow/Fraunhofer, Henkel, K&S, IBM)과 일반 무연 리플로 프로파일에서 가져왔다. 실제 HBM 양산 조건과 다를 수 있다.
- 열 성능 비교는 출처 회사에 따라 반대 결론이 나온다. 보고서와 화면에서는 반드시 "누구의 주장인지"를 함께 표시한다.
- TechInsights 등 역설계 보고서에는 정확한 치수가 있지만 유료라서 이번 조사에 쓰지 않았다.
