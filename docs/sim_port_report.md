# 단계 3-B 검증 및 Issue 기록

작성: Codex, 검증: Claude 예정. 브랜치 `feat/sim-port`. 원문 KPI·확정 파라미터를 변경하지 않았다.
아래 시간·전력·오버슈트는 원본 모델의 계산 결과이며 새로운 KPI가 아니다.

## 구현과 검증

- `sim/thermal.js`: 공통 열 플랜트와 두 프리셋, 원본 헤드 해석·드리프트·수냉 계산.
- `sim/ncf.js`, `muf.js`, `warpage.js`, `alignment.js`, `cycle.js`, `recipe.js`: 기존 순수식. `epoxy.*`, `recipe.*`, `cycle.*` 포함.
- `sim/plant.js`: 10 μs 하중 적분, 0.8 ms 서보, 직렬 강성, 50 FIFO, 열팽창 항, 3절점 열·열전대 플랜트. 제어 계산은 기존 C float wasm REFERENCE.
- `sim/rng.js`: xoshiro128** + SplitMix32 시드 확장 + Box–Muller. numpy 난수열과 동일하다고 가정하지 않는다.
- 새 공정 가정값은 도입하지 않았다. 기존 golden에 필요한 상수만 원본 파일·행 출처 주석과 함께 보존했다. `params.json`은 변경하지 않았다. 다층 결합 등 신규 파라미터를 사용하는 단계 3-C는 구현하지 않았다.
- `sim/test/cases.json`은 출력값을 포함하지 않는 독립 입력·메타데이터·출력 단위 명세다. golden과 id 집합(중복·누락·추가 포함), 입력·단위, model/function/source, 출력 이름·단위·중첩 모양을 대조하고 구현으로 계산한 값만 비교한다. golden 파일은 변경하지 않았다.

실행 결과:

| 명령 | 실제 결과 |
|---|---|
| `node --test sim/test` | tests=119, pass=119, fail=0. golden 111개 + 상위 테스트 1개 + params 5개 + RNG 2개 |
| `npm --prefix sim test` | 동일하게 119 pass / 0 fail |
| golden 요약 | `SUMMARY total=111 golden_pass=103 float_exception_pass=8 failures=0` |
| `make -C firmware wasm` | 성공. 기존 `fw_set_temp_period_ms`를 export하고 재빌드 |
| `make -C firmware test-wasm` | `Validation 6: PASS (1200 rows, 14400 values, max_abs_error=8.119141e-6; rel=1e-3/abs=1e-4)` |
| 기본 `python3 -I calc/reference/check_golden.py` | Python 3.15.2에 numpy 없음: `ModuleNotFoundError: No module named 'numpy'` |
| 기존 Python 3.12의 `python3 -I calc/reference/check_golden.py` | `SUMMARY vectors=111 compared_values=262 different_values=11 failures=0 max_relative_error=8.625599925950891e-15`, `ALL OK` |
| 기존 Python 3.12의 `python3 calc/contact_transient.py` | 6항목 모두 수기 값과 일치, 차이 0 N |
| 기존 Python 3.12의 `python3 calc/run_midterm.py` | 13케이스: 성공 10, 의존성 누락 2, 원본 FEM 오류 1 (아래 표) |

이번 환경에서는 아래처럼 이미 설치된 Python 3.12를 선택했다. 새 의존성을 설치하거나 전역 환경을 바꾸지 않았다.

```sh
PATH=/Library/Frameworks/Python.framework/Versions/3.12/bin:$PATH python3 -I calc/reference/check_golden.py
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 calc/contact_transient.py
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 calc/run_midterm.py
```

초기 의존성 확인에서 matplotlib의 기본 사용자 캐시 폴더가 쓰기 불가라는 경고와 fontconfig 캐시 경고도 출력됐다.
원본 실행 래퍼는 요청된 임시 작업 폴더 안에 matplotlib 설정 폴더를 두며 원본은 수정하지 않는다.
Python 3.12에서 실제 원본 계산은 아래 결과대로 완료했다. cv2는 없으므로 두 비전 원본은 실행하지 못했다.

## #3 — 열 모델 두 벌

증상: 10장 설명과 달리 7·10장의 열 이산화와 상수가 다르다.
원인: thermal.py:9-41과 control_sim.py:45-64가 다른 설정을 사용한다.
해결: 하나의 `createHeadModel` / `headStep`에 절점 수·손실 면적·열용량 인자를 두고 프리셋으로 원본 차이를 보존했다.

| 프리셋 | MACOR 절점 | 손실 면적 m² | 팁 열용량 J/K | 사용처 | golden 결과 |
|---|---:|---:|---:|---|---|
| `ch7_16node` | 16 | 0.0017 | 8.7748 | 7장 헤드 해석, 단계 3-C 적층 기본 | head_sim 승온·드리프트·냉각 2개·PI 램프 총 5개 모두 원래 tolerance 통과 |
| `ch10_3node` | 3 | 0.0011 | 8.77 | 10장 wasm SIL 온도 플랜트 | temp_sim 10/100 ms 2개 모두 승인 float tolerance 통과 |

`headSim`은 7장 원본 PI/on-off 실험을 재현한다. 10장 프리셋의 제어 실행은 `tempSim(fw, opts)`로만 하며, 10장 제어기를 JS로 구현하지 않았다.
wasm import는 sim 기준 `../firmware/build/controller.js`이고 브라우저도 같은 ESM import를 쓴다. Node의 fs/wasmBinary 주입은 테스트에만 있다. 브라우저에서의 실제 실행 검증은 단계 4에 남아 있다.

## #4 — 7장 PI 유지 설명과 on/off 결과 불일치

증상: 7장 원고는 PI 유지라고 설명하지만 원본 JSON은 Kp=1e6/Ki=0으로 생성됐다.
해결: golden 재현 조건을 보존하고, thermal.py 기본 이득 40/8의 비교 실험만 추가했다. 파라미터를 결과에 맞춰 조정하지 않았다.

공통 조건은 ch7_16node, 20→400 ℃ 설정 스텝, 400 W, dt=0.005 s, 종료 300 s, 0.1 s 기록이다.
도달 시간은 원본 정의대로 **399 ℃ 이상인 첫 기록**이며, 유지 전력은 마지막 200개 기록 평균,
오버슈트는 전체 기록의 `max(T)−400`이다. 원본은 기록 시각에 해당 Euler 한 스텝 갱신 후 온도를 붙인다.

| 이득 Kp/Ki | 도달 시간 s | 유지 전력 W | 기록 기준 오버슈트 ℃ | 최종 재킷 열류 W |
|---|---:|---:|---:|---:|
| 1e6 / 0 (원본 on/off 조건) | 17.200000000000863 | 65.43345523525795 | 0.1889939470181048 | 55.46142648119621 |
| 40 / 8 (thermal.py 기본 PI) | 17.200000000000863 | 67.69794941998605 | 3.6681617210735453 | 55.45098549147936 |

도달 시간이 같아도 유지 응답은 다르다. 유지 전력 약 65 W를 40/8 PI의 결과로 설명하면 안 된다.
7장 원고 변경은 요청대로 단계 6에 남겼다.

## #5 — 수기 contact_transient_N

증상: control_sim.py는 이 키를 생성하지 않는다.
해결: `calc/contact_transient.py`는 임시 복사본에서 **원본 contact_speed_study.py 전체를 그대로 실행**하고 stdout 6행을 파싱한다.
JSON은 stdout, 항목별 차이는 stderr로 출력한다. `calc/out/`은 .gitignore에 추가했다.
원본 초기 시드 3과 루프 순서(1 ms→10 ms, 접근 20→200→500 μm/s), 노이즈 0.002 N을 그대로 따른다.
수기 값과 같은 0.001 N 자리 반올림 후 비교다.

| 주기 | 접근 μm/s | 수기 N | 재생성 N | 차이 N |
|---|---:|---:|---:|---:|
| 1 ms | 20 | 0.002 | 0.002 | 0 |
| 1 ms | 200 | 0.010 | 0.010 | 0 |
| 1 ms | 500 | 0.035 | 0.035 | 0 |
| 10 ms | 20 | 0.052 | 0.052 | 0 |
| 10 ms | 200 | 0.088 | 0.088 | 0 |
| 10 ms | 500 | 0.131 | 0.131 | 0 |

노이즈가 있어도 초기 시드와 소비 순서가 같아 전부 일치했다. 시드나 선행 난수 소비가 달라지면 달라질 수 있다.
JS의 결정론 golden은 noise=0이므로 이 노이즈 표와 직접 같은 값이어야 하는 것은 아니다.

## #7 — 원본 실행 폴더

증상: 일부 원본은 부모 폴더의 calc/fig, 일부는 calc 안과 ../fig를 가정한다.
해결: `calc/run_midterm.py`가 각 케이스마다 임시 `{calc,fig}` 구조에 원본을 복사하고 필요한 cwd에서 순차 실행한다.
성공/실패/의존성 누락/timeout을 표로 표시하고 나머지 케이스도 계속 실행한다. 기본 timeout은 스크립트당 600 s이며 실행 보호 설정이다.

실제 Python 3.12 실행 표 (종료 코드 1은 아래 3건의 미성공을 뜻함):

script / arguments | cwd | status | seconds | detail
--- | --- | --- | ---: | ---
process_physics.py  | parent | OK | 13.23 | completed in isolated copy
education_calc.py  | parent | OK | 0.15 | completed in isolated copy
thermal.py  | calc | OK | 14.55 | completed in isolated copy
control_sim.py  | calc | OK | 14.21 | completed in isolated copy
contact_speed_study.py  | calc | OK | 13.32 | completed in isolated copy
vision.py  | calc | MISSING DEPENDENCY | 0.07 | ModuleNotFoundError: No module named 'cv2'
vision_robust.py  | calc | MISSING DEPENDENCY | 0.05 | ModuleNotFoundError: No module named 'cv2'
error_budget.py  | parent | OK | 13.30 | completed in isolated copy
integration.py  | parent | OK | 13.13 | completed in isolated copy
drive_calc.py  | parent | OK | 0.06 | completed in isolated copy
fea_struct.py 10 static v5 0 | calc | FAIL | 0.75 | ZeroDivisionError: division by zero; original fea_struct.py:93-94: no load nodes on z=175 mm at h=10; unchanged
fea_struct.py 10 modal v5 0 | calc | OK | 5.40 | completed in isolated copy
fea_struct.py 5 static v5 0 | calc | OK | 32.40 | completed in isolated copy
SUMMARY cases=13 successful=10 unsuccessful=3


fea_struct.py h=10 static은 **수정하지 않았다**. 93-94행에서 z=175 mm 하중 면에 절점이 없어
`len(load)==0`으로 `F/len(load)`가 ZeroDivisionError를 낸다. h=5 static과 h=10 modal은 성공했다.
비전 2개는 `cv2` 미설치가 원인이며 NCC JS 테스트 전용 수치 참조는 외부 패키지 없이 통과했다.
기본 Python 3.15로 실행한 래퍼 표에서는 13개 모두 numpy 누락이었다.

## float 예외의 실제 오차

펌웨어 HANDOFF 4절 1번의 float 단정밀도 기준을 승인된 세 prefix에만 적용했다:
`control.force_sim.*`, `control.contact_peak.*`, `control.temp_sim.*`.
허용오차는 `max(1e-3*abs(ref), abs)`이며 abs는 하중 1e-4 N, 온도 항목 1e-3, 접촉 시간 1e-3 s다.
아래 `golden_limit`은 변경하지 않은 원래 `abs + rel*abs(ref)`다.
10개 후보 중 contact_peak 고속 2개는 원래 tolerance도 통과해서 golden_pass 103개에 포함된다.
나머지 8개만 float_exception_pass로 센다. 모든 접촉 시각은 원래 golden과 같았다.

| vector / output | ref | JS wasm SIL | 절대 오차 | golden_limit | 원래 통과 |
|---|---:|---:|---:|---:|---|
| `control.force_sim.low1N_1ms.noise0` / `t_contact` | 3.504000000014488 | 3.504000000014488 | 0 | 3.514e-07 | true |
| `control.force_sim.low1N_1ms.noise0` / `overshoot` | 0.03179382678407938 | 0.03179381941811377 | 7.36596562e-09 | 4.17938268e-09 | false |
| `control.force_sim.low1N_1ms.noise0` / `ss_err` | 0.00003041985522367341 | 0.00003041729306207941 | 2.56216159e-09 | 1.00304199e-09 | false |
| `control.force_sim.low1N_1ms.noise0` / `F_at_t_contact_plus_1s` | 1.0000004626607129 | 1.0000004822846373 | 1.96239245e-08 | 1.01000046e-07 | true |
| `control.force_sim.high20N_1ms.noise0` / `t_contact` | 1.103999999998765 | 1.103999999998765 | 0 | 1.114e-07 | true |
| `control.force_sim.high20N_1ms.noise0` / `overshoot` | 0.03487122401981679 | 0.03487136036369165 | 1.36343875e-07 | 4.4871224e-09 | false |
| `control.force_sim.high20N_1ms.noise0` / `ss_err` | 0.00003308232702536884 | 0.00003305995276292606 | 2.23742624e-08 | 1.00330823e-09 | false |
| `control.force_sim.high20N_1ms.noise0` / `F_at_t_contact_plus_1s` | 5.102499959345189 | 5.102500117999628 | 1.58654439e-07 | 5.11249996e-07 | true |
| `control.force_sim.high20N_10ms.noise0` / `t_contact` | 1.1099999999988044 | 1.1099999999988044 | 0 | 1.12e-07 | true |
| `control.force_sim.high20N_10ms.noise0` / `overshoot` | 0.054426445332453 | 0.05442570583455009 | 7.39497903e-07 | 6.44264453e-09 | false |
| `control.force_sim.high20N_10ms.noise0` / `ss_err` | 0.000047237082384299356 | 0.00004613842558498504 | 1.0986568e-06 | 1.00472371e-09 | false |
| `control.force_sim.high20N_10ms.noise0` / `F_at_t_contact_plus_1s` | 5.1024999052952795 | 5.102500024882975 | 1.19587695e-07 | 5.11249991e-07 | true |
| `control.force_sim.high20N_1ms_therm.noise0` / `t_contact` | 0.9769999999981884 | 0.9769999999981884 | 0 | 9.87e-08 | true |
| `control.force_sim.high20N_1ms_therm.noise0` / `overshoot` | 0.03487122402037457 | 0.03487130685793005 | 8.28375555e-08 | 4.4871224e-09 | false |
| `control.force_sim.high20N_1ms_therm.noise0` / `ss_err` | 0.00003308232737353478 | 0.000033023311701185776 | 5.90156723e-08 | 1.00330823e-09 | false |
| `control.force_sim.high20N_1ms_therm.noise0` / `F_at_t_contact_plus_1s` | 5.102499960378169 | 5.102500137438551 | 1.77060382e-07 | 5.11249996e-07 | true |
| `control.contact_peak.Ts0.001_ap0.02.noise0` / `peak_over_sp_0p3s` | 0.0017567551540360604 | 0.0017567052840998798 | 4.98699362e-08 | 1.17567552e-09 | false |
| `control.contact_peak.Ts0.001_ap0.02.noise0` / `t_contact` | 1.103999999998765 | 1.103999999998765 | 0 | 1.114e-07 | true |
| `control.contact_peak.Ts0.001_ap0.5.noise0` / `peak_over_sp_0p3s` | 0.03504164414375788 | 0.0350416400200409 | 4.12371698e-09 | 4.50416441e-09 | true |
| `control.contact_peak.Ts0.001_ap0.5.noise0` / `t_contact` | 0.04600000000000341 | 0.04600000000000341 | 0 | 5.6e-09 | true |
| `control.contact_peak.Ts0.01_ap0.02.noise0` / `peak_over_sp_0p3s` | 0.04663599276933983 | 0.0466359762451769 | 1.65241629e-08 | 5.66359928e-09 | false |
| `control.contact_peak.Ts0.01_ap0.02.noise0` / `t_contact` | 1.1099999999988044 | 1.1099999999988044 | 0 | 1.12e-07 | true |
| `control.contact_peak.Ts0.01_ap0.5.noise0` / `peak_over_sp_0p3s` | 0.13151355174061802 | 0.13151355017592617 | 1.56469185e-09 | 1.41513552e-08 | true |
| `control.contact_peak.Ts0.01_ap0.5.noise0` / `t_contact` | 0.05000000000000464 | 0.05000000000000464 | 0 | 6e-09 | true |
| `control.temp_sim.10ms.noise0` / `overshoot` | 1.3004117321842728 | 1.3004110120450036 | 7.20139269e-07 | 1.31041173e-07 | false |
| `control.temp_sim.10ms.noise0` / `stab_150` | 0.25422352443482055 | 0.2542233070902 | 2.17344621e-07 | 2.64223524e-08 | false |
| `control.temp_sim.10ms.noise0` / `stab_300` | 0.41156267490225673 | 0.41156239321730936 | 2.81684947e-07 | 4.21562675e-08 | false |
| `control.temp_sim.10ms.noise0` / `ramp` | 20.262696093918194 | 20.262696356578736 | 2.62660542e-07 | 2.02726961e-06 | true |
| `control.temp_sim.10ms.noise0` / `P_hold` | 65.87204882120115 | 65.87204544233994 | 3.37886121e-06 | 6.58820488e-06 | true |
| `control.temp_sim.10ms.noise0` / `T_at_50s` | 301.25692456712716 | 301.256925356165 | 7.8903787e-07 | 3.01266925e-05 | true |
| `control.temp_sim.100ms.noise0` / `overshoot` | 1.291647602944522 | 1.2916471914759313 | 4.11468591e-07 | 1.3016476e-07 | false |
| `control.temp_sim.100ms.noise0` / `stab_150` | 0.25289131112629093 | 0.2528920460145514 | 7.3488826e-07 | 2.62891311e-08 | false |
| `control.temp_sim.100ms.noise0` / `stab_300` | 0.4111524247677494 | 0.411155164226102 | 2.73945835e-06 | 4.21152425e-08 | false |
| `control.temp_sim.100ms.noise0` / `ramp` | 20.248157684864093 | 20.248156148986116 | 1.53587798e-06 | 2.02581577e-06 | true |
| `control.temp_sim.100ms.noise0` / `P_hold` | 65.85872496125097 | 65.85872366213603 | 1.29911494e-06 | 6.5868725e-06 | true |
| `control.temp_sim.100ms.noise0` / `T_at_50s` | 301.2267626474882 | 301.2267650283318 | 2.38084357e-06 | 3.01236763e-05 | true |

## HANDOFF와 달라진 점·남은 한계

1. 사용자 승인 float 예외를 적용했다. 그 밖의 golden tolerance는 변경하지 않았다.
2. 지시에 영상 처리는 단계 4라고 되어 있지만 전체 111개에 렌더링 3개·NCC 4개가 들어 있다. 이 7개는 테스트 전용 수치 참조 `sim/test/helpers/vision-reference.js`에서 계산하며 production `alignment.js`에는 영상 처리를 넣지 않았다. 단계 4의 실제 영상 기능은 여전히 미구현이다.
3. 100 ms 온도 비교를 위해 이미 존재하는 C 함수 `fw_set_temp_period_ms`를 wasm export에 추가했다. Makefile 변경도 재빌드 의존성에 포함했다. C 제어 로직과 MCU 산출물은 변경하지 않았다.
4. 기본 Python에는 numpy가 없어 기존 3.12로 검증했다. cv2 원본 2개는 의존성 누락으로 실행하지 못했다. 원본 FEM h=10 오류는 보존했으며 #7 전체 성공으로 보고하지 않는다.
5. `calc/midterm/`, Python 참조 구현, golden, params, HANDOFF 및 원고는 변경하지 않았다. push/PR/Issue 작성·수정은 하지 않았다.

## 커밋

`git log --oneline main..HEAD` (이 보고서 정리 커밋 직전):

```text
e5f5837 fix: 10장 열 제어는 wasm SIL 경로로 제한
f84e98b feat: 원본 계산 실행 래퍼 run_midterm.py (#7)
e7b5fc5 feat: contact_transient 재생성 스크립트 (#5)
692dace test: golden 111개 JS 대조와 float 예외 오차 출력
8c69f11 build: SIL 온도 비교용 기존 주기 설정 API wasm export
093e214 feat: SIL 플랜트와 wasm REFERENCE 제어기 연결
bab1d4d feat: 열 모듈 이식과 프리셋 2개 (#3)
b479a4a feat: NCF·MUF·휨·정렬·사이클 기존 식 이식
770b22c feat: 시드 PRNG xoshiro128**와 Box–Muller
```

문서 정리 커밋의 해시는 최종 응답의 커밋 목록에 추가한다.
