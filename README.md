# 교육용 HBM 적층 본더 — TC-NCF / MR-MUF 비교 시뮬레이터

> UNIST MSE489 첨단패키징기술 PBL 과제
> 중간 과제의 교육용 다이본더를 다단 적층 본더로 고도화한 디지털 트윈

**데모 사이트:** https://ycpark06.github.io/hbm-stacking-edu-sim/
**시뮬레이션 영상:** _(단계 7에서 기입)_

**기말 보고서:** [원고·그림·PDF 빌드](docs/report/final/)
**실습 매뉴얼:** [적층 공정 비교 실습](docs/manual/실습매뉴얼.md)

---

## 1. 장비 개요

### 기능
- 한 장비에서 HBM 적층 공정 두 가지를 선택해 실행한다.
  - **TC-NCF 모드:** 층마다 비전도성 필름(NCF)을 사이에 두고 열과 하중으로 바로 접합한다.
  - **MR-MUF 모드:** 층마다 순간 가열로 임시 고정하고, 전체를 한 번에 리플로우한 뒤 칩 사이에 수지를 채운다.
- 듀얼 비전으로 층마다 정렬하고, 하중·온도를 실시간 제어한다.
- 과하중, 과온, 정렬 오차, 휨 한도, 미충전에 대해 알람과 인터락이 동작한다.

### 목적
학생이 두 공정의 **원리 차이**(열 이력, 정렬 보정, 휨 누적, 보이드가 생기는 원리, 처리량)를 같은 장비에서 직접 비교하며 익히는 교육 장비다. 어느 공정이 우수한지 판정하는 장비가 아니다.

### 주요 사양
| 구분 | 항목 | 값 |
|---|---|---|
| 원문 KPI | 정합 반복정밀도 | ±1 μm |
| 원문 KPI | 펄스 히터 최고 온도 | 400 ℃ |
| 원문 KPI | 최대 본딩 하중 | 50 N |
| 원문 KPI | 풋프린트 (가로·세로) | ≤ 600 mm |
| 원문 요구 | 피드백 주기 | 10 ms |
| 설계 목표 | 층간 정렬 오차 | 층마다 아래층 대비 3σ ≤ 1 μm |
| 문헌값 | 층간 간격 | 기본 15 μm, 선택 7~30 μm, 20 μm는 "시험 칩" 선택지 |
| 설계 목표 | 층별 휨 한도 (주의) | 절대 휨이 층간 간격의 1/4 초과 (15 μm 기준 3.75 μm), 조기 경고 |
| 설계 목표 (근거: 문헌값, SK hynix ECTC 2023) | 층별 휨 한도 (불량) | ±20 μm 초과 (절대 휨 > 20 μm), SK hynix MR 접합 안정 범위 (220 ℃ 측정, ECTC 2023) |
| 설계 목표 | 결함 면적률 (보이드 + 미충전 합산) | ≤ 1 % 양호 / 1~5 % 주의 / > 5 % 불량 |

시편 조건·관찰 항목(사이클 시간 등)·근거는 [`docs/requirements.md`](docs/requirements.md)에 있다.

TC-NCF 기본 하중은 **40 N** (선택 25~50 N, 사용자 확정 설계값; Henkel 문헌 25~75 N)이다. 승온 속도는 **20 K/s** (중간 보고서 7장 히터 최대 22 K/s에 근거한 장비 설정)를 사용하며, 문헌 **80 ℃/s**는 비교값이다. 교육 장비의 한계로 구분한다.

공정 조건(온도, 하중, 시간, 재료 물성)은 문헌값·설계값·중간 보고서값·가정값으로 구분하고, 가정값에는 근거 문장을 붙인다. 전체 목록은 [`sim/params.json`](sim/params.json), 출처는 [파라미터 조사 자료](docs/research/params_research.md)에 있다.

업체 주장은 **관찰 항목(표시만)**으로 구분하고, 판정·계산 입력에 쓰지 않으며 회사·출처와 함께 표시한다: SK hynix는 MR-MUF 접합 온도가 TC-NCF보다 **14 ℃ 낮음**을 주장한다 (Lee et al., ECTC 2023). Samsung 인용 시뮬레이션은 TC-NCF 접합부 열저항이 MR-MUF보다 **35 % 낮음**을 주장한다 (Chip Scale Review 2024 p.47, A.U.). [조사 자료 7절](docs/research/params_research.md#7-tc-ncf-vs-mr-muf-공개-비교)에 회사와 출처가 있다.

---

## 2. 시스템 아키텍처

```text
firmware/src/*.c (공통 제어기 C)
   ├── MCU HAL → controller.bin → STM32H743
   └── wasm HAL → controller.js + controller.wasm
                         ↕
 sim/plant.js (JS 플랜트, 독립 SIL)    sim/stack.js (열·휨·충전·정렬)
                         └──────────┬───────────────┘
                           Web Worker (web/js/worker.js)
                                    ↕ 계산 결과·진행 이벤트
                           HMI · Canvas 그래프 · three.js 3D
                                    │
 GitHub Actions: web/ + sim/ + firmware/build/ (+ 선택 CAD GLB)
                                    ↓
                          _site/ → GitHub Pages
```

HMI는 ES module Worker에서 모델을 계산하고, 계산 후 실제 층·단계 이력을 재생한다.
하중 그래프는 `sim/plant.js` + wasm REFERENCE 제어기의 독립 SIL이다.
적층 열 모델의 이상 경계 조건과 직접 연결된 폐루프라고 해석하지 않는다.
고장 주입은 별도의 wasm FIRMWARE 인스턴스를 사용한다.

---

## 3. 제어 로직 및 알고리즘

### 3.1 펌웨어
`firmware/src/`의 공통 C99 float 제어기(하중 PI 1 ms·온도 PI 10 ms·시퀀서·인터락)를
`hal/`의 PC·STM32H743·wasm HAL과 연결한다. 동적 할당은 없다.
`FW_MODE_REFERENCE`는 원본 golden 대조용이며 제한·anti-windup이 없다.
기본 `FW_MODE_FIRMWARE`는 하중 속도 ±0.5 mm/s와 `I_max=v_max/Ki`를 적용하고
포화 시 이번 적분을 되돌린다(설계값, 10장 최대 접근 속도 기준).
인터락은 실물 비교기·래치에 의한 독립 하드웨어 차단의 모사다. 경고는 Z를 정지하고,
고장 래치는 히터·Z를 정지하며 수동 리셋 전까지 유지한다.
[빌드·검증 및 wasm API](firmware/README.md), [#6·#13 결정 기록](firmware/docs/force_integral_limit.md)을 참고한다.

### 3.2 비전 정렬
`sim/vision.js`는 합성 피듀셜, NCC 검출, 가우시안 서브픽셀 보간,
평탄화 보정, 아핀 좌표 변환 및 재측정 폐루프를 제공한다.
`web/vision.html`에서 층별 상·하 영상, 검출 십자선, Δx·Δy·Δθ와 보정 반복을 확인한다.
HMI의 현재 층 링크가 비전 페이지의 층 선택에 연결된다.
원본 golden 비전 오차 허용치는 절대 **2e-4 px**, 중간 보고서 폐루프 결과는
**3σ 0.09 μm**이다(중간 보고서 결과이며 실물 KPI 달성 보증이 아님).
비전 상수 24개는 `params.alignment`에 원본 value·unit·kind·source로 보존했다
(21개 midterm, θ 분해능·조명 기울기 3개 assumption).
`visionOptions`는 params → 원본 기본값 순으로 읽고 호출자 override를 마지막에 적용한다.

### 3.3 시뮬레이션 모델

`runStack(mode, recipe, params)`가 열 이력·휨·충전·정렬·판정·사이클을 묶는다.
모드는 `TC-NCF`/`MR-MUF`, recipe는 `layers`, `thickness_um`, `gap_um`,
`bond_force_N`, `seed`, `alignment_reference`를 선택한다. 기본은 params의
8단·100 μm·15 μm·40 N·시드489·직전 층 기준이다. 20 μm는 시험 칩 옵션이다.
전체 이력과 층별 결과를 반환하며 브라우저에서도 같은 ES 모듈을 import한다.

| 모듈 | 수식·결합 | 가정·한계 |
|---|---|---|
| `thermal.js` | N층 Si 중심 열 사슬, `C ΔT/Δt = Q_in−Q_out` 후진 오일러; TC 층별 접합, MR tack 후 전체 리플로우 | 접합층 독립 온도·잠열·경화 발열 없음. 스택 헤드 경계는 이상 추종이며 400 W 제한/wasm 폐루프 직접 결합은 미구현 |
| `warpage.js` | 적층판 A/B/D 열합력·모멘트, `w=κL²/8`; 2층은 Timoshenko와 일치 | 층별 접합/리플로우/경화 무응력 온도. 상온 물성 고정, 기판 구속·점탄성·경화 수축 없음. 전체 공정의 최대 절대 휨 판정 |
| `ncf.js` | `μ=μref exp[(Eμ/R)(1/T−1/Tref)] [αg/(αg−α)]^(A+Bα)`, `dα/dt=k(T)(1−α)`; Stefan `1/h²=1/h₀²+4Ft/(3πμR⁴)`를 RK4 적분 | 초기 `h₀=gap+4 μm`(기본19 μm). 접촉 전 겔·저점도 체류의 **정성 경향**만 제공. 결함 면적률 `null`, 판정 “정량 모델 없음 (경향: …)” |
| `muf.js` | `t=6μL²/[h²(ΔPapp+2γcosθ/h)]`; 압력0이면 Washburn `3μL²/(γhcosθ)`. 병렬 층 완료 `max_i`; 미충전 `max(0,1−sqrt(t_allow/t_fill))`의 면적 가중 평균 | 다이 한 변 전체 공급·직선 선단, 흐름 길이는 한 변. 범프 밀도/투과도 보정 없음. 점도는 기존 충전 가정값 상수. 필러 막힘·정량 보이드·경화 유동 결합 없음 |
| `alignment.js` / `rng.js` | C2 시드 xoshiro128**+Box–Muller 배치 오차. MR `K=N_b·2γd/h`, `m x″+c x′+Kx=−F sign(x′)` 2차 감쇠 응답을 층별 TAL 동안 적용 | 작은 변위, 원형 지름을 패드 폭으로 대입, 독립 층간 좌표·다이 질량·정지 마찰. MR 잔여 3σ는 기존20000표본 MC 표준편차 지표이며 비정규 분포의99.7% 보장 아님 |
| `cycle.js` | 삼각/사다리꼴 이동, 층별 픽업·정렬·접합 합산 | **본더 점유 / 배치 후공정 / 직렬 합계 분리**. 배치 크기 가정 없이 라인 UPH를 만들지 않음 |
| `stack.js` | 휨: gap/4 초과 주의,20 μm 초과 불량; 결함: ≤1% 양호,>1~5% 주의,>5% 불량; 층간 축별3σ≤1 μm | MR 결함률은 미충전만 포함하며 정량 보이드 없음. MR 접촉은 젖음·접촉 가정으로 정량 판정 없음. 누적 오차와 업체 주장은 관찰값 |

**재가열은 후속 접합 가열 이벤트 수**이며 **재용융은 액상선221 ℃ 교차**와 구분한다.
TC 아래층은 N−1회 후속 접합 가열을 받지만, 액상선 교차·후속 재용융 횟수는 층별 이력으로 구분한다.
현재 기본 TC-NCF의 1·2층은 자기 접합 때 액상선에 미달한다. 후속 재가열을 자기 접합 온도 충족으로 간주하지 않는다.
MR은 전체 리플로우1회, 후속 tack 노출은 별도 기록한다. 업체 주장은 회사·출처와 함께 표시만 한다.

중간 모델 golden은 `ch7_16node`(MACOR16절점)와 `ch10_3node` 프리셋을 각각 재현한다.
7장 원본은 Kp=1e6/Ki=0(on/off 근사)이며 “PI 유지” 설명 수정은 #4·단계6이다.
10장 제어 golden은 `controller.wasm` REFERENCE + JS 플랜트로 대조한다.
새 적층 사슬은 C1의 별도 후진 오일러 모델이며 헤드 프리셋과 구분한다.

원문 KPI(±1 μm·400 ℃·50 N·≤600 mm)와 원문 요구10 ms는 장비 요구이고,
층간3σ·휨·결함 기준은 **설계 목표**,15 μm 등은 **문헌값**,40 N은 **설계값**이다.
접촉 열저항은 **역산 추정값**, MUF 충전 점도/입구 압력·감쇠/마찰은 **가정값**, 후경화 시간은 **문헌값**으로 params 한곳에 근거를 둔다.
원본 재현 상수는 원본 출처 주석과 함께 보존한다. 결과에 맞춘 파라미터 조정은 하지 않았다.

[단계3 전체 표·대표 시나리오·민감도·신규 params](docs/stage3_report.md),
[16개 시나리오 및 민감도 JSON](sim/test/scenario_results.json),
[C1 열·휨·#2](docs/thermal_history_report.md), [C2 NCF·#20](docs/tcncf_mode_report.md),
[golden과 #3·#4·#5·#7](docs/sim_port_report.md)에 재현 조건과 한계가 있다.
단계 4에서는 가압 충전 `t=6μL²/[h²(ΔP입구+ΔP모세관)]`으로 보정했다.
기본 입구 유효 압력 1 MPa(가정값, 범위 0.1~3 MPa)에서 간격 15 μm의 충전 시간은
약 3.32 s, 미충전률은 0 %다(계산 결과). 압력 0은 모세관 단독 비교로 남긴다.
접촉 열저항 툴–다이·다이–척 각각 2e-4 m²K/W는 직접 측정값이 아닌 **역산 추정값**이다.
이 입력에서 TC-NCF 12단의 자기 접합 최고온도는 1층 약 208.54 ℃, 2층 약 215.85 ℃로
액상선 221 ℃(문헌값)에 못 미쳐 `BOND_TEMP_LOW`를 표시한다.
`head_temp_compensation` 옵션은 층별 목표 = 액상선 + 10 ℃(설계값)를 만족하도록
헤드 온도를 계산한다. 필요 온도가 400 ℃(원문 KPI)를 넘으면 `HEAD_TEMP_LIMIT`로
거부하고 층·필요 온도를 표시한다. 기본 레시피와 모델 파라미터는 유지한다.
[S1~S5 및 보정 결과·웹 호출 계약](docs/stage4_model_update.md)을 참고한다.

### 모델 한계

휨 판정은 두 모드에 **같은 기준**(주의=간격/4, 불량=절대 휨 20 μm 초과,
설계 목표)을 사용한다. 업체의 “TC-NCF가 휨에 민감 / MR-MUF가 박형에 유리”라는
주장과 달리 이 모델의 S3에서는 50 μm에서 두 모드 모두 불량이다.
1D 선형 탄성·상온 물성의 한계이며 기판 구속·점탄성·경화 수축을 포함하지 않는다.
결과를 맞추려 파라미터나 모드별 기준을 조정하지 않았다.
NCF 보이드 정량 모델은 없고, MUF 미충전 모델에는 범프 투과도·필러 여과·갇힌 공기가
포함되지 않는다. 필러 막힘 규칙과 겔 경고는 별도로 표시한다.
[가정값 전체 목록](sim/params.json)은 HMI 파라미터 표에서 `assumption`으로 검색할 수 있다.
[가정값 민감도와 한계](docs/stage4_model_update.md#민감도-판정을-바꾸는-가정-순서)도 참고한다.

### 3.4 알람과 인터락
경고 **52 N / 410 ℃**, 래치 **55 N / 420 ℃**는 중간 보고서 10장 안전 계층의
**설계값**이다. 원문 KPI 최대 50 N / 400 ℃와 구분한다.
`fw_get_warning`·`fw_get_latched`를 표시하고 과하중·과온·하드웨어 고장을 주입한다.
고장 원인 해제만으로 래치는 풀리지 않으며 `fw_reset_latch` 수동 리셋이 필요하다.
조건이 남아 있으면 즉시 재래치한다. 래치 시 히터·Z가 차단된다.

두 히터 동시 통전은 금지한다. 헤드 통전 중 리플로우 척 히터를 요청하면
`fw_get_dual_heater_blocked`가 차단을 보고하고 척 출력은 0 W가 된다.
이 플래그는 비래치 경고이며 양방향 전환에는 펌웨어가 정한 대기 주기가 있다.
자세한 [wasm 히터 인터락 계약](firmware/README.md)을 따른다.
모델 알람은 접합 온도 미달 `BOND_TEMP_LOW`, 휨·결함 판정, 필러·겔 경고를
펌웨어 보호 상태와 함께 표시한다.

### 3.5 하드웨어(적층 부품)

[Fusion 요약](cad/stacker/out/summary.json)의 외곽은 **590 × 480 mm**로 가로·세로 ≤ 600 mm **원문 KPI를 통과**하며, 간섭은 **0**이다. 높이 **630 mm**와 질량 **101.88 kg**은 판정 대상이 아닌 **참고값**이다.

헤드 **400 W**와 리플로우 척 **150 W**는 **설계값**이며 **순차 사용**한다. **두 히터 동시 통전 금지**는 [펌웨어 SW 인터락](firmware/README.md#두-히터-동시-통전-금지-w7-2026-11-28)(PR #30)으로 구현·시험했다. 보조 전력을 포함한 척 단계 **250 W** / 헤드 단계 **500 W**는 중간 전원 **48 V 600 W** 이내다. 척 히터는 **3 K/s** 승온에 필요한 **120.7 W** 대비 여유가 있다. 리플로우 척 **250 ℃·승온 1~3 K/s**는 문헌 프로파일에 근거한 **공정 목표**이며 헤드 **400 ℃ 원문 KPI**와 구분한다.

공기·N₂ 강제 냉각의 **설계 목표**는 **피크→180 ℃에서 4 K/s 이상 유지**다. 현재 계산은 최소 **3.39 / 평균 4.10 K/s**로 **FAIL/REVIEW**이며, **180 ℃ 아래는 관찰 항목(판정 없음)**이다. 풍량 **100 L/min**과 대류 열전달계수 **h = 400 W/m²K**는 실측 전 **가정값**이다. 평균 속도가 목표를 넘어도 전 구간 유지 조건을 통과하지 못한다.

가압 지그는 **Ø4 mm 플런저**(설계값)에 마찰 가정을 포함한 **42.7 N**에서 금형 압력 **3 MPa**(문헌값)에 도달하는 계산이다. 독립 **M3 나사 4개 합계 예압 ≥ 216 N**은 설계값이며, **기밀·내압은 제작 후 시험**한다. 범프 접촉 응력 손계산은 **40 / 50 N**에서 **9.9 / 12.3 MPa**, 비교 문헌 Si 굽힘 파괴강도는 **261 MPa**(**51 μm 시험편**)다. 전면 석영 지지·균일 범프 하중을 전제로 **조건부 PASS**이며 실제 다이의 최소강도나 수명 보증은 아니다.

층간 정렬은 적층 중 상온 또는 고정 정렬 온도에서 완료한다. 리플로우 시 기준점 **108.6 μm** 이동은 완성 스택이 척과 함께 강체 이동한다는 해석에서 **층간 정합 ±1 μm 원문 KPI에 영향 없음**이다. **적층 척 = 리플로우 척**이면 정렬 온도를 고정하고 **온도 도달 후 90 s 안정화**한 뒤 정렬한다(중간 보고서 7장). 열 휨·미끄러짐은 제작 후 별도 확인한다.

숫자·판정·문헌 출처는 [하드웨어 계산 4종](calc/hardware/README.md)에 있다. 산출물: 제작 도면 3장([적층 척](docs/drawings/stack_chuck.pdf), [리플로우 척](docs/drawings/reflow_chuck.pdf), [가압 지그](docs/drawings/mold_jig.pdf)), [배선도](wiring/hbm_wiring.svg)·[핀 배정표](wiring/pinmap.csv), [장비 GLB](cad/web/hbm_stacker.glb), [Fusion 실행 방법](cad/stacker/README.md#실행-방법).

---

## 4. 저장소 구조

```
├─ docs/        계획서, 요구사항, 보고서, 실습 매뉴얼, 발표 자료
│  └─ drawings/ 적층 척·리플로우 척·가압 지그 제작 도면
├─ calc/        Python 계산 모델
│  └─ hardware/ 신규 하드웨어 계산 4종·결과 JSON
├─ firmware/    제어 C 코드, HAL, 빌드 결과 (.bin, .wasm)
├─ sim/         시뮬레이션 엔진 (JS), params.json, 테스트
├─ web/         웹 시뮬레이터 (GitHub Pages)
├─ cad/         Fusion 스크립트, STEP, GLB
│  ├─ stacker/  적층 장비 Fusion 스크립트·STEP·요약
│  └─ web/      웹용 장비 GLB
├─ wiring/      배선도·STM32H743 핀 배정표
└─ media/       영상, 캡처
```

---

## 5. 실행 방법

### 시뮬레이션 모델 검증

```bash
node --test 'sim/test/*.test.js' # golden111 + 비전·모델·HMI 검증 (Node 24 호환 glob)
# sim/package.json의 폴더 인자 npm test는 Node 버전에 따라 실패할 수 있으므로 위 glob 사용
python3 -I calc/reference/check_golden.py
python3 calc/contact_transient.py  # JSON은 stdout, 항목별 차이는 stderr
python3 calc/run_midterm.py       # 임시 복사본 실행 결과 표, 원본은 수정하지 않음
```

Python 원본에는 numpy·matplotlib·scipy·opencv-python이 필요하며, 없는 의존성은 래퍼가 표시한다.
3-B에서는 Python 3.12로 참조를 검증했다. 3-C3의 기본 `python3` 재실행은 numpy 부재로
`check_golden.py`와 `run_midterm.py`가 exit1이었다. 의존성 오류와 미완료 범위는 전체 보고에 기록했다.
Node 테스트는 직렬화 전 NaN/Infinity·음수 두께/시간을 검사하고 `scenario_results.json`을 다시 쓴다.
시나리오 판정은 테스트 기대값으로 고정하지 않는다.
SIL 모듈의 상대 ESM import는 브라우저에서도 같고, Node의 wasm 파일 읽기는 테스트에서만 한다.

### 웹 시뮬레이터
```bash
web/serve_local.sh             # 저장소 구조를 _site/에 조립하고 서버 실행
# http://localhost:8000/web/
web/tools/headless_check.sh     # Chrome headless wasm 로드·1,000 tick, Node와 비교
node web/tools/wasm_check_node.mjs # 브라우저 없이 wasm 점검
node web/tools/check_hmi.mjs    # JS 문법·정적 import/자산·vendor 해시 검사
node web/tools/check_worker.mjs # S1~S5 Worker 메시지·전체 이력·wasm SIL 확인 (DOM/3D 검증 제외)
```

HMI에서 레시피 실행 또는 S1~S5를 선택한다. S1은 기본/헤드 보정/MR-MUF를 비교하며
층별 접합 온도·재가열·재용융을 펼쳐 볼 수 있다. S3은 휨 증가 배율과 모델 한계를,
S5는 간격 × 입구 압력 표와 필러·겔 경고를 표시한다.
고장 주입 → 고장 원인 해제 → 수동 래치 리셋 순서로 보호 동작을 확인한다.
3D는 절차적 모델을 쓰며, `cad/web/hbm_stacker.glb`가 병합되면 조립 스크립트가
복사하고 뷰어가 같은 노드 이름으로 헤드·척 위치를 연결한다.
three.js 0.160.0은 로컬 vendor이며 [원본 URL·SHA256·라이선스](web/vendor/README.md)를 보존한다.

### 펌웨어 빌드

도구: make, C99 cc, Python 3, arm-none-eabi-gcc/objcopy/size, Emscripten emcc, Node.
MCU는 NUCLEO-H743ZI2 기준 STM32H743이며 ADC·PWM·서보 실물 bring-up은 미구현이다.
`firmware/build/controller.bin`, `controller.js`, `controller.wasm`은 일반 Git 산출물이다.

```bash
make -C firmware test       # PC 검증 1~4
make -C firmware mcu        # STM32H743 .elf → .bin 및 size
make -C firmware wasm       # ES module controller.js + controller.wasm
make -C firmware test-wasm  # 검증 6, Node ↔ PC 고정 입력 비교 (별도 실행)
```

---

## 6. 트러블슈팅 로그

해결한 Issue를 한 줄씩 기록한다. 자세한 분석은 각 Issue에 있다.

| 날짜 | Issue | 문제 | 원인 | 해결 |
|---|---|---|---|---|
| 2026-11-28 | [#4](https://github.com/ycpark06/hbm-stacking-edu-sim/issues/4) | 중간 7장 "PI로 유지" 설명과 결과 계산 조건 불일치 | 결과는 Kp 1e6·Ki 0(사실상 on/off)으로 계산 | 기말 보고서 7장 7.2.1절에 두 조건 결과를 구분해 기록, 원본 golden 보존 ([PR #41](https://github.com/ycpark06/hbm-stacking-edu-sim/pull/41)) |
| 2026-11-28 | [#37](https://github.com/ycpark06/hbm-stacking-edu-sim/issues/37) | CI Node 24에서 시나리오 기준값 정확 일치 테스트 실패 | Box–Muller `Math.log/cos/sin` 마지막 ulp가 V8 버전마다 다름 | 숫자 상대 1e-12 허용 비교 ([PR #38](https://github.com/ycpark06/hbm-stacking-edu-sim/pull/38)) |
| 2026-11-28 | [#33](https://github.com/ycpark06/hbm-stacking-edu-sim/issues/33) | Fusion 내장 Python 기본 인코딩 ASCII에서 `read_text`/`open` 실패 | 인코딩 미지정 | cad 스크립트 입출력 UTF-8 명시 + ASCII 환경 검사 `cad/tools/check_encoding.py` ([PR #34](https://github.com/ycpark06/hbm-stacking-edu-sim/pull/34)) |
| 2026-11-28 | [#23](https://github.com/ycpark06/hbm-stacking-edu-sim/issues/23) | worktree index.lock 생성 실패 | Codex 샌드박스의 git 메타데이터 보호 | Codex는 코드 작성, Claude가 커밋 |
| 2026-11-28 | [#25](https://github.com/ycpark06/hbm-stacking-edu-sim/issues/25) | Node 24에서 node --test 폴더 인자 실패 | 폴더를 모듈 경로로 해석 | `node --test 'sim/test/*.test.js'` glob 사용 |
| 2026-11-28 | [#29](https://github.com/ycpark06/hbm-stacking-edu-sim/issues/29) | TC-NCF 1·2층 접합 온도 미달 | 역산 접촉 열저항 입력으로 다이 온도 하강 | 파라미터 유지, 알람·헤드 보정 옵션·KPI 초과 거부 |
| 2026-11-26 | #3 | 7·10장 열 모델 차이 | 절점·손실 면적·열용량이 다름 | 하나의 플랜트에 16/3절점 프리셋, 두 golden 재현 ([기록](docs/sim_port_report.md)) |
| 2026-11-26 | #5 | contact_transient_N 수기 입력 | control_sim 출력에 해당 키 없음 | 원본 contact_speed_study 재사용 스크립트, 6항목 차이 0 N |
| 2026-11-26 | #7 | 원본 실행 폴더가 다름 | 상대 출력 경로 혼재 | 임시 작업 폴더 래퍼 추가, h=10 FEM 원본 오류 보존 ([기록](docs/sim_port_report.md)) |
| 2026-11-26 | #20 | NCF 초기 두께·MR 사이클 비교 왜곡 | 지시문의 곱셈 오류·배치 후공정 직렬 합산 | h0=15+4=19 μm 복구, 본더 점유/배치 후공정 분리 및 [C2 결과 재계산](docs/tcncf_mode_report.md) |
| 2026-11-26 | #2 | 헤드 열팽창 2.6 μm/s 출처 없음 | 하중 모델에 상수만 존재 | ch7_16node·CAD z 높이로 정렬 시점 약 0.03935 μm/s 계산. 상부 고정 온도·유효 길이 가정을 [기록](docs/thermal_history_report.md)에 명시 |
| 2026-11-25 | #6 | 하중 적분 누적·초과량 | 출력·적분 한계와 anti-windup 없음 | FIRMWARE에 ±0.5 mm/s·I_max=v_max/Ki·포화 시 이번 적분 차감, 포화 3조건 검증 통과 |
| 2026-11-25 | #13 | 저레인지 원본 유지 구간 오차 초과 | 속도 제한으로 유지 구간 시작 전 목표 미도달 | 두 모드의 판정 시작=max(원본 시작, 98% 목표 도달+0.5 s), 원본 오차·도달 시각 관찰값 보존, 검증 2 통과 |
| 2026-11-25 | #8 | Codex 샌드박스에서 브랜치 생성 실패 | workspace-write가 `.git` 쓰기를 막음 | 브랜치는 Claude가 만들고 `.git`만 writable_roots에 추가 |
| 2026-11-25 | #9 | golden 재생성 시 끝자리 값이 달라짐 | Python 3.13.18 ↔ 3.13.9 부동소수점 끝자리 차이 (최대 상대 8.6e-15) | 바이트 비교 대신 `check_golden.py`로 벡터별 tolerance 비교 |
| 2026-11-25 | #15 | 저레인지 레시피 램프 5 N/s가 장비 능력 초과 | 하중 상승률 상한 ≈ k_eff·v_max ≈ 1 N/s (저레인지) | FIRMWARE에서 ramp > k_spring·v_max 레시피 거부, 저레인지 기본 1 N/s. 원본 유지 구간에서도 ss_err 4.4e-7 N로 통과 |

---

## 7. 중간 대비 개선 성과

기준: [`v1.0-midterm`](../../tree/v1.0-midterm) → [`v2.0-final`](../../tree/v2.0-final)

| 항목 | 중간 (`v1.0-midterm`) | 최종 (`v2.0-final`) |
|---|---|---|
| 지원 공정 | 에폭시 다이 부착, Cu pillar 열압착 (단일 다이) | _(기입)_ |
| 제어 구현 | 설계·계산 | _(기입)_ |
| 조작 화면 | 없음 | _(기입)_ |
| 알람·인터락 | 설계 | _(기입)_ |
| 시뮬레이션 | 정적 계산 | _(기입)_ |
| 산출물 | 보고서, CAD, 도면 3장 | _(기입)_ |

---

## 참고
- 강의: MSE489 첨단패키징기술 강의자료 (0917 공정, 1001 플립칩, 1008 2.5D·3D)
- SK하이닉스 뉴스룸, MR-MUF: https://news.skhynix.com/en/?p=1917
- 삼성전자 반도체, HBM3E (Advanced TC-NCF): https://semiconductor.samsung.com/dram/hbm/hbm3e/
