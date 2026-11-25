# 펌웨어 빌드·검증 (단계 C·D)

`make -C firmware test`는 C99, `-Wall -Wextra -Werror`로 빌드하며 실패 시
종료 코드 1을 반환한다. 플랜트는 double, 제어 상태·연산은 float다.

- 기본값은 `FW_MODE_FIRMWARE`. `fw_set_recipe()`에서 모드를 선택하며,
  golden 51개 지표는 항상 `FW_MODE_REFERENCE`로 비교한다.
- `fw_config.h`의 설계값 `v_max=0.5 mm/s`, `I_max=v_max/Ki`와 근거는
  [적분 제한 결정](docs/force_integral_limit.md)에 기록한다.
- 검증 2: 원본 노이즈 0 플랜트, 하중 네 시나리오와 온도 10 ms.
  하중 표의 도달 시간은 첫 `F >= 0.98*target` 시각에서 접촉 시각을 뺀 값이다.
  #13 판정 시작은 두 모드 모두
  `max(t_contact + target/ramp + 0.5 s, 첫 F >= 0.98*target 시각 + 0.5 s)`이며
  `t > 시작`인 표본의 최대 오차를 판정한다. `ss_original_N`과 도달 시각은
  판정하지 않는 관찰값이다. golden 비교의 원본 마스크는 변경하지 않는다.
  검증 2 하중 네 시나리오 × 두 모드, 온도 모두 PASS다.
- 검증 3: 테스트 플랜트의 선택적 실제 속도 한계 ±0.5 mm/s와 고착 외란.
  옵션 기본값은 꺼짐이다. 한계를 켜면 수락 속도와 실제 Z 속도를 함께 제한해
  위치 명령 backlog가 생기지 않게 한다. 고착 중 위치 명령도 누적하지 않는다.
  저레인지 1 N은 속도 한계만으로 포화한다. 고레인지 20 N, 5 N/s는 그 한계만으로
  포화하지 않으므로 접촉 후 3.7 s에 0.5 s 고착을 넣는다. 추가 조건은 저레인지
  접촉 직후 0.5 s 고착이다. 고착 시각·기간은 테스트 가정값이며 KPI가 아니다.
  각 12 s 동안 모든 PI 갱신의 적분을 관찰하며, 인터락 개입 없이 비교함을 검사한다.
- 검증 4: 경고/차단/하드웨어 고장과 경계값을 두 모드에서 주입한다.
  10 ms 분주 사이에도 매 1 ms 검사한다. 경고 중 Z·하중 설정값·PI·시퀀서는
  동결되고 온도 PI는 계속 실행한다. 래치는 히터도 0으로 만든다.
  `fw_reset_latch()`만 래치를 해제하며 조건이 남으면 즉시 재래치한다.
  `fw_init()`이나 레시피 변경은 기존 래치를 해제하지 않는다.

실물은 비교기·래치 회로가 소프트웨어와 무관하게 차단한다(10장 10.4절).
펌웨어 래치는 그 동작을 모사하고 상태를 보고한다.

시퀀서는 접근 → 접촉 판정/램프 → 유지를 하중 루프에 감싼다.
유지 시간은 호출자가 결정하며 `fw_release()`로 해제를 요청한다.
설정값을 레시피 속도로 0 N까지 내리고 측정 하중이 접촉 문턱 이하가 되면
상승한다. 잔류 압축을 푼 뒤 무하중에서 초기 간극 0.02 mm만큼 더 상승하고 정지한다
(설계값, 원본 `control_sim.py:12`의 초기 간극 재사용).

## 구조와 빌드

- `src/`: 하중·온도 PI, 시퀀서, 인터락. 하드웨어 접근은 `hal.h`만 사용한다.
- `hal/`: host 테스트 입력·출력, wasm 숫자 API, STM32H7 레지스터 최소 HAL.
- `mcu/`: FLASH 2 MB, DTCM 128 KB(데이터·BSS·스택), AXI SRAM 512 KB.
  startup은 벡터 테이블·FPU·data 복사·BSS 초기화 후 main을 호출한다.
- `test/`: golden 플랜트, 성능·안전·고정 입력 비교.
- `build/`: 일반 커밋은 `controller.bin`, `controller.js`, `controller.wasm`만.
  ELF·map·PC 실행파일·CSV 기록은 무시한다.

도구: make, C99 cc, Python 3, arm-none-eabi-gcc/objcopy/size, emcc, Node.
저장소 루트에서 실행한다. 모든 C 빌드는 `-std=c99 -Wall -Wextra -Werror -O2`다.

```sh
make -C firmware test       # PC 검증 1~4, 실패 시 비정상 종료
make -C firmware mcu        # controller.elf → controller.bin, size 출력
make -C firmware wasm       # controller.js + controller.wasm
make -C firmware test-wasm  # 별도 검증 6, 실패 시 종료 코드 1
```

MCU는 Cortex-M7, fpv5-d16 hard float이며 `-nostartfiles`, section GC를 쓴다.
HSI 64 MHz(/1), SysTick processor clock: `64000000/1000-1=63999`다.
PG0 active-high·pull-down 고장 입력은 임시 핀 설계값이다. 보드 연결은 확인하지 않았다.
실물 보드 없이 빌드 가능한 산출물까지만 검증했다. ADS1256 SPI, AD8495 내부 ADC,
20 kHz PWM, 서보·안전 상태 출력은 `TODO(board bring-up)` 틀이다.
센서 틀은 0을 반환한다. ST HAL·CMSIS vendor 헤더와 네트워크 다운로드는 사용하지 않는다.

## wasm API와 검증 6

ES module의 기본 export는 비동기 모듈 생성 함수다. `cwrap`/`ccall` 또는
모듈의 `_함수명`을 쓴다. 선형 메모리 growth를 끄고 `MALLOC=none`으로 빌드한다.

| 함수 | 인자·반환 |
|---|---|
| `fw_init()` | 기본 FIRMWARE 레시피, 기존 래치 보존 |
| `fw_wasm_set_recipe(spring,target,ramp,approach,period_ms,mode)` | N/mm, N, N/s, mm/s, 정수 ms, 0=REFERENCE/1=FIRMWARE; 성공 1 |
| `fw_step_1ms(force_meas_N,temp_meas_C)` | 두 float 측정값 저장 후 공통 코어 1 ms 실행 |
| `fw_reset_latch()` | 현재 측정값으로 수동 해제, 조건 잔존 시 재래치 |
| `fw_set_hw_fault(fault)` | 외부 고장 모사 입력 |
| `fw_get_z_velocity()`, `fw_get_heater_power()` | mm/s, W |
| `fw_get_mode()`, `fw_get_phase()` | 제어 모드, sequencer.h의 시퀀스 단계 |
| `fw_get_warning()`, `fw_get_latched()`, `fw_get_brake()`, `fw_get_sto()` | 정수 플래그 |
| `fw_get_force_setpoint()`, `fw_get_force_integral()`, `fw_get_temp_integral()` | N, N·s, ℃·s |

코어의 무인자 `fw_step_1ms`는 wasm 빌드에서만 `fw_core_step_1ms`로 이름을
바꾼다. PC·MCU의 API는 그대로다. 모듈을 새로 만들면 독립 상태를 얻는다.
검증 6은 `fixed_inputs.csv`의 미리 정한 600개 측정값을 두 모드에 각각 넣는다.
접촉 전 0 N, 접촉, 출력 포화, 경고·래치·하드웨어 고장·수동 리셋을 포함하며
모든 입력은 테스트 가정값이다. JS 플랜트와 출력 피드백은 없다.
PC 프로그램은 host HAL을, Node는 wasm HAL을 사용하며 각각 CSV를
`build/fixed_pc.csv`, `build/fixed_wasm.csv`에 기록한다.
출력 12열·1,200행(14,400값)을 `max(상대 1e-3, 절대 1e-4)`로 비교한다.
결과: PASS, 최대 절대 차이 `7.676563e-6`.

## 검증 7 — 출처·설계값 자체 확인 (2026-11-25)

| 확인 대상 | 출처·표기 확인 |
|---|---|
| fw_config.h: 1 ms tick, 하중 1 ms | HANDOFF 2절·control_sim.py:6, 호스트 tick은 설계값 |
| 접촉 강성 2000, PI 20 Hz·2 Hz·π | control_sim.py:8–10,40, 원본 이득식 |
| fw.c 기본 레시피 50 N/mm·20 N·5 N/s·0.02 mm/s | control_sim.py:6,38 고레인지 시나리오, 원본 시험 조건 |
| 접촉 문턱·램프 시작 0.1 N | control_sim.py:24,26 |
| 온도 10 ms·Kp=25·Ki=6·Kd=0, 적분 ±30, 히터 400 W | 10장 10.3·HANDOFF 3.2·control_sim.py:45,54–56 |
| 150→300 ℃, 20 K/s, 40·70 s | control_sim.py:65 프로파일 가정값 |
| 하중 ±0.5 mm/s, I_max=v_max/Ki | HANDOFF 3.1·10장 접근 속도·#6 결정, 설계값 |
| 경고 52 N/410 ℃, 차단 55 N/420 ℃ | 10장 10.4·HANDOFF 3.3, 설계값 |
| 상승 0.02 mm, 해제 문턱·순서 | 원본 초기 간극·HANDOFF 해제 단계, 설계값 |
| temp_ctrl.c·interlock.c | 위 상수 사용, 적분 차감 순서 원본 54–56행, 독립 실물 차단 모사 주석 |
| MCU HSI 64 MHz, /1, tick 1000 Hz, reload 63999 | RM0433 RCC·ARMv7-M SysTick, 클럭 선택·1 ms 설계값 |
| MCU PG0·pull-down·고장 극성, 16 KiB 스택 여유 | GPIO RM0433, 핀·극성·스택 크기 설계값 |
| 검증 2 98% 도달·0.5 s·max 유지 시작 | #13 결정, 테스트 코드에 설계값; golden 정의 보존 |

이득·주기·한계값의 출처와 새 설계값 표기를 확인했으며 누락 없음.
원문 KPI(±1 μm, 400 ℃, 50 N, 600 mm)와 피드백 요구 10 ms는
설계값·시험 가정값과 구분한다.
