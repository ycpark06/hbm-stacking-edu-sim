# 교육용 HBM 적층 본더 — TC-NCF / MR-MUF 비교 시뮬레이터

> UNIST MSE489 첨단패키징기술 PBL 과제
> 중간 과제의 교육용 다이본더를 다단 적층 본더로 고도화한 디지털 트윈

**데모 사이트:** _(GitHub Pages 주소 — 단계 4에서 기입)_
**시뮬레이션 영상:** _(단계 7에서 기입)_

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

_(그림 — 단계 4에서 추가)_

```
[웹 HMI / 3D 뷰]  ←→  [시뮬레이션 엔진 (JS)]  ←→  [펌웨어 (wasm)]
   레시피·모드 선택        플랜트 물리 모델           하중 PI 1 ms
   실시간 그래프           (열·휨·NCF·MUF)           온도 PI 10 ms
   비전 정렬 화면                                    인터락
                                                       │
                                     같은 C 코드 → MCU 빌드 (controller.bin)
```

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
_(단계 4에서 작성 — 피듀셜 생성, NCC 검출, 서브픽셀 보간, 아핀 보정, 폐루프 정렬)_

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
TC 아래층은 N−1회 후속 접합 가열을 받고, 기본 조건에서는 첫 접합만 액상선을 넘는다.
MR은 전체 리플로우1회, 후속 tack 노출은 별도 기록한다. 업체 주장은 회사·출처와 함께 표시만 한다.

중간 모델 golden은 `ch7_16node`(MACOR16절점)와 `ch10_3node` 프리셋을 각각 재현한다.
7장 원본은 Kp=1e6/Ki=0(on/off 근사)이며 “PI 유지” 설명 수정은 #4·단계6이다.
10장 제어 golden은 `controller.wasm` REFERENCE + JS 플랜트로 대조한다.
새 적층 사슬은 C1의 별도 후진 오일러 모델이며 헤드 프리셋과 구분한다.

원문 KPI(±1 μm·400 ℃·50 N·≤600 mm)와 원문 요구10 ms는 장비 요구이고,
층간3σ·휨·결함 기준은 **설계 목표**,15 μm 등은 **문헌값**,40 N은 **설계값**이다.
접촉 열저항·MUF 충전 점도/압력·감쇠/마찰·경화 시간은 **가정값**으로 params 한곳에 근거를 둔다.
원본 재현 상수는 원본 출처 주석과 함께 보존한다. 결과에 맞춘 파라미터 조정은 하지 않았다.

[단계3 전체 표·대표 시나리오·민감도·신규 params](docs/stage3_report.md),
[16개 시나리오 및 민감도 JSON](sim/test/scenario_results.json),
[C1 열·휨·#2](docs/thermal_history_report.md), [C2 NCF·#20](docs/tcncf_mode_report.md),
[golden과 #3·#4·#5·#7](docs/sim_port_report.md)에 재현 조건과 한계가 있다.
기본 gap15 μm MR도 미충전80.153%로 불량이므로 “좁힐 때만 불량” 시연을 뒷받침하지 않는다.

### 3.4 알람과 인터락
_(단계 4에서 작성)_

---

## 4. 저장소 구조

```
├─ docs/        계획서, 요구사항, 보고서, 실습 매뉴얼, 발표 자료
├─ calc/        Python 계산 모델
├─ firmware/    제어 C 코드, HAL, 빌드 결과 (.bin, .wasm)
├─ sim/         시뮬레이션 엔진 (JS), params.json, 테스트
├─ web/         웹 시뮬레이터 (GitHub Pages)
├─ cad/         Fusion 스크립트, STEP, GLB, 2D 도면
├─ wiring/      배선도
└─ media/       영상, 캡처
```

---

## 5. 실행 방법

### 시뮬레이션 모델 검증

```bash
node --test sim/test          # golden111 유지 + 물리 모델 + 16개 시나리오/민감도, 전체139개
(cd sim && npm test)          # 동일한 Node 내장 테스트
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
# 단계 4에서 작성
```

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
| 2026-11-26 | #3 | 7·10장 열 모델 차이 | 절점·손실 면적·열용량이 다름 | 하나의 플랜트에 16/3절점 프리셋, 두 golden 재현 ([기록](docs/sim_port_report.md)) |
| 2026-11-26 | #5 | contact_transient_N 수기 입력 | control_sim 출력에 해당 키 없음 | 원본 contact_speed_study 재사용 스크립트, 6항목 차이 0 N |
| 2026-11-26 | #7 | 원본 실행 폴더가 다름 | 상대 출력 경로 혼재 | 임시 작업 폴더 래퍼 추가, h=10 FEM 원본 오류 보존 ([기록](docs/sim_port_report.md)) |
| 2026-11-26 | #20 | NCF 초기 두께·MR 사이클 비교 왜곡 | 지시문의 곱셈 오류·배치 후공정 직렬 합산 | h0=15+4=19 μm 복구, 본더 점유/배치 후공정 분리 및 [C2 결과 재계산](docs/tcncf_mode_report.md) |
| 2026-11-26 | #2 | 헤드 열팽창 2.6 μm/s 출처 없음 | 하중 모델에 상수만 존재 | ch7_16node·CAD z 높이로 정렬 시점 약 0.03935 μm/s 계산. 상부 고정 온도·유효 길이 가정을 [기록](docs/thermal_history_report.md)에 명시, Issue 반영은 리뷰 후 처리 |
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
