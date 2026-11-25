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
| 설계 목표 | 층별 휨 한도 | 층간 간격의 1/4 이하 (가정 간격 20 μm 기준 5 μm) |
| 설계 목표 | 결함 면적률 (보이드 + 미충전 합산) | ≤ 1 % 양호 / 1~5 % 주의 / > 5 % 불량 |

시편 조건·관찰 항목(사이클 시간 등)·근거는 [`docs/requirements.md`](docs/requirements.md)에 있다.

공정 조건(온도, 하중, 시간, 재료 물성)은 강의 자료와 문헌을 바탕으로 한 **가정값**이다. 전체 목록은 [`sim/params.json`](sim/params.json)에 있다.

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
| 모델 | 비교 포인트 |
|---|---|
| 층별 열 이력 | TC-NCF는 아래층이 N회 재가열, MR-MUF는 리플로우 1회 |
| 정렬 + 자기정렬 | TC-NCF는 정렬 오차가 남음, MR-MUF는 리플로우 때 일부 보정 |
| 휨 누적 | 층 수와 다이 두께에 따른 누적 |
| NCF 스퀴즈 유동 | 필름이 밀려 나오는 양, 갇힌 보이드 |
| MUF 모세관 충전 | 충전 시간, 미충전 |
| 사이클 시간 | 처리량 |

_(단계 3에서 수식과 가정을 작성)_

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
