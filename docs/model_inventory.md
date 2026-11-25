# 계산 모델 인벤토리: 중간 프로젝트 Python 모델의 JS 포팅 준비

- 대상: `중간보고서/02_설계보고서_작업/calc/*.py` 12개, 결과 JSON 11개, 보고서 4·7·9·10·13장
- 실행 환경: 원본을 별도 작업 폴더로 복사해 `python3 -I` 로 실행 (Chat 작업 환경) (Python 3.13, numpy 2.5.3, scipy 1.18.1, OpenCV 5.0.0)
- 같은 폴더의 산출물
  - `golden_vectors.json`: 식 111개, 출력값 258개
  - `reference_models.py`: 순수 함수로 정리한 참조 구현. `__main__` 을 실행하면 golden_vectors.json 을 다시 만든다.
- 줄 번호 표기: `파일:줄`. 보고서는 `04:69` 처럼 장 번호와 줄 번호로 쓴다.

---

## 0. 검증 결과

| 확인 항목 | 방법 | 결과 |
|---|---|---|
| 원본 스크립트 실행 | 복사본에서 하나씩 실행 (1절) | 폴더 구조만 맞추면 11개 모두 정상 종료. fea_struct 정적 해석은 h=10 에서 실패 |
| 원본 JSON 재현 | 폴더 구조를 맞춰 다시 실행하고 원본 JSON 과 항목별로 비교 | 9개 JSON 모두 일치 (상대오차 1e-9 이내). 차이는 control.json 의 `contact_transient_N` 키 하나뿐이다. 이 키는 어떤 스크립트도 만들지 않는다 |
| reference_models.py 가 원본 JSON 을 재현하는가 | `reference_models.py --verify-json <원본 calc>` | ALL OK. thermal, process_physics, education_calc, control(시드 3 난수열을 같은 순서로 소비), contact_transient, 각도, RSS 를 모두 재현 |
| golden_vectors 를 원본 코드로 다시 계산 | 대조용 보조 스크립트(Chat 작업 환경, 저장소 미포함): 원본 .py 를 exec 하고 난수 생성기를 0 노이즈로 바꿔 끼운 뒤 같은 입력으로 계산 | 258개 출력 모두 허용오차 안. 비전 측정을 빼면 최대 상대오차 5e-8 (dh/dt 수치미분 항목). 나머지는 1e-15 수준. 비전 NCC 는 cv2(float32)와 numpy(float64) 차이로 최대 1e-5 px |
| 다층 적층판 식이 Timoshenko 와 일치하는가 | 3절 D 의 식을 2층으로 계산해 `timo` 와 비교 | 크기가 상대 1e-15 안에서 같다. 부호 규약만 반대 |

---

## 1. 스크립트 요약표

| 스크립트 | 목적 (장) | 핵심 식 | 쓰는 JSON | 원본 그대로 실행 (calc_copy 에서) | 폴더 구조를 맞춘 실행 |
|---|---|---|---|---|---|
| process_physics.py | 공정 물리: 스퀴즈 유동, 필렛, 경화, 휨, 기울기 (4장) | Stefan, 체적 보존, 1차 아레니우스, Timoshenko | `calc/process_physics.json` | 실패: `calc/` 경로 없음 (66행) | 정상, 1 s |
| education_calc.py | DoE 예측, 언더필 Washburn, 하중 상한, 평행도 MC (13장) | Stefan, 필렛, Timoshenko, Washburn, 평면 맞춤 | `calc/education_calc.json` | 실패: 47행 경로 | 정상, <1 s |
| thermal.py | 헤드 승온·냉각·드리프트, 척 단열, 수냉판, 프리즘 홀더 (7장) | 1D 집중정수 + 명시적 오일러, kAΔT/t | `thermal.json` | JSON 은 쓰고 그림(88행 `../fig/`)에서 실패 | 정상, 3 s |
| control_sim.py | 하중 PI 루프(1 ms), 온도 PI 루프(10 ms) (10장) | 서보 1차 지연 + 직렬 스프링, PI, 집중정수 열 모델 | `control.json` | JSON 은 쓰고 그림(94행)에서 실패 | 정상, 3 s |
| contact_speed_study.py | 접근 속도·루프 주기별 접촉 하중 초과 (10장) | control_sim 의 force_sim 재사용 (exec, 2행) | 없음 (표준출력만) | 정상 | 정상 |
| vision.py | 합성 영상 NCC 검출, 아핀 보정, 폐루프 정렬 MC, 각도 (9장) | 면적 피복 렌더, NCC, 로그-포물선 보간, 최소제곱 아핀 | `vision.json` | JSON 은 쓰고 그림(112행)에서 실패 | 정상, 8 s |
| vision_robust.py | 블러·저대비·조명 기울기 영향 (9.4) | vision.py 앞부분 exec (2행) | `vision_robust.json` | 정상 | 정상 |
| error_budget.py | 정합 오차 예산 RSS + MC 100만 회 (5장) | σ(정규)=p, σ(균일)=p/√3, RSS | `calc/error_budget.json` | 실패: 27행 경로 | 정상, 1 s |
| integration.py | 각 장 결과로 예산 다시 합산 (12장) | 같은 RSS/MC, 세 열(예산·대표·보수) | `calc/integration.json` | 실패: 31행 경로 | 정상 |
| drive_calc.py | 볼스크루 토크·관성·위험속도, 판스프링 (6장) | 볼스크루 식, 판스프링 k=4Ebt³/L³ | `calc/drive_calc.json` | 실패: 54행 경로 | 정상 |
| fea_struct.py | 프레임 복셀 FEM 정적·모달 (8장) | hex8 강성 (2×2×2 가우스), CG, eigsh | `fea_{MODE}_{VAR}_e{ECC}_h{h}.json`, `fea_u.npy`, `fea_used.npy`, `fea_grid.json` | 시험하지 않음 (아래 참고) | `5 static v5 0` 정상 74 s, `10 modal v5 0` 정상 7 s, `10 static v5 0` **실패** (ZeroDivisionError, 94행) |
| (fea_summary.json) | v1~v5 요약 | — | 이 JSON 을 쓰는 스크립트가 없다 (손으로 만든 것) | — | v5 의 "0"=0.0012084 μm(정적 h=5), "f1"=176.97 Hz(모달 h=10)를 재현 |

**경로 문제.** 스크립트마다 기준 폴더가 다르다.
- `calc/` 의 부모 폴더에서 실행해야 하는 것: process_physics, education_calc, error_budget, integration, drive_calc (`calc/x.json`, `fig/` 를 씀)
- `calc/` 안에서 실행해야 하는 것: thermal, control_sim, vision, vision_robust, contact_speed_study, fea_struct (`x.json`, `../fig/` 를 씀)
- 원본은 고치지 않았다. 검증할 때는 `work_inventory/run/{calc,fig}` 구조를 만들어 각자 맞는 폴더에서 실행했다.

### 1.1 스크립트별 상세

#### process_physics.py (4장)
- **입력 (가정값):**
  - μ = 20 Pa·s (10행), h₀ = 150 μm (11행), h_min = 15 μm (12행, 필러 한계)
  - 다이 a ∈ {2, 5, 10} mm, F ∈ {0.2, 1, 5, 20} N (21-22행)
  - 다이 5 mm, 두께 0.3 mm, BLT 25 μm, 필렛 20 %·50 % (36-37행)
  - Ea ∈ {60, 80, 100} kJ/mol, T ∈ {120, 150, 180, 200} ℃, 기준점 180 ℃·30 min → 95 % (43-46행)
  - Si (130 GPa, 2.6 ppm/K), FR-4 (22 GPa, 16 ppm/K), 유리 (64 GPa, 3.3 ppm/K) (53행). 기판 0.4 mm, L = 10 mm, 다이 두께 0.1~0.725 mm, 경화 150·180 ℃ → 25 ℃ (54-60행)
  - 평행도 2 μm/10 mm (64행)
- **식:**
  - 스퀴즈 (13-19행): R = a/√π, 1/h² = 1/h₀² + 4Ft/(3πμR⁴), h ≥ h_min. 역으로 t = (1/h_T² − 1/h₀²)·3πμR⁴/(4F)
  - 필렛 (33-37행): V = a²·BLT + 2a·h_f², 따라서 h_f = √(max(V − a²·BLT, 0)/(2a))
  - 경화 (42-46행): k(T) = k_ref·exp(−Ea/R·(1/T − 1/T_ref)), k_ref = −ln 0.05/1800 s. t₉₅ = −ln 0.05/k. 85행: α(t) = 1 − e^(−kt)
  - 휨 (50-52, 60행): κ = 6(α₂−α₁)ΔT(1+m)² / (h[3(1+m)² + (1+mn)(m² + 1/(mn))]), m = h₁/h₂, n = E₁/E₂. 휨 w = κL²/8
  - 기울기 (64행): ΔBLT = 2/10·d [μm]
- **출력:** t25 표, 도포량 창, t₉₅ 표, 10 mm 휨 표, 기울기 BLT. → `process_physics.json`

#### education_calc.py (13장)
- **입력:**
  - DoE 수준 T (150, 180 ℃), F (0.5, 2 N), t (2, 10 s), V (0.66, 0.80 mm³). 2⁴⁻¹, D = ABC (15-19행)
  - 언더필: γ = 0.03 N/m, θ = 40°, μ = 0.8 Pa·s (25 ℃) / 0.1 Pa·s (90 ℃), L ∈ {5, 10} mm, 간격 ∈ {30, 50} μm (26-31행). 모두 가정값
  - 하중 상한: 1 / 0.5 / 2 MPa, 50 N 상한 (35-37행)
  - 평행도 MC: 15×15 점, 레이저 σ 0.5 μm, 5,000회, 시드 1 (40-46행)
- **식:**
  - h_t (스칼라, 6-7행)와 timo (10-12행)는 process_physics 의 것을 복사했다
  - fillet_pct = 100·h_f/t_die (8-9행)
  - Washburn 평행판 t = 3μL²/(γ·h·cosθ) (25, 31행)
  - 휨: timo(Si 0.3 mm, FR-4 0.4 mm, ΔT = T−25)·(5 mm)²/8 (22행)
- **출력:** doe 8회, underfill_s 8개, force_limit_N 5행, parallel_meas → `education_calc.json`

#### thermal.py (7장)
- **입력:**
  - AlN (k 170, ρ 3260, c 740, α 4.5 ppm/K), MACOR (1.46, 2520, 790, 9.3 ppm/K), 스테인리스 (16, 7900, 500, 17 ppm/K) (6행). T_amb = 20 ℃
  - head_sim 기본값: 히터 20×20×5 mm, 콜렛 10 mm 정육면체, MACOR 40×40×16 mm 를 16절점으로 분할, 재킷 20 ℃ 고정, h_nat = 10 W/m²K, ε = 0.3, P_max 400 W, dt 5 ms, PI Kp 40 W/K, Ki 8 W/(K·s), I 제한 ±50 (9-41행)
  - 결과 계산에 쓴 조건: Kp = 1e6, Ki = 0 (사실상 최대 전력 on/off) (43, 49, 51행). 냉각 제트 air_h = 400 W/m²K (49행)
  - 척: 110×110 mm, ΔT 180 K, 단열재 3종 (61-63행). 수냉판: 1 L/min, h 3000 W/m²K, A 0.006 m² (65-68행). 홀더 L = 20 mm (70행)
- **식:**
  - 팁 노드: C_tip·dT/dt = P − h·A(T−T_amb) − εσA(T⁴−T_amb⁴) − 2G(T − T_m,1)
  - MACOR 절점: C_m·dT_i/dt = G(T_{i−1} − T_i) − G(T_i − T_{i+1}). 양 끝 반 셀은 2G. G = kA/Δx, C_m = ρcAΔx
  - 명시적 오일러로 적분한다. t += dt 를 누적하고 0.1 s 마다 기록한다
  - 드리프트 = α_MACOR·20 mm·|dT̄_m/dt| (57행)
  - τ_MACOR = C_total/(2·kA/L) (59행)
  - 척 Q = kAΔT/t. 수냉판 상승 = Q/(ṁc_p)/2 + Q/(hA)
- **출력:** heater (t_to_400 = 17.2 s, 22.09 K/s, 유지 65.4 W, 재킷 55.5 W), cooling 45.1 s, 자연냉각 242.7 s, drift (대기 88 s, τ 174.5 s), chuck, coolplate, prism_holder → `thermal.json`

#### control_sim.py (10장)
- **하중 루프 force_sim (6-35행). 단위 mm·N·s.**
  - k_c = 2000 N/mm, k_eff = (1/k + 1/k_c)⁻¹
  - 서보: 1차 지연 τ = 0.8 ms. 측정: 0.5 ms 지연 + 노이즈 σ 0.002 N (rng 시드 3)
  - Kp = 2π·20/k_eff, Ki = (2π·20)(2π·2)/k_eff (40행)
  - 시퀀스: 접근 20 μm/s → 0.1 N 에서 접촉 판정 → 5 N/s 램프 → 유지
  - dt = 10 μs, 9 s 시뮬레이션
  - 케이스 (37-38행): 2 N/mm·1 N·1 ms / 50 N/mm·20 N·1 ms / 50 N/mm·20 N·10 ms / 50 N/mm·20 N·1 ms + 열팽창 2.6 μm/s
  - 허용 오차: 저 레인지 0.05 + 0.01F, 고 레인지 0.1 + 0.01F (41행)
- **하중 루프 식:**
  - 플랜트: ż_cmd = v, ż = (z_cmd − z)/τ, F = max(0, k_eff(z + therm·t))
  - 제어기 (Ts 마다): sp = min(F_t, 0.1 + ramp·(t − t_c)), e = sp − F_m, I += e·Ts, v = Kp·e + Ki·I
  - 적분 제한과 anti-windup 은 없다
- **온도 루프 temp_sim (45-64행):**
  - C = 8.77 J/K, MACOR 3절점, 손실 면적 A = 0.0011 m², h = 10, ε = 0.3
  - 열전대 1차 지연 5 ms, 노이즈 σ 0.2 ℃ (상수로 박혀 있음, 54행)
  - PI: Kp 25 W/K, Ki 6 W/(K·s), I 를 ±30 으로 제한하고, 출력이 포화되면 이번 적분을 되돌린다. P ∈ [0, 400] W
  - dt 1 ms, 프로파일 150 ℃ → 40 s 부터 20 K/s → 300 ℃ (65행)
- **출력:** force 4케이스의 overshoot·ss_err·pass, temperature 2케이스의 overshoot·안정도·램프·유지 전력 → `control.json`
- 78행의 그림 데이터 `CT` 는 contact_speed_study 결과를 숫자로 옮겨 적은 것이다

#### contact_speed_study.py (10장)
- control_sim.py 를 `'cases={}'` 앞까지 exec 해서 force_sim 을 가져온다 (2행)
- 조건: k = 50 N/mm, F = 5 N, Ts ∈ {1, 10} ms, 접근 속도 ∈ {0.02, 0.2, 0.5} mm/s, t_end = 4 s
- 지표: 접촉 후 0.3 s 동안 max(F − sp)
- 결과는 표준출력으로만 나온다. 0.002 / 0.010 / 0.035 / 0.052 / 0.088 / 0.131 N 으로 보고서 10장 표와 같다

#### vision.py, vision_robust.py (9장)
- **입력:**
  - 1.725 μm/px (5행)
  - 십자 마크: 팔 60 px, 선폭 6 px, 밝기 220/30, 블러 σ 1 px, N = 128 (7행)
  - 템플릿 = render(0, 0, N = 80) (19행)
  - 노이즈 σ ∈ {1, 2, 4, 8} 계조, 1·4 프레임, 10 bit 양자화 (30-33행), 시드 7
  - 아핀 참값: 회전 0.3°, 배율 오차 0.2 %, 기울어짐 0.0005, b = (12, −7) μm. 5×5 격자 ±1500×±1200 μm, 픽셀 노이즈 0.03 (61-66행)
  - 폐루프: 초기 오차 ±30 μm, ±0.3°. 판정 |Δ| ≤ 0.15 μm, |Δθ| ≤ 0.002°, 최대 3회. 매핑 오차 5e-4, 스테이지 σ 0.02 μm (78-86행)
  - 각도: 마크 간격 L = 4000 μm (95행)
- **식:**
  - 픽셀 면적 피복률 (10-15행)
  - NCC: cv2 의 TM_CCOEFF_NORMED (22행)
  - 3점 보간 δ = ½(a−c)/(a−2b+c). 가우시안 방식은 세 값에 ln 을 먼저 취한다 (24-26행)
  - 아핀: 최소제곱 s = A·p + b (67행)
  - 각도 σ: 4 마크는 √2·s/L, 2 마크는 2s/L (96행)
- **출력:** detection 16행, pixel_locking, affine, closed_loop, angle → `vision.json`. vision_robust 는 6케이스 → `vision_robust.json`
- vision_robust.py 14행: "평탄화 보정" 을 grad = 0(완전 제거)으로 넣었다

#### error_budget.py, integration.py (5·12장)
- 9개 항목 (정규 σ 또는 균일 반폭, μm). error_budget.py 7-17행, integration.py 7-17행 (예산·대표·보수 세 열)
- 식: σ = p (정규), p/√3 (균일). RSS = √Σσ². MC 100만 회, 시드 1·2
- 결과 (3σ RSS): 예산 0.882 μm, 대표 0.689 μm, 보수 0.903 μm

#### drive_calc.py (6장)
- **입력 (27-32행):**
  - Y: 6 kg, 리드 5 mm, d 12 mm, L 250 mm, η 0.9, 1 m/s², 50 mm/s, μ 0.005
  - X: 10 kg, L 350 mm, 나머지는 Y 와 같음
  - Z: 2.5 kg, 리드 2 mm, L 150 mm, 0.5 m/s², 20 mm/s, 수직, F_ext 100 N
  - 모터 Jm 3e-6 kg·m²
  - 판스프링 E 200 GPa, b 20 mm, L 25 mm (46행)
- **식:**
  - T = F·l/(2πη), T_acc = (J_s + J_m)·2πa/l
  - 위험속도, 좌굴 P = η₂·d_r⁴/L²·10⁴
  - 판스프링 t = (kL³/(4Eb))^(1/3), σ = 3Etδ/L²
- **출력:** `drive_calc.json`. 사이클 시간 모델이 쓸 축 속도와 가속도가 여기에 있다

#### fea_struct.py (8장, 시뮬레이션 대상 아님)
- 복셀 hex8 FEM. 인자는 h [mm], static/modal, v1~v5, 편심 [mm]
- E·ρ: Al, steel, MACOR, AlN (6행). ν = 0.3 (76행)
- 하중: 콜렛 +50 N, 척 −50 N (94행)
- 브라우저 시뮬레이션에서는 다시 쓰지 않는다. 결과값(예: 강성 157.5 N/μm, 1차 고유진동수 177 Hz)만 상수로 가져다 쓸 수 있다

---

## 2. 시뮬레이션 모델별 재사용 맵

`ref:` 는 reference_models.py 의 함수, `원본:` 은 원본 줄 번호다.

### A. 층별 열 이력 (1D 집중정수, 7장) → `sim/thermal.js`

| 재사용 | 내용 | 근거 |
|---|---|---|
| 헤드 모델 골격 | 팁 1절점 + MACOR n절점 + 재킷 고정온도. 대류·복사 손실, 명시적 오일러 | ref: `head_sim`, 원본: thermal.py:9-41 |
| 물성·형상 | AlN, MACOR, 스테인리스 물성, 히터 20×20×5 mm, C_tip 8.77 J/K, P_max 400 W | thermal.py:6, 10-16 |
| 손실·냉각 | h_nat 10, ε 0.3, 제트 h 400 W/m²K. 400→100 ℃ 냉각 45.1 s (제트) / 242.7 s (자연) | thermal.py:17, 29, 49 |
| 승온 능력 | 20→400 ℃ 17.2 s (평균 22.1 K/s), 유지 65 W | thermal.json heater |
| 척 정상상태 | Q = kAΔT/t, 규산칼슘 10 mm → 26 W. 척 최고 200 ℃ | ref: `conduction_Q_W`, thermal.py:61-63 |
| 드리프트 | α·L·dT/dt, 대기 88 s | ref: `macor_drift_metrics`, thermal.py:54-59 |
| 경화도 적분 | k(T) 아레니우스. 시간에 따라 변하는 T 에 대해 dα/dt = k(T(t))(1−α) 로 적분하면 된다 | ref: `cure_rate_1_s`, process_physics.py:43 |
| 솔더 녹는점 기준 | SnAgCu 약 217 ℃ (강의 인용) | 04:157 |

**적층에 필요한데 없는 것 (gap)**
- 다이·접합층·기판 노드가 없다. 지금 모델은 툴 팁에서 끝난다.
  - 필요한 식: N층 1D 사슬. 노드 = [툴 팁 | 다이_N | 접합층_N | … | 다이_1 | 접합층_1 | 베이스 | 척]
  - C_i·dT_i/dt = Σ G_ij(T_j − T_i), C_i = ρ_i·c_i·A·t_i, G = (t_i/(2k_iA) + R_c + t_j/(2k_jA))⁻¹
  - 척 쪽은 척 온도를 경계로 두거나 척 노드를 추가한다
  - 조사 필요: Si·NCF·MUF·솔더·베이스 다이의 k·ρ·c, 층 두께, 다이 크기, TSV 유효 열전도, 툴–다이와 층간 접촉 열저항
- 적분 안정성: 얇은 층은 C/G 가 작아 명시적 오일러의 dt 한계가 5 ms 보다 훨씬 작아진다. 적층 모델은 후진 오일러(3중 대각 행렬, Thomas 알고리즘)를 쓰는 것을 권장한다. 헤드 단독 모델은 golden 재현을 위해 명시적 오일러를 그대로 둔다.
- TC-NCF 재가열 횟수: 층 i 가 본딩된 뒤 위층 본딩 N−i 회 동안 받는 최고 온도, 액상선 위에 머문 시간, 경화도 증가량을 기록하는 로직이 필요하다 (새로 작성).
- MR-MUF 질량 리플로우: 오븐 프로파일 T_oven(t) 와 대류 경계 h_oven 이 필요하다. 조사 필요: 예열·피크·액상선 위 유지 시간, h_oven. 순간 가열 tack 펄스의 온도와 시간도 조사 필요 (head_sim 의 ramp/T_set 으로 표현할 수 있다).
- 열 모델이 두 벌이다: thermal.py (MACOR 16절점, A_rad 0.0017 m²) 와 control_sim.py (3절점, A 0.0011 m²). 한 모듈로 합치고 절점 수와 손실 면적을 인자로 둔다 (6절 3번).

### B. 하중·온도 PI 응답 (10장, 이후 C 펌웨어) → `sim/control.js` + `firmware/`

| 재사용 | 내용 | 근거 |
|---|---|---|
| 하중 제어기 1주기 | 상태(mode, I, t_contact, sp, v_cmd). 접근 → 0.1 N 접촉 판정 → 램프 → 유지. v = Kp·e + Ki·I | ref: `force_ctrl_step`, control_sim.py:22-28 |
| 이득 | Kp = 2π·20/k_eff [(mm/s)/N], Ki = (2π·20)(2π·2)/k_eff. k_eff = (1/k + 1/2000)⁻¹ | ref: `force_gains`, control_sim.py:9-10, 40 |
| 하중 플랜트 | 서보 1차 지연 0.8 ms, ADC 지연 0.5 ms (버퍼), dt 10 μs | ref: `force_sim`, control_sim.py:6-35 |
| 판스프링 | 2 N/mm·50 N/mm, 두께·응력 식 | ref: `leaf_flexure`, drive_calc.py:45-50 |
| 온도 제어기 1주기 | PI, I 를 ±30 으로 제한, 포화 시 적분 되돌림, P 를 [0, 400] W 로 제한 | ref: `temp_ctrl_step`, control_sim.py:53-56 |
| 온도 플랜트 | C 8.77 J/K, MACOR 3절점, 열전대 5 ms 지연 | ref: `temp_sim`, control_sim.py:45-64 |
| 프로파일 | 150 ℃ → 20 K/s → 300 ℃ | ref: `tcncf_profile_C`, control_sim.py:65 |
| 안전 한계 | 소프트웨어 52 N·410 ℃, 하드웨어 55 N·420 ℃ | 13:122, 10장 회로 |
| 하중 상한 | 1 / 0.5 / 2 MPa, 50 N | ref: `force_limit_N`, education_calc.py:35-37 |

**gap**
- 하중 루프에 적분 제한과 anti-windup 이 없다 (control_sim.py:27). 펌웨어로 옮길 때 넣어야 한다. 그러면 원본과 결과가 달라지므로, golden 대조용 "원본 동작 모드" 와 펌웨어 모드를 나눈다.
- 층별 하중·온도 레시피가 없다. 필요한 형식: 층 i 마다 (F(t), T(t)) 구간 목록.
  - 조사 필요: TC-NCF 층당 본딩 하중, 온도, 유지 시간, 하중 유지 냉각 온도. MR-MUF tack 하중·온도·시간
  - 하중은 장비 한계 50 N·400 ℃ 와 비교해 확인해야 한다 (원문 KPI)
- NCF 와 하중 루프의 결합이 없다. 지금은 접촉 강성이 2000 N/mm 로 일정하다. NCF 를 넣으면 범프가 닿기 전까지 하중이 점성 저항 F = 3πμR⁴/(2h³)·(−dh/dt) 로 전달된다. 플랜트 하중을 ncf.js 의 h(t) 와 연결하는 식이 필요하다 (새로 작성).
- 헤드 열팽창 외란 2.6 μm/s 는 출처가 없다 (6절 4번). 열 모델에서 헤드 길이 변화 dL/dt = Σα_i·L_i·dT_i/dt 를 계산해 넘겨주는 식이 필요하다. 조사 필요: 헤드 각 부품의 길이.
- 펌웨어: 제어기 1주기 함수(`*_ctrl_step`)를 JS 와 C 에서 같은 구조체와 같은 연산 순서로 만든다. noise = 0 golden vector 로 Python·JS·C 세 구현을 대조할 수 있다.
  - 조사 필요: 고정소수점 여부, ADC 분해능 (ADS1256 24 bit, AD8495 5 mV/℃ 는 10장에 있다)

### C. 비전 정렬 + 자기 정렬 (9장, 4.9) → `sim/alignment.js`

| 재사용 | 내용 | 근거 |
|---|---|---|
| 합성 영상 | 면적 피복률 렌더, 블러 (커널 크기 round(8σ+1)\|1, reflect-101) | ref: `render_cross`, `gaussian_blur`, vision.py:7-18 |
| 검출 | NCC (TM_CCOEFF_NORMED 정의), 로그-포물선 3점 보간 | ref: `ncc_map`, `subpixel_peak`, `measure_cross`, vision.py:21-29 |
| 아핀 | 6계수 최소제곱 | ref: `affine_fit`, vision.py:67-74 |
| 폐루프 MC | ±30 μm, ±0.3°, 판정 0.15 μm·0.002°, 최대 3회 | ref: `align_once`, vision.py:78-86 |
| 통계값 (빠른 모드) | 채널당 σ 0.0148 μm (노이즈 2, 4프레임). 최종 3σ 0.091 μm. 반복 1회 99.1 % | vision.json |
| 각도 | √2·s/L | ref: `angle_sigma_deg`, vision.py:96 |
| 예산 합산 | 9개 항목 RSS. 예산 3σ 0.88, 대표 0.69, 보수 0.90 μm | ref: `rss_sigma`, error_budget.py, integration.py |
| 자기 정렬 (정성) | 리플로우하면 표면장력이 다이를 패드 중심으로 당긴다. TCB 는 자기 정렬이 거의 없다 | 04:161-163 (식 없음) |

**gap**
- 자기 정렬 복원력 모델이 전혀 없다. 4.9절은 정성 설명뿐이다.
  - 후보식: 직육면체 솔더 근사로 직접 유도했다. 문헌 확인 필요.
  - 조인트 하나의 횡강성 k_sa ≈ 2γw/h (정사각 패드 폭 w, 솔더 높이 h, 작은 변위). 전체 K = N_j·k_sa
  - 감쇠 c ≈ N_j·μ_s·w²/h (용융 솔더의 Couette 유동)
  - 운동식: m·ẍ + c·ẋ + K·x = −F_저항. 과감쇠라면 x(t) ≈ x₀·exp(−t·K/c)
  - 적분 시간 = 액상선 위 유지 시간 (열 모델 출력)
  - 부분 정렬은 F_저항 (tack 접착력, 마찰, 미경화 수지)으로 표현한다
  - 조사 필요: γ_solder, μ_solder, 패드 크기, 범프 수, 솔더 높이, 다이 질량, F_저항
- 적층 누적 오차가 없다.
  - 아래 다이에 맞춰 정렬하면 오차가 누적된다: σ_N = √N·σ_층
  - 기판 기준 마크에 맞춰 정렬하면 누적되지 않는다
  - 어느 기준을 쓰는지 정해야 한다 (조사 필요: HBM 적층에서 쓰는 정렬 기준)
- 본딩 중 미끄러짐(#8)은 원본에도 "모델 없음" 이다 (integration.py:15). TC-NCF 에서 필름 유동이 다이를 밀어내는 양을 넣을 식이 필요하다 (조사 필요).
- 휨으로 생기는 층간 횡변위 결합 (D 의 κ 에서 가장자리 기울기 κL/2 사용)은 새로 작성해야 한다.
- 브라우저 성능: NCC 49×49×6400 ≈ 1,500만 곱셈/프레임이다. 영상 모드는 화면 표시용으로 쓰고, MC 는 통계 모드(σ 값 사용)로 돌리는 두 단계를 권장한다.

### D. 휨 누적 (Timoshenko, 4.8) → `sim/warpage.js`

| 재사용 | 내용 | 근거 |
|---|---|---|
| 2층 곡률 | Timoshenko 식 | ref: `timoshenko_curvature_1_m`, process_physics.py:50-52 |
| 휨 높이 | w = κL²/8 | ref: `warp_sagitta_m`, process_physics.py:60 |
| 물성 | Si 130 GPa·2.6 ppm/K, FR-4 22 GPa·16 ppm/K, 유리 64 GPa·3.3 ppm/K | process_physics.py:53 |
| 측정 기준 | 레이저 스캔, 평면 맞춤 불확도 0.27 μm/10 mm (95 %) | education_calc.json parallel_meas |

**gap**
- 다층 식이 필요하다. 2층 Timoshenko 로는 N층 적층을 계산할 수 없다.
  - 필요한 식: 고전 적층판 이론 (각 층 E_i, α_i, z 구간 [z_b, z_t])
  - A = ΣE_i·t_i, B = ΣE_i(z_t² − z_b²)/2, D = ΣE_i(z_t³ − z_b³)/3
  - N_T = ΣE_i·α_i·ΔT·t_i, M_T = ΣE_i·α_i·ΔT(z_t² − z_b²)/2
  - 연립식 [A B; B D]·[ε₀; κ] = [N_T; M_T]
  - 2층이면 Timoshenko 와 크기가 같다 (0절에서 확인, 부호 규약만 반대). 판의 이축 변형을 보려면 E 대신 E/(1−ν) 를 쓴다
- 층별 무응력 온도:
  - TC-NCF: 층 i 는 본딩 온도에서 고정되고 그 뒤 재가열을 N−i 회 받는다
  - MR-MUF: 리플로우 한 번 + MUF 경화 온도에서 고정된다
  - 층마다 다른 ΔT_i 를 넣을 수 있도록 N_T, M_T 의 ΔT 를 층별 값으로 바꾼다
  - 순차 적층은 단계마다 층을 하나 추가하고 증분 ΔT 를 중첩해 계산한다 (새로 작성)
- 조사 필요:
  - NCF, MUF(EMC)의 E, α (Tg 위아래), Tg, 경화 수축률
  - 층 두께, 베이스 다이·인터포저·기판 물성
  - 재가열 중 점탄성 완화 여부
  - ν: fea_struct 는 모든 재료에 0.3 을 썼다 (76행). 적층 재료값은 조사 필요
- 휨 합격 기준값: 조사 필요

### E. NCF 스퀴즈 유동 (4.3) → `sim/ncf.js`

| 재사용 | 내용 | 근거 |
|---|---|---|
| Stefan 닫힌 해 | 1/h² = 1/h₀² + 4Ft/(3πμR⁴), R = a/√π | ref: `squeeze_blt_m`, `squeeze_time_to_m`, process_physics.py:13-19 |
| 미분형 | dh/dt = −2Fh³/(3πμR⁴). 하중이 변하거나 점도가 변할 때 적분한다 | ref: `squeeze_dhdt_m_s`, process_physics.py:8 주석 |
| 경화 | 1차 아레니우스 (기준점을 바꿀 수 있게 인자화했다) | ref: `cure_rate_1_s`, `cure_conversion`, process_physics.py:42-46 |
| 체적 보존 | 밀려 나온 양 → 필렛 | ref: `fillet_height_mm`, process_physics.py:33-35 |
| 기울기 | 평행도 → 두께 차이 | ref: `tilt_blt_diff_um`, process_physics.py:64 |
| 하중 상한 | TCB 2 MPa | ref: `force_limit_N` |

**gap**
- 점도 μ(T, α):
  - 원본은 μ = 20 Pa·s 상수이고, 온도와 무관하다 (education_calc.py:20 의 DoE 도 마찬가지)
  - 필요한 식 (형태만 제시): μ = μ₀·exp(E_μ/RT)·(α_g/(α_g − α))^(A + Bα), 겔화점 α_g 에서 유동이 멈춘다
  - 조사 필요: μ₀, E_μ, α_g, A, B 등 모든 계수
- 필름 초기 두께와 최종 간격:
  - h₀ 는 NCF 두께다 (조사 필요)
  - 최종 간격은 필러 한계 h_min 대신 범프 스탠드오프 h_bump 로 둔다 (조사 필요: 범프 높이, 솔더 캡 두께)
- 범프가 닿은 뒤의 하중 분담: F = F_film + F_bumps(δ). 범프 수와 범프 변형 강성은 조사 필요
- 비뉴턴 유동: 멱법칙 Stefan 식으로 확장할지 결정해야 한다. 식의 출처는 문헌 확인 필요
- 갇힌 보이드: 원본에 모델이 없다 (4.6 은 정성 설명).
  - 최소안: 보이드율을 사용자 입력으로 두고, 승온 속도·점도에 따른 경향을 규칙으로 표현한다
  - 정량 모델은 조사 필요
- NCF 면적과 다이 면적의 비, 밀려 나온 필름의 필렛 모양: 조사 필요
- 경화 기준점: 원본의 180 ℃·30 min·95 % 는 에폭시 접착제 값이다. NCF 값은 조사 필요
- 재가열 때마다 경화도가 더 오르는 것을 반영하려면 A(열 이력)와 결합해야 한다

### F. MUF 모세관 충전 (Washburn, 13장) → `sim/muf.js`

| 재사용 | 내용 | 근거 |
|---|---|---|
| 충전 시간 | t = 3μL²/(γ·h·cosθ) | ref: `washburn_fill_time_s`, education_calc.py:25-31 |
| 선단 위치 | L(t) = √(γ·h·cosθ·t/(3μ)) (위 식의 역) | ref: `washburn_front_m` |
| 경화 | 1차 아레니우스 형태 | ref: `cure_rate_1_s` |
| 관찰 방법 | 유리 기판 + 하부 카메라 | 13:27 |

**gap**
- 원본 값(γ 0.03 N/m, θ 40°, μ 0.8/0.1 Pa·s)은 언더필 가정값이다 (13:27). MUF 의 μ(T), γ, θ 는 조사 필요
- 간격 h: 리플로우 후 스탠드오프 (조사 필요). 휨이 있으면 h(x) 가 위치에 따라 달라지므로 D 와 결합한다
- 범프 배열의 유동 저항: 원본은 빈 평행판이다. 유효 간격이나 투과율로 보정하는 식이 필요하다 (조사 필요: 범프 피치·지름)
- 여러 간격 동시 충전: N−1 개(또는 N 개) 간격을 측면에서 채운다. 충전 완료 시간 = max_i t_i. 간격마다 h_i 와 μ_i(T_i) 가 다를 수 있다 (새로 작성)
- 가압 충전 (몰딩형 MUF 를 표현할 때): L·dL/dt = h²(ΔP_cap + ΔP_app)/(12μ), ΔP_cap = 2γcosθ/h. ΔP_app = 0 이면 원본 Washburn 식과 같다. 이 경우 t = 6μL²/(h²(ΔP_cap + ΔP_app)). 조사 필요: ΔP_app
- 충전 중 경화로 점도가 오르는 효과 (μ(T, α)): 조사 필요
- 유동 선단이 합쳐지며 생기는 보이드, 가장자리로 먼저 흐르는 현상(race-tracking): 정량 모델은 조사 필요
- MUF 경화 후 휨: D 의 다층 모델에 EMC 층을 추가한다

### G. 사이클 시간 (새로 작성) → `sim/cycle.js`

| 가져다 쓸 값 | 값 | 근거 |
|---|---|---|
| 접촉 전 접근 속도 | 20 μm/s (1 ms 루프면 500 μm/s 까지 가능) | 10:13, 10:49 |
| 접촉 판정, 하중 램프 | 0.1 N, 5 N/s | control_sim.py:24, 26 |
| 승온 | 20→400 ℃ 17.2 s (평균 22 K/s). 프로파일 램프 20 K/s | thermal.json, control_sim.py:65 |
| 냉각 | 400→100 ℃: 제트 45.1 s, 자연 242.7 s | thermal.json |
| 첫 본딩 대기 | 설정 온도 도달 후 88 s (운전 규칙 90 s) | thermal.json drift, 07:68 |
| 정렬 반복 | 1회 99.1 %, 2회 0.8 %, 3회 0.1 % (4프레임 평균) | vision.json closed_loop |
| XY 축 | 50 mm/s, 1 m/s² | drive_calc.py:27-28 |
| Z 축 | 20 mm/s, 0.5 m/s² | drive_calc.py:30 |
| 경화 시간 | t = −ln(1−α)/k(T) | ref: `cure_time_to_s` |
| 에폭시 1회 본딩 | 정렬·가압·확인 약 3분 (추정) | 13:38 |

**새 식**
- 사다리꼴 이동 시간:
  - d ≥ v²/a 이면 t = d/v + v/a
  - 그렇지 않으면 t = 2√(d/a)
- TC-NCF 적층 시간: T = Σ_{i=1..N} [t_pick + t_xy + n_iter·t_frame + t_z(d_z) + d_gap/v_approach + t_ramp(T_idle → T_bond) + t_hold + t_cool(T_bond → T_release)]
- MR-MUF 적층 시간: T = Σ_{i=1..N} [t_pick + t_xy + n_iter·t_frame + t_z + d_gap/v_approach + t_tack] + t_reflow + t_dispense + t_fill(F) + t_cure
- t_ramp 와 t_cool 은 A(head_sim)에서 직접 계산하거나, 처음에는 위 값으로 근사한다

**조사 필요:** 픽업·진공 시간, 카메라 노출·전송 시간, Z 이동 거리, 층당 유지 시간, 하중 유지 냉각 목표 온도, tack 조건, 리플로우 프로파일 길이, MUF 디스펜스·경화 조건

---

## 3. gap 목록 (요약)

| # | 모델 | 없는 것 | 필요한 식·파라미터 | 값 |
|---|---|---|---|---|
| G1 | thermal | 층별 열 경로 (다이·접합층·베이스·척) | N층 1D 사슬 C_i·dT_i/dt = ΣG_ij(T_j − T_i), 후진 오일러 | 조사 필요: Si·NCF·MUF·솔더 k, ρ, c, 두께, 접촉 열저항 |
| G2 | thermal | 재가열 이력 기록 | 층별 최고 온도, 액상선 위 유지 시간, Δα | 액상선 217 ℃ 는 강의 인용. 나머지는 조사 필요 |
| G3 | thermal | 질량 리플로우·tack 펄스 | T_oven(t), h_oven, tack 프로파일 | 조사 필요 |
| G4 | control | 하중 루프 적분 제한·anti-windup | I 제한, 포화 시 적분 되돌림 (온도 루프와 같은 방식) | 설계값 |
| G5 | control | 층별 레시피, NCF–하중 결합 | 구간 레시피 (F(t), T(t)), 플랜트에 F_film(h, ḣ) 연결 | 조사 필요: 층당 하중·온도·시간 |
| G6 | control | 헤드 열팽창 외란의 출처 | dL/dt = Σα_i·L_i·dT_i/dt | 조사 필요: 부품 길이. 2.6 μm/s 는 출처 없음 |
| G7 | alignment | 자기 정렬 복원력 | k_sa ≈ 2γw/h (후보, 문헌 확인 필요), c ≈ μ_s·w²/h, m·ẍ + c·ẋ + Kx = −F_저항 | 조사 필요: γ, μ_s, 패드, 범프 수, 높이, F_저항 |
| G8 | alignment | 적층 누적 오차, 본딩 중 미끄러짐 | 정렬 기준에 따라 σ_N = √N·σ 또는 σ_N = σ, 미끄러짐 항 | 조사 필요 |
| G9 | warpage | 다층·층별 무응력 온도 | 고전 적층판 [A B; B D]·[ε₀; κ] = [N_T; M_T], 층별 ΔT_i | 조사 필요: NCF·EMC 의 E, α, Tg, 수축, ν |
| G10 | ncf | 점도 μ(T, α), 필름 두께, 범프 스탠드오프 | μ(T, α) 형태식, h_final = h_bump, F = F_film + F_bump | 조사 필요 (모든 계수) |
| G11 | ncf | 보이드 갇힘 | 사용자 입력 또는 경향 규칙 (정량 모델은 조사 필요) | 조사 필요 |
| G12 | muf | MUF 물성, 범프 배열 저항, 다중 간격 | Washburn + 유효 간격 보정, max_i t_i, 가압 항 ΔP_app | 조사 필요: μ(T), γ, θ, 간격, 피치 |
| G13 | cycle | 모듈 전체 | 사다리꼴 이동, 단계 합산식 (2절 G) | 조사 필요: 픽업, 노출, tack, 리플로우, 경화 |
| G14 | 공통 | 난수 | numpy 난수열은 JS 로 재현할 수 없다. 시드 고정 PRNG (예: xoshiro128 + Box–Muller) 를 쓰고, MC 결과는 통계(평균·σ·백분위)로 대조한다 | — |

---

## 4. 권장 JS 모듈 구성과 함수 시그니처

모든 함수는 순수 함수로 만든다. 단위는 인자 이름에 붙인다. 상태가 있는 시뮬레이션은 `step(state, input, params) → state` 형태로 쓴다.

```js
// sim/thermal.js
export function heaterTipCapacity(heaterMm = [20,20,5], colletMm = [10,10,10]) // -> J/K
export function headSim({heater, P_max, T_set, t_end, dt, cool_at, air_h, Kp, Ki, ramp, n_macor}) // -> {t[],T[],Tm[],P[],Qj[],C_tip,G_mac}
export function headHeatupMetrics(r, {thr = 399, target = 400}) // -> {t_to_400_s, avg_ramp_K_per_s, P_hold_400_W, Q_jacket_steady_W}
export function headCoolingTime(r, cool_at, T_end = 100)       // -> s | null
export function macorDriftMetrics(r, t400, {lim_K_s, alpha, L_m, waits})
export function conductionQ(k_W_mK, A_m2, t_m, dT_K)
export function coolplateRise(Q_W, {flow_L_min, h_W_m2K, A_m2, cp})
export function thermalOffsetUmPerK(alpha_1_K, L_m = 0.020)
export function gradientNonUniform(y, x)                        // numpy.gradient 와 같은 규칙 (드리프트 계산용)
// 새로 작성 (G1-G3)
export function buildStack({layers, toolContact_R, chuck})      // -> {C[], G[]}
export function stackStep(state, {P_W, T_chuck_C, h_conv, T_amb_C}, model, dt) // 후진 오일러
export function stackSim(model, schedule /* 층별 구간 레시피 */) // -> 층별 T(t), 최고 온도, 액상선 위 시간
export function cureStep(alpha, T_C, dt_s, cureParams)          // dα = k(T)(1-α)dt

// sim/control.js  (firmware/force_pi.c, firmware/temp_pi.c 와 같은 구조체, 같은 연산 순서)
export function kEff(k_spring_N_mm, k_c_N_mm = 2000)
export function forceGains(k_spring_N_mm, f_c_Hz = 20, f_i_Hz = 2)     // -> {Kp, Ki}
export function forceCtrlStep(st, Fmeas_N, t_s, {F_target, ramp, Kp, Ki, Ts, approach, F_contact}) // -> st
export function forceSim(opts /* force_sim 인자 + rng|null */)        // -> {t[],F[],sp[],t_contact,overshoot,ss_err}
export function contactPeak(r, window_s = 0.3)
export function tempCtrlStep(st, Tmeas_C, sp_C, {Ts, Kp, Ki, Kd, P_max, I_lim}) // -> st
export function tempSim(opts)                                          // -> {t[],T[],sp[],P[]}
export function tempMetrics(t, T, P)
export function tcncfProfile(t_s)
// 새로 작성 (G4-G6)
export function forceCtrlStepFw(st, Fmeas_N, t_s, p)    // I 제한·anti-windup 포함 (펌웨어 모드)
export function recipeSetpoint(recipe, layerIdx, t_s)  // -> {F_sp, T_sp}

// sim/ncf.js
export function squeezeBlt(F_N, a_mm, t_s, {mu, h0, hmin})
export function squeezeTimeTo(hT_m, F_N, a_mm, {mu, h0})
export function squeezeDhdt(h_m, F_N, a_mm, mu_Pa_s)
export function squeezeIntegrate({F_of_t, mu_of_t, a_mm, h0_m, h_stop_m, dt_s, t_end_s}) // 새로 작성: RK4, -> h(t)
export function cureRate(T_C, Ea_J_mol, {Tref_C, tref_s, alpha_ref})
export function cureTimeTo(alpha, T_C, Ea_J_mol, p)
export function cureConversion(t_s, T_C, Ea_J_mol, p)
export function filletHeight(V_mm3, a_mm, blt_um)       // -> {h_f_mm, V_f_mm3}
export function tiltBltDiff(die_mm, parallel_um_per_10mm = 2)
export function forceLimit(a_mm, mode)
export function ncfViscosity(T_C, alpha, params)        // 새로 작성, 계수 조사 필요 (G10)

// sim/muf.js
export function washburnFillTime(mu_Pa_s, L_m, gap_m, {gamma, theta_deg})
export function washburnFront(mu_Pa_s, t_s, gap_m, {gamma, theta_deg})
export function pressureFillTime(mu_Pa_s, L_m, gap_m, {gamma, theta_deg, dP_app_Pa}) // 새로 작성
export function stackFillTime(gaps /* [{h_m, mu_Pa_s, L_m}] */, opts)               // 새로 작성, max_i

// sim/warpage.js
export function timoshenkoCurvature(h1_m, E1_Pa, a1, h2_m, E2_Pa, a2, dT_K)
export function warpSagitta(kappa_1_m, L_m)
export function laminateCurvature(layers /* [{t_m, E_Pa, alpha, dT_K}] 아래→위 */)    // 새로 작성 -> {eps0, kappa}
export function stackWarpHistory(steps /* 층 추가·온도 이력 */)                       // 새로 작성

// sim/alignment.js
export function renderCross(dx, dy, {N, arm, w, blur, bright, dark})  // Float64Array N*N
export function gaussianKernel(sigma); export function gaussianBlur(img, N, sigma)
export function nccMap(img, imgN, tpl, tplN)
export function subpixelPeak(a, b, c, method = 'gauss')
export function measureCross(img, N, {method, tpl})   // -> {cx, cy}
export function affineFit(P_px, S_um)                 // -> {A, b, rot_deg, scale_um_px}
export function angleSigmaDeg(s_um, L_um = 4000, n_marks = 4)
export function alignOnce(rng, sig_ch_um, opts)       // -> {d_um:[x,y], theta_rad, iters}
export function sigmaOf(dist, p); export function rssSigma(terms)
export function selfAlign({x0_um, K_N_m, c_Ns_m, m_kg, F_resist_N, t_liquid_s}) // 새로 작성 (G7)
export function stackOffset({N, sigma_layer_um, reference: 'substrate'|'previous'}) // 새로 작성 (G8)

// sim/cycle.js  (모두 새로 작성)
export function trapezoidMoveTime(d_mm, v_mm_s, a_mm_s2)
export function bondStepTimes(mode /* 'TC-NCF'|'MR-MUF' */, recipe, machine)
export function stackCycleTime(mode, N, recipe, machine)   // -> {total_s, breakdown}

// sim/rng.js
export function makeRng(seed)  // {uniform(a,b), normal(mu,sigma)}. numpy 와 수열이 다르다
```

**golden 대조 규칙**
- JS 테스트는 `golden_vectors.json` 의 각 항목에 대해 `|js − ref| ≤ abs + rel·|ref|` 를 확인한다.
- 시간 적분 모델 (`headSim`, `forceSim`, `tempSim`)은 원본과 같은 순서로 계산하면 1e-9 안에서 맞는다.
  - `t += dt` 누적
  - 기록 판정 `Math.round(t/dt) % Math.trunc(0.1/dt) === 0`
  - `T += dt*(P − q_loss − q)/C` 처럼 곱셈을 먼저 하는 순서
  - 배열 갱신은 `q[0..n-2] −= fl` 를 먼저 하고 `q[1..n-1] += fl` 를 나중에 한다
  - 하중 지연 버퍼는 길이 50 FIFO 로, 넣은 다음 꺼낸다
- 경계 판정은 원본을 따른다.
  - 승온 도달은 399 ℃ 넘는 첫 기록 시점이다
  - 냉각 시간은 cool_at 이후 기록 중 100 ℃ 이하인 첫 점이다
  - `np.interp` 는 선형 보간이다. `np.polyfit(…,1)` 은 최소제곱 직선이다
- 비전 측정 항목의 허용오차는 abs 2e-4 px 다.

---

## 5. 시뮬레이션에 바로 넣을 수 있는 상수 (원본 결과값)

| 상수 | 값 | 출처 |
|---|---|---|
| 툴 팁 열용량 | 8.7748 J/K | thermal.json |
| MACOR 전체 열전도 G | 0.146 W/K, τ 174.5 s | thermal.json |
| 400 ℃ 유지 전력 / 재킷 열류 | 65.4 W / 55.5 W | thermal.json |
| 프레임 강성 (v5, 정적 h=5) | Kz 157.5 N/μm | fea_struct 재실행 결과 |
| 1차 고유진동수 (v5, 모달 h=10) | 177 Hz | fea_summary.json, 재실행 결과 |
| 정렬 3σ (대표) | 0.69 μm, 채널당 σ 0.0148 μm | integration.json, vision.json |

---

## 6. 코드와 보고서의 불일치, 주의할 점

1. **thermal.py 주석이 코드와 다르다.**
   - 42행 주석은 "250 W", 코드는 P_max = 400 W 다
   - 48행 주석은 "h=150", 코드는 air_h = 400 이다
   - 결과와 보고서는 코드 값(400 W, 400 W/m²K)을 따른다
2. **7장 제어 방식 설명이 결과와 다르다.**
   - 07:25 는 "도달 후에는 PI 제어로 유지" 라고 한다
   - 그러나 thermal.json 의 모든 결과는 Kp = 1e6, Ki = 0 (사실상 on/off) 으로 계산됐다 (thermal.py:43, 49, 51)
   - 유지 전력 65 W 도 이 조건의 값이다. PI 기본 이득(40/8)으로 계산한 결과는 없다
3. **10장이 "7장 모델을 그대로 썼다" 고 하지만 (10:55) 같은 모델이 아니다.**
   - control_sim.py 의 temp_sim 은 MACOR 3절점, 손실 면적 A = 0.0011 m², C = 8.77 J/K 다
   - thermal.py 는 16절점, A_rad = 0.0017 m², C = 8.7748 J/K 다
   - control_sim.py:46 의 `Gm` 은 쓰이지 않는다
   - JS 에서는 하나의 열 모듈에 절점 수와 손실 면적을 인자로 두고, 두 원본 설정을 프리셋으로 제공한다
4. **헤드 열팽창 2.6 μm/s 는 출처가 없다.**
   - 10:51 은 "7장에서 … 2.6 μm/s 로 늘어난다는 결과" 라고 쓴다
   - thermal.py 와 7장 본문 어디에도 이 계산과 값이 없다
   - control_sim.py:38 에 상수 `2.6e-3` 로만 들어 있다 (G6)
5. **control.json 은 스크립트 출력과 다르다.**
   - `contact_transient_N` 키를 control_sim.py 가 만들지 않는다. contact_speed_study.py 의 표준출력을 손으로 넣은 것으로 보인다
   - control_sim.py:78 의 그림 값도 숫자를 직접 적어 넣었다
   - 다시 실행하면 이 키가 사라진다
6. **fea_summary.json 을 만드는 스크립트가 없다.**
   - fea_struct.py 는 케이스마다 별도 JSON 을 쓴다 (117행)
   - h=10 정적 해석은 하중 면(z = 175 mm)에 절점이 없어 0으로 나누기 오류가 난다 (93-94행)
   - fea_grid.json 의 `xs0=-260` (104행)은 실제 격자 원점 −300 (43행)과 다르다
7. **스크립트마다 실행 폴더가 다르다** (1절 경로 문제). 원본만으로는 한 위치에서 전체를 다시 실행할 수 없다.
8. **쓰이지 않는 코드**
   - process_physics.py:29-31 `fillet_h` (주석의 nl·mm³ 단위 설명이 혼동되어 있다)
   - education_calc.py:3 `importlib` spec
   - integration.py:29-30 `T8` (민감도 분석을 하다 만 코드)
9. **4.4절 도포량 범위 표기가 JSON 과 다르다.**
   - 04:69 는 "±13 % (중앙값 기준)" 이다. 이것은 (0.85 − 0.661)/2 ÷ 0.755 = 12.5 % 다
   - JSON 의 `V_window_pct` = 28.6 은 (hi − lo)/lo 다. 정의가 다르므로 UI 에 표시할 때 어느 정의인지 밝힌다
   - 04:71 의 "0.62 mm³" 는 필렛 0 % 경계(a²·BLT = 0.625)로, 표의 0.66 (필렛 20 %)과는 다른 값이다
10. **DoE 의 BLT 는 온도와 무관하다** (education_calc.py:20). μ 가 150 ℃ 와 180 ℃ 에서 같고 경화와 연결되지 않아 T 는 휨에만 영향을 준다. NCF 모델에서는 이 결합(G10)이 핵심이다.
11. **평탄화 보정이 이상적으로 모델링됐다.** 09:23 의 방법은 기준 영상으로 나누는 것이다. vision_robust.py:14 는 조명 기울기를 완전히 없앤 경우(grad = 0)로 계산했다. 0.031 px 는 낙관적인 값이다.
12. **Timoshenko 부호.** 코드는 ΔT = T_cure − 25 (양수)를 넣어 휨 크기만 구한다. 다층 식으로 옮기면 냉각 ΔT 는 음수이고 부호 규약이 반대다 (0절에서 확인).
13. **13장 시간 계산:** 13:38 "24회 × 약 3분 → 약 1시간 20분". 계산값은 72분이다. 차이는 작다.
14. **하중 루프 지표의 기록 간격.** overshoot 와 ss_err 는 1 ms 마다 기록한 F_true 로 계산한다 (control_sim.py:31). 더 촘촘한 첨두값은 놓칠 수 있다. JS 도 같은 간격으로 계산해야 golden 과 맞는다.
15. **노이즈가 들어간 결과는 JS 에서 그대로 재현할 수 없다.**
    - control.json 의 하중·온도 결과와 vision.json 의 MC 결과는 numpy 난수열에 따라 정해진다
    - golden vector 는 noise = 0 조건으로 만들었다 (원본 코드에 0 노이즈 난수 생성기를 끼워 같은 값임을 확인했다)
    - 노이즈가 있는 결과는 원본 값을 통계 기준(예: 하중 overshoot 0.032~0.059 N, 온도 ±0.30~0.49 ℃)으로 비교한다

---

## 7. 파일 목록 (저장소 위치)

| 경로 | 내용 |
|---|---|
| `docs/model_inventory.md` | 이 문서 |
| `sim/test/golden_vectors.json` | golden vector 111개 (id, model, function, source, inputs{value,unit}, output{value,unit}, tolerance) |
| `calc/reference/reference_models.py` | 참조 구현. `python3 -I calc/reference/reference_models.py sim/test/golden_vectors.json` 으로 다시 생성, `--verify-json calc/midterm` 으로 원본 JSON 재현 확인 |

원본 그대로 실행한 복사본과 실행 로그, golden 을 원본 코드로 다시 계산해 대조한 보조 스크립트는 Chat 작업 환경에만 있고 저장소에는 넣지 않았다. 검증 결과는 0절에 정리했다.
