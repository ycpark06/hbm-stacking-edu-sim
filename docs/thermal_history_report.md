# 단계 3-C1 검증 기록 — 열 이력·적층 휨·Issue #2

브랜치 `feat/thermal-history`. 원문 KPI나 업체 양산 공정의 검증 결과가 아니라, 출처가 붙은 물성과 교육용 공정 가정에 대한 모델 계산이다. HANDOFF 1절의 15 μm 간격, 주의 1/4·불량 20 μm 초과, 20 K/s, 40 N 및 출처별 업체 주장 표시는 변경하지 않았다. push·PR·Issue 조작은 하지 않았다.

## 구현과 사용

`sim/thermal.js`의 `buildStack({layers, toolContact_R, chuck, params})`는 N개의 Si 다이 중심 절점과 N+1개의 경계/층간 전도도를 반환한다. `layers`는 아래→위의 `{mode: 'TC-NCF'|'MR-MUF', thickness_um, molded?}` 배열이다. 두께 생략 시 params 기본값을 사용한다. 길이·접촉 저항을 제외한 모든 입력 물성·공정 기본값은 전달받은 `params`에서 읽는다. `toolContact_R`와 `chuck.R`의 단위는 K/W이며, 기본값은 params의 면적 저항을 다이 면적으로 나눈다. 척은 온도 경계이고 별도 베이스/기판은 추가하지 않았다.

각 절점 C는 Si와 그 아래 접합층 열용량의 합이다. Si 열저항은 중심에서 반씩 나누고, 접합층 저항 전체를 그 Si 아래에 둔다. 접합층의 독립 온도는 풀지 않는 집중정수 근사다. 초기 구현의 등가 중심(접합층 저항도 반씩 분할)은 다이 중심 온도와 달라 별도 fix 커밋으로 고쳤다. 이 변경은 접촉 파라미터 조정이 아닌 공간 이산화 수정이다. Si 중심 기준의 전도도 배치를 테스트에서 직접 확인한다.

TC-NCF 접합층은 NCF, MR-MUF 미충전층은 `materials.bump_layer_k_eff`를 사용한다. 후자는 `bump_layer_R_unit`의 16 μm/8 K·mm²/W에서 유도된 기존 2 W/mK 대리값으로 현재 간격에 적용한다. 두 값을 저항에 중복 합산하지 않는다. 원 문헌은 **underfilled** 측정이므로 미충전 범프층에 대한 불확실성이 남는다. 미충전 열용량은 Cu/SnAg 범프 체적률만 반영한다. `molded:true`는 MUF k·ρ·cp로 전환한다.

`stackStep({T}, input, model, dt)`는 후진 오일러 삼중대각 풀이로 새 상태와 `input_J`, `loss_J`, `stored_J`를 반환한다. `input`은 `P_W` 또는 `T_head_C` 중 하나와 선택적 `T_chuck_C`, `h_conv`, `T_amb_C`다. 생략한 헤드/척 경계는 단열이다. 대류는 측면과 노출 상면에 적용하고 툴 접촉 시 상면 대류를 제외한다. 입력·손실은 적분 끝점 온도로 평가하여 BE 에너지 수지를 보존한다. 잠열·복사·경화 발열은 C1에서 제외한다.

`stackSim(model, schedule)`는 층 추가 시 기존 온도를 보존하고 새 다이는 주위 온도로 넣는다. 결과는 `history`(t_s, T[], phase, event), `layers`(peak_C, time_above_s, reheat_count, subsequent_reheats, crossings_by_phase)다. 액상선은 `solder.liquidus_snag=221 ℃`, 교차 시간은 연속 기록 사이 선형 보간이다. **재가열 횟수(reheat_count)는 첫 접합/tack까지 포함한 아래→위 액상선 교차 총수**다. 첫 교차를 제외한 값은 별도 `subsequent_reheats=max(0,reheat_count−1)`로 기록한다. 따라서 “매번 녹는 TC N층”이라면 총수는 N, 후속 재가열은 N−1이다. 가열 명령 횟수와 액상선 교차 횟수는 다르다.

`tcncfSchedule(N, params)`는 층마다 100→300 ℃를 장비값 20 K/s로 승온, 3.2 s 유지, 1.7 s에 100 ℃까지 냉각하며 척은 100 ℃다. 80 ℃/s는 비교 문헌값으로만 남는다. 헤드 온도는 지정 경계를 이상적으로 추종한다고 가정하며, C1 적층 모델은 헤드의 400 W 제한·wasm 제어 응답까지 결합하지 않는다. 기존 `ch7_16node`/`ch10_3node`와 golden은 보존했다. #2 계산은 `ch7_16node`를 직접 사용한다.

`mrmufSchedule`은 층마다 240 ℃ 1 s tack, 총 3 s 사이클의 잔여 시간은 툴 분리·척/대류 냉각이다. 전체 적층 후 예열→소크→승온→shoulder→피크→냉각의 리플로우 1회다. 235.5 ℃ shoulder는 액상선과 피크의 중간 온도라는 **가정**이며, 20 s 피크 유지와 90 s 액상선 위 프로그램 시간을 동시에 구성하기 위한 구간이다. 90 s 문헌의 SAC217 기준을 SnAg221 경계에 차용했음을 params에 명시했다. 실제 다이 TAL은 계산값을 기록한다. 오븐과 척에 같은 온도 프로그램을 주므로 하부는 강하게 가열된다. 몰딩 후 열용량 전환은 buildStack에서 지원하고, 이 기본 스케줄은 리플로우까지다.

`laminateCurvature(layers)`는 아래→위 적층의 A/B/D 및 열합력/모멘트를 풀며 두께 중간면의 eps0와 kappa를 반환한다. 입력은 `{t_m,E_Pa,alpha,dT_K,nu?}`이고 nu를 주면 E/(1−nu), 생략하면 원본 Timoshenko와 같은 strip E를 사용한다. `stackWarpHistory`에는 각 시점의 전체 접합된 적층체와 T_C/stress_free_C(또는 dT_K), die_size_m를 전달한다. 휨은 원본 `warpSagitta=κL²/8`로 환산한다. `thermalWarpSteps`가 열 이력을 이 형식으로 바꾼다.

TC-NCF의 각 새 Si/NCF 쌍은 해당 층 유지 종료 시 계산된 접합 온도가 무응력 기준이다. 기존 층의 기준은 보존한다. MR-MUF Si/범프는 tack에서 임시 기준을 부여한 뒤 리플로우 피크 종료의 층별 온도로 재설정한다. 몰딩 MUF는 가정 경화 온도 175 ℃가 무응력 기준이며 Si의 리플로우 기준은 유지한다. 몰딩 전 예열·경화·상온 냉각은 평형 끝점으로 평가하고, 몰딩 과도 열 이력·NCF 경화도는 C2 이후 범위다. 무응력 기준을 갖는 선형 strip의 재평가이며, 부착 시 이전 곡면의 기하학적 상속, 점탄성, 경화 수축, Tg 전후 물성·소성 및 기판 구속을 계산하지 않는다. 상온 E/cte1의 전 온도 적용도 명시적 가정이므로 고온의 정량 예측으로 사용하지 않는다.

## 기본 조건의 열 이력

모든 경우 간격 15 μm, 다이 5 mm. 최고 온도와 TAL은 맨 아래 Si 절점이다. 전체 층별 수치와 층수별 최대 휨은 [c1_results.json](../sim/test/c1_results.json)에 있다.

| 모드 | N | 두께 μm | 아래층 최고 ℃ | 교차 총수 | 첫 교차 제외 | TAL s |
|---|---:|---:|---:|---:|---:|---:|
| TC-NCF | 2 | 100 | 264.4680 | 1 | 0 | 6.2922 |
| TC-NCF | 2 | 50 | 264.8404 | 1 | 0 | 6.3117 |
| TC-NCF | 4 | 100 | 264.4680 | 1 | 0 | 6.2922 |
| TC-NCF | 4 | 50 | 264.8404 | 1 | 0 | 6.3117 |
| TC-NCF | 8 | 100 | 264.4680 | 1 | 0 | 6.2922 |
| TC-NCF | 8 | 50 | 264.8404 | 1 | 0 | 6.3117 |
| TC-NCF | 12 | 100 | 264.4680 | 1 | 0 | 6.2922 |
| TC-NCF | 12 | 50 | 264.8404 | 1 | 0 | 6.3117 |
| MR-MUF | 2 | 100 | 250.0000 | 1 | 0 | 90.0000 |
| MR-MUF | 2 | 50 | 250.0000 | 1 | 0 | 90.0000 |
| MR-MUF | 4 | 100 | 250.0000 | 1 | 0 | 90.0000 |
| MR-MUF | 4 | 50 | 250.0000 | 1 | 0 | 90.0000 |
| MR-MUF | 8 | 100 | 250.0000 | 1 | 0 | 90.0000 |
| MR-MUF | 8 | 50 | 250.0000 | 1 | 0 | 90.0000 |
| MR-MUF | 12 | 100 | 250.0000 | 1 | 0 | 90.0000 |
| MR-MUF | 12 | 50 | 250.0000 | 1 | 0 | 90.0000 |

**TC-NCF N−1 기대는 충족하지 않았다.** 첫 접합에서는 약 264 ℃이지만 적층이 늘면 헤드에서 아래층까지 NCF 직렬 열저항이 추가되고, 아래층은 100 ℃ 척에 계속 연결된다. 후속 가열 때 아래층은 221 ℃를 다시 넘지 않는다. 가열 명령 N회가 재용융 N회라는 보장은 없다. 테스트는 실제 이력에서 교차를 독립적으로 다시 세고 기대 불일치를 diagnostic에 출력한다. 기대 N−1을 강제하는 assertion으로 물리 결과를 고정하지 않았다.

기본 MR-MUF에서는 모든 층의 tack 교차가 0이며, **각 층이 전체 리플로우에서 한 번** 넘는다. 액상선 위 프로그램 90 s를 실제 온도에 더하지 않고, 온도 이력에서 따로 적분했다. 아래 접촉 저항 민감도에서는 tack 교차가 생기기도 하며, 그 경우 총수에 그대로 포함된다. 합성 tack→냉각→리플로우 테스트로 tack 포함 교차 2회/후속 1회 정의를 확인했다.

## 최대 휨과 판정

최대는 완성된 N층만이 아니라 **1층부터 전체 접합·냉각 과정**의 |w| 최대다. 판정은 기록용이며 테스트에 고정하지 않았다. 주의는 3.75 μm 초과, 불량은 20 μm 초과다.

| 모드 | N | 100 μm 최대 휨 μm | 판정 | 50 μm 최대 휨 μm | 판정 |
|---|---:|---:|---|---:|---|
| TC-NCF | 2 | 9.9279 | 주의 | 42.5142 | 불량 |
| TC-NCF | 4 | 9.9279 | 주의 | 42.5142 | 불량 |
| TC-NCF | 8 | 9.9279 | 주의 | 42.5142 | 불량 |
| TC-NCF | 12 | 9.9279 | 주의 | 42.5142 | 불량 |
| MR-MUF | 2 | 6.7234 | 주의 | 27.6734 | 불량 |
| MR-MUF | 4 | 6.7234 | 주의 | 27.6734 | 불량 |
| MR-MUF | 8 | 6.7234 | 주의 | 27.6734 | 불량 |
| MR-MUF | 12 | 6.7234 | 주의 | 27.6734 | 불량 |

각 N에서 최대가 같은 것은 초기 저층 적층의 휨이 지배하기 때문이다. 층수에 따라 휨이 단조 증가하도록 가정하지 않았다. 50 μm 12층 TC-NCF의 불량 예상은 이 strip 모델에서는 관찰되지만, MR-MUF 50 μm도 최대 휨 기준으로 불량이다. 업체 공정 간 우열로 일반화할 수 없다.

시간 간격 0.05→0.025 s, N=12/50 μm 비교(세부 수치는 JSON):

| 모드 | 아래층 최고 온도 차 ℃ | TAL 차 s | 최대 휨 차 μm |
|---|---:|---:|---:|
| TC-NCF | 0 | 2.84e-14 | 0.243815 |
| MR-MUF | 1.14e-13 | 7.72e-12 | 0.000000 |

후진 오일러의 안정성과 시간 정확도는 별개다. 얇은 다이의 빠른 transient에서 최대 휨은 간격 의존성이 남으므로 이 차이도 기록한다.

## 가정 민감도

N=12, 50 μm에서 두 접촉 면적 저항을 각각 범위 양끝으로만 변경하고 나머지는 기본값을 유지했다. 범위 1e-6~1e-4 m²K/W는 실측 부재에 따른 한 차수 아래·위 가정이다. 기본값을 결과에 맞춰 수정하지 않았다.

| 모드 | 변경 항목 | m²K/W | 아래층 최고 ℃ | 교차 총수 | 최대 휨 μm | 판정 |
|---|---|---:|---:|---:|---:|---|
| TC-NCF | tool_contact_R_area | 1e-06 | 295.222 | 1 | 50.243 | 불량 |
| TC-NCF | tool_contact_R_area | 0.0001 | 164.485 | 0 | 17.498 | 주의 |
| TC-NCF | chuck_contact_R_area | 1e-06 | 258.361 | 1 | 40.838 | 불량 |
| TC-NCF | chuck_contact_R_area | 0.0001 | 286.244 | 3 | 48.062 | 불량 |
| MR-MUF | tool_contact_R_area | 1e-06 | 250.000 | 2 | 40.898 | 불량 |
| MR-MUF | tool_contact_R_area | 0.0001 | 250.000 | 1 | 6.537 | 주의 |
| MR-MUF | chuck_contact_R_area | 1e-06 | 250.000 | 1 | 20.063 | 불량 |
| MR-MUF | chuck_contact_R_area | 0.0001 | 250.000 | 2 | 39.837 | 불량 |

툴 접촉 가정은 두 모드 모두 판정을 바꾼다. MR-MUF 교차 총수가 2인 행은 첫 tack과 전체 리플로우를 모두 센 결과다. 따라서 “MR-MUF는 열 교차가 항상 1회”도 경계/펄스 조건에 의존한다.

## Issue #2 — 헤드 열팽창

증상: `control_sim.py:38`의 2.6 μm/s는 7장 결과라는 설명과 달리 계산 근거가 없다. `sim/head_drift.js`는 `dL/dt=Σα_i L_i dT_i/dt`를 계산하고, 기존 하중 golden의 상수는 변경하지 않는다.

도달은 7장과 같은 첫 399 ℃ 이상 기록 17.2 s, 정렬은 그로부터 90 s 후인 107.2 s다. `ch7_16node` 원본 on/off 제어로 계산한 정렬 중심 10 s의 0.1 s 간격 기록을 선형 회귀한다. 온도는 구간 평균이다. 팁 온도의 스위칭 잔차 때문에 작은 음의 팁 기울기가 가능하다. MACOR는 **각 16절점 기울기**를 구한 뒤 길이 균등 가중 합산하며 JSON에 절점별 값도 저장했다.

`spec.py`의 box dz와 cylinder z_top−z_bottom을 읽어 길이를 대조했다. 표의 길이는 CAD 외형 높이로 확인되지만, 실제 열팽창 유효 길이/직렬 하중 경로로 채택하는 것은 모두 **가정**이다. 특히 Flexure의 실제 변형 경로는 외형 dz와 다를 수 있다. 재킷과 그 위 부품은 헤드 열 모델의 20 ℃ 고정 경계에 묶여 0 기여다. 이 모델에는 이 부품들의 독립 동적 온도가 없으므로 0이 실측 결론이라는 뜻은 아니다. Z rail·motor는 병렬 지지/구동 경로여서 이 직렬 경로에 더하지 않는다.

AlN/MACOR CTE는 원본 thermal.py, steel은 원본 스테인리스 값의 CAD steel 대리 가정이다. Al은 [Kaiser 6061 제조사 자료](https://online.kaiseraluminum.com/depot/PublicProductInformation/Document/1071/Kaiser_Aluminum_6061_Pipe_Tube.pdf)의 23.6 ppm/K를 CAD al에 대리 적용하는 가정이다.

| 부품 | 길이 mm (유효 길이 가정) | CTE ppm/K | 온도 ℃ | dT/dt K/s | 기여 μm/s |
|---|---:|---:|---:|---:|---:|
| Collet_Tool | 10 | 17 | 400.07350 | -0.00023925 | -0.00004067 |
| AlN_Heater | 5 | 4.5 | 400.07350 | -0.00023925 | -0.00000538 |
| MACOR_Insulator | 16 | 9.3 | 200.63090 | 0.26474432 | 0.03939395 |
| Cooling_Jacket | 19 | 23.6 | 20.00000 | 0.00000000 | 0.00000000 |
| Gimbal_Lockable | 16 | 17 | 20.00000 | 0.00000000 | 0.00000000 |
| Load_Cell_100N | 16 | 17 | 20.00000 | 0.00000000 | 0.00000000 |
| Flexure_Leaf_Spring | 18 | 17 | 20.00000 | 0.00000000 | 0.00000000 |
| Theta_Stage | 16 | 17 | 20.00000 | 0.00000000 | 0.00000000 |
| Z_Carriage | 74 | 23.6 | 20.00000 | 0.00000000 | 0.00000000 |
| **계산 합계** | | | | | **0.03934790** |
| 원본 비교 상수 | | | | | 2.60000000 |

계산 합계는 원본의 1.5134% (약 66.08배 작음)다. MACOR 실제 CAD 높이 16 mm를 사용했고, 기존 `macorDriftMetrics`의 기본 20 mm를 가져오지 않았다. **2.6 μm/s를 7장 모델에서 유도한 값으로 설명할 근거는 확인되지 않는다.** 이 표와 가정·한계를 Issue #2 기록에 사용할 수 있다.

## 추가한 params 전 목록

기존 항목은 수정하지 않았다. 아래 신규 leaf는 모두 kind와 source를 갖는다. 문자열 model 항목도 근사를 한곳에 기록하기 위한 params 항목이다. 각 source의 전체 문장은 JSON에 있으며 여기도 보존한다.

| 경로 | 값 | 단위 | kind | source/근거 |
|---|---|---|---|---|
| `thermal_stack.ambient_temp` | 20 | C | midterm | calc/midterm/thermal.py:6의 주위 온도를 적층 초기 온도로도 사용한다. |
| `thermal_stack.dt` | 0.05 | s | assumption | 얇은 접합층의 빠른 응답을 기록하기 위한 후진 오일러 시간 간격. 1/2 간격 수렴 결과를 함께 보고한다. |
| `thermal_stack.h_conv` | 10 | W/m2/K | assumption | calc/midterm/thermal.py의 자연대류 10을 다이 노출 측면과 상면에 적용하는 가정. 복사는 별도로 포함하지 않는다. |
| `thermal_stack.h_oven` | 100 | W/m2/K | assumption | 강제 순환 리플로우 오븐의 대류를 자연대류보다 큰 100으로 근사한다. 장비 측정값이 없으며 리플로우 경계는 척에도 같은 프로파일을 준다. |
| `thermal_stack.tool_contact_R_area` | 1e-05 | m2*K/W | assumption | 공개 툴 접촉 저항이 없어, params materials.bump_layer_R_unit의 8e-6 m2 K/W와 같은 차수인 1e-5를 면적 접촉 저항으로 가정한다. 결과 보정용 값이 아니다. 민감도 범위는 실측 부재에 따른 한 차수 아래·위(1e-6~1e-4)로 가정한다. |
| `thermal_stack.chuck_contact_R_area` | 1e-05 | m2*K/W | assumption | 척 접촉 실측값이 없어 툴과 같은 면적 접촉 저항을 가정한다. 척은 유한 열용량 대신 온도 경계로 둔다. 민감도 범위는 실측 부재에 따른 한 차수 아래·위(1e-6~1e-4)로 가정한다. |
| `thermal_stack.unfilled_gap_capacity` | Cu/SnAg pillars only; void capacity neglected | model | assumption | MR-MUF 미충전 간격은 지름/피치에서 계산한 범프 체적률만 열용량에 반영한다. 열전도는 underfilled 문헌 대리값 bump_layer_k_eff를 사용하므로 미충전 저항의 불확실성이 있다. |
| `thermal_stack.mechanical_model` | 1D strip; constant room-temperature moduli and cte1; no substrate | model | assumption | 독립 적층체의 열 휨만 비교한다. C2 경화·점탄성 이전 단계이므로 온도 의존 탄성률·Tg·경화 수축·소성·기판 구속을 제외한 선형 탄성 민감도 모델이다. |
| `thermal_stack.mold_model` | replace effective gap with MUF at cure_temp; retain Si reflow reference | model | assumption | 몰딩 후 간격을 균질 MUF로 치환한다. 수지 무응력 온도는 가정 경화 온도이고 Si는 리플로우 피크를 유지한다. 범프 기계 강성의 병렬 기여는 이 단계에서 제외한다. |
| `thermal_stack.reflow_shoulder_temp` | 235.5 | C | assumption | 리플로우 액상선 위 시간과 피크 유지 시간을 함께 지정하기 위해 SnAg 액상선 221 ℃와 피크 250 ℃의 중간 온도 235.5 ℃에 shoulder dwell을 둔다. 양산 오븐 프로파일이 아닌 교육용 구간 구성 가정이다. reflow.time_above_liquidus의 SAC217 기준 시간을 SnAg221 프로그램 경계에 적용한다. |
| `thermal_stack.volume_model` | die-centred node; full gap below; gap capacity lumped to die | model | assumption | 층별 온도를 Si 다이 중심 온도로 정의한다. Si 열저항은 반씩 나누고 충전층 열저항은 해당 다이 아래에 전부 둔다. 매우 얇은 간격의 별도 온도를 풀지 않고 열용량을 다이에 합친 1차원 근사이다. 툴 접촉 중 상면 대류는 제외한다. |
| `head_drift.alignment_wait` | 90 | s | midterm | 중간 보고서 7장: 설정 온도 도달 90 s 후 정렬. |
| `head_drift.fit_window` | 10 | s | assumption | 7장 on/off 제어의 스위칭 온도 진동을 평균화하기 위해 정렬 시각 중심 10 s 구간의 최소제곱 온도 기울기를 사용한다. 순간 기울기는 드리프트로 해석하지 않는다. |
| `head_drift.target_temp` | 400 | C | midterm | calc/midterm/thermal.py의 7장 가열 조건. |
| `head_drift.arrival_threshold` | 399 | C | midterm | calc/midterm/thermal.py: 설정 도달은 첫 399 ℃ 이상 기록 시점. |
| `head_drift.dt` | 0.005 | s | midterm | calc/midterm/thermal.py의 적분 시간 간격. |
| `head_drift.sample_period` | 0.1 | s | midterm | calc/midterm/thermal.py의 기록 간격. |
| `head_drift.power` | 400 | W | midterm | calc/midterm/thermal.py의 최대 히터 전력. |
| `head_drift.original_drift` | 2.6 | um/s | midterm | calc/midterm/control_sim.py:38의 비교용 상수. 7장 계산 근거가 없어 예측 입력으로 사용하지 않는다. |
| `head_drift.temperature_mapping` | Collet/AlN=tip; MACOR=16-node mean; jacket and above=ambient | model | assumption | 7장 모델은 팁과 MACOR 16절점만 동적으로 푼다. 수냉 재킷은 20 ℃ 고정 경계이며 그 위 부품도 같은 고정 온도로 가정한다. 이 가정 아래 상부 기여는 0이며 실장비 전체 드리프트 검증이 아니다. |
| `head_drift.steel_cte` | 17 | ppm/K | assumption | CAD steel을 calc/midterm/thermal.py:6의 스테인리스 17 ppm/K로 대리한다. CAD에는 강종 정보가 없으므로 재료 대응은 가정이다. |
| `head_drift.aln_cte` | 4.5 | ppm/K | midterm | calc/midterm/thermal.py:6의 AlN 물성. |
| `head_drift.macor_cte` | 9.3 | ppm/K | midterm | calc/midterm/thermal.py:6의 MACOR 물성. |
| `head_drift.al_cte` | 23.6 | ppm/K | assumption | https://online.kaiseraluminum.com/depot/PublicProductInformation/Document/1071/Kaiser_Aluminum_6061_Pipe_Tube.pdf ; 20–100 ℃ 6061 대표값. CAD al의 합금 미지정이므로 6061 대응은 가정이다. |
| `head_drift.Collet_Tool_length` | 10 | mm | assumption | cad/midterm/spec.py: Collet_Tool의 box dz 또는 cylinder z_top−z_bottom. CAD 외형의 z 높이이며 직렬 하중 경로의 유효 열팽창 길이로 사용하는 것은 가정이다. Flexure는 실제 변형 경로 대신 외형 높이를 사용한다. |
| `head_drift.AlN_Heater_length` | 5 | mm | assumption | cad/midterm/spec.py: AlN_Heater의 box dz 또는 cylinder z_top−z_bottom. CAD 외형의 z 높이이며 직렬 하중 경로의 유효 열팽창 길이로 사용하는 것은 가정이다. Flexure는 실제 변형 경로 대신 외형 높이를 사용한다. |
| `head_drift.MACOR_Insulator_length` | 16 | mm | assumption | cad/midterm/spec.py: MACOR_Insulator의 box dz 또는 cylinder z_top−z_bottom. CAD 외형의 z 높이이며 직렬 하중 경로의 유효 열팽창 길이로 사용하는 것은 가정이다. Flexure는 실제 변형 경로 대신 외형 높이를 사용한다. |
| `head_drift.Cooling_Jacket_length` | 19 | mm | assumption | cad/midterm/spec.py: Cooling_Jacket의 box dz 또는 cylinder z_top−z_bottom. CAD 외형의 z 높이이며 직렬 하중 경로의 유효 열팽창 길이로 사용하는 것은 가정이다. Flexure는 실제 변형 경로 대신 외형 높이를 사용한다. |
| `head_drift.Gimbal_Lockable_length` | 16 | mm | assumption | cad/midterm/spec.py: Gimbal_Lockable의 box dz 또는 cylinder z_top−z_bottom. CAD 외형의 z 높이이며 직렬 하중 경로의 유효 열팽창 길이로 사용하는 것은 가정이다. Flexure는 실제 변형 경로 대신 외형 높이를 사용한다. |
| `head_drift.Load_Cell_100N_length` | 16 | mm | assumption | cad/midterm/spec.py: Load_Cell_100N의 box dz 또는 cylinder z_top−z_bottom. CAD 외형의 z 높이이며 직렬 하중 경로의 유효 열팽창 길이로 사용하는 것은 가정이다. Flexure는 실제 변형 경로 대신 외형 높이를 사용한다. |
| `head_drift.Flexure_Leaf_Spring_length` | 18 | mm | assumption | cad/midterm/spec.py: Flexure_Leaf_Spring의 box dz 또는 cylinder z_top−z_bottom. CAD 외형의 z 높이이며 직렬 하중 경로의 유효 열팽창 길이로 사용하는 것은 가정이다. Flexure는 실제 변형 경로 대신 외형 높이를 사용한다. |
| `head_drift.Theta_Stage_length` | 16 | mm | assumption | cad/midterm/spec.py: Theta_Stage의 box dz 또는 cylinder z_top−z_bottom. CAD 외형의 z 높이이며 직렬 하중 경로의 유효 열팽창 길이로 사용하는 것은 가정이다. Flexure는 실제 변형 경로 대신 외형 높이를 사용한다. |
| `head_drift.Z_Carriage_length` | 74 | mm | assumption | cad/midterm/spec.py: Z_Carriage의 box dz 또는 cylinder z_top−z_bottom. CAD 외형의 z 높이이며 직렬 하중 경로의 유효 열팽창 길이로 사용하는 것은 가정이다. Flexure는 실제 변형 경로 대신 외형 높이를 사용한다. |
| `head_drift.max_heatup_time` | 400 | s | midterm | calc/midterm/thermal.py:43의 가열 해석 400 s 구간을 미도달 감지 상한으로 사용한다. |

## 검증 결과와 HANDOFF 차이

`node --test sim/test` 실제 결과: tests 128, suites 0, pass 128, fail 0, cancelled 0, skipped 0, todo 0 (약 0.53 s). 기존 golden 111개 유지, 기존 기타 8개 및 C1 신규 9개를 포함한다. `node --test sim/test/models.test.js`의 최초 8개 검사도 통과했고 이후 스케줄 검사 1개를 추가했다.

검사 내용: 부호까지 포함한 2층 CLT↔Timoshenko 상대 1e-9, 공통 열변형 무곡률, 이축계수, 단열/경계/대류 에너지 수지 상대 1e-9, 직렬 저항 정상해, 큰 dt의 유계성, Si 중심 열저항 배치, 충전 전/후 물성, 16개 시나리오의 유한 수치·독립 교차 계수, 리플로우 프로그램 TAL, tack 포함 정의, 무응력/냉각 휨 및 엄격한 판정 경계, CAD 길이·MACOR 16절점·부품별 팽창 합산.

`make -C firmware clean`을 실제 실행했다. 세 커밋 산출물 controller.bin/controller.js/controller.wasm 및 .gitkeep의 SHA256이 전후 동일하고, 만든 .o/.elf/.map/.csv probe는 삭제됐다. `distclean`은 임시 디렉터리에 Makefile과 산출물 fixture를 복사해 실행하여 세 산출물과 생성 header/테스트 바이너리가 삭제되고 .gitkeep와 무관한 소스가 보존됨을 확인했다. 생성 golden header는 clean에서 보존하고 distclean에서 제거한다. MCU/wasm 소스는 변경하지 않아 재빌드는 하지 않았다.

HANDOFF와 다른 점: `buildStack`에 브라우저에서도 파일 접근 없이 사용할 수 있도록 명시적 params 인자를 추가했다. 척은 허용된 온도 경계로 선택했다. C1의 TC N−1 숫자 기대는 실제 교차 수와 달라 실패 원인을 기록하고 카운터 정확성을 검증했다. 휨 표는 C1 어댑터로 만들었으며 최상위 `runStack`·C2 경화/유동 결합·자기정렬·결함률·전체 사이클은 이번 범위 밖이다. 데이터 파일은 후속 scenario 결과와 충돌하지 않도록 `c1_results.json`으로 구분했다. 7장 원고와 inbox는 수정하지 않았다. 권한/샌드박스 실패나 작업을 막는 외부 의존성은 없었다.
