"""MSE489 중간 프로젝트 계산 모델의 참조 구현 (JS 포팅 검증용).

- 원본: 중간보고서/02_설계보고서_작업/calc/*.py (읽기 전용으로 두고, 식만 옮겨 왔다)
- 그림 그리기, 파일 입출력, 전역 난수 상태를 모두 뺀 순수 함수만 둔다.
- 각 함수 docstring의 [원본] 표시는 원본 파일과 줄 번호다.
- `python3 -I reference_models.py [출력경로]` 를 실행하면 golden_vectors.json 을 다시 만든다.
- `python3 -I reference_models.py --verify-json <원본 calc 폴더>` 는 이 파일의 함수로
  원본 결과 JSON(thermal, process_physics, education_calc, control 일부)을 재현하는지 확인한다.

단위 규칙: 함수 인자 이름 끝에 단위를 붙였다 (_m, _mm, _um, _s, _N, _C, _K, _Pa_s ...).
원본과 같은 단위계를 유지했다 (원본이 mm·N·s를 쓰는 하중 루프는 그대로 mm·N·s).
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

# =====================================================================
# 1. 공정 물리 (process_physics.py, education_calc.py)
# =====================================================================
EPOXY_MU_PA_S = 20.0      # [원본] process_physics.py:10  (가정값)
EPOXY_H0_M = 150e-6       # [원본] process_physics.py:11  (가정값)
EPOXY_HMIN_M = 15e-6      # [원본] process_physics.py:12  (필러 한계, 가정값)


def squeeze_equiv_radius_m(a_mm):
    """정사각 다이(한 변 a)를 같은 면적의 원판으로 근사: R = a/sqrt(pi).  [원본] process_physics.py:14"""
    return a_mm * 1e-3 / math.sqrt(math.pi)


def squeeze_blt_m(F_N, a_mm, t_s, mu_Pa_s=EPOXY_MU_PA_S, h0_m=EPOXY_H0_M, hmin_m=EPOXY_HMIN_M):
    """Stefan 스퀴즈 유동, 일정 하중.  1/h^2 = 1/h0^2 + 4 F t / (3 pi mu R^4), h >= hmin.
    [원본] process_physics.py:13-16 (education_calc.py:6-7 은 같은 식의 스칼라판)"""
    R = squeeze_equiv_radius_m(a_mm)
    h = 1.0 / math.sqrt(1.0 / h0_m ** 2 + 4.0 * F_N * t_s / (3.0 * math.pi * mu_Pa_s * R ** 4))
    return max(h, hmin_m)


def squeeze_time_to_m(hT_m, F_N, a_mm, mu_Pa_s=EPOXY_MU_PA_S, h0_m=EPOXY_H0_M):
    """목표 두께 hT 에 도달하는 시간. t = (1/hT^2 - 1/h0^2) * 3 pi mu R^4 / (4F).  [원본] process_physics.py:17-19"""
    R = squeeze_equiv_radius_m(a_mm)
    return (1.0 / hT_m ** 2 - 1.0 / h0_m ** 2) * 3.0 * math.pi * mu_Pa_s * R ** 4 / (4.0 * F_N)


def squeeze_dhdt_m_s(h_m, F_N, a_mm, mu_Pa_s=EPOXY_MU_PA_S):
    """미분형 (하중이 시간에 따라 변할 때 수치 적분용).  dh/dt = -2 F h^3 / (3 pi mu R^4).
    [원본] process_physics.py:8 주석의 식 F = 3 pi mu R^4/(2 h^3) (-dh/dt) 를 정리한 것. 원본에 함수는 없다."""
    R = squeeze_equiv_radius_m(a_mm)
    return -2.0 * F_N * h_m ** 3 / (3.0 * math.pi * mu_Pa_s * R ** 4)


def fillet_height_mm(V_mm3, a_mm, blt_um):
    """체적 보존: V = a^2*BLT + 4a*h_f^2/2  ->  h_f = sqrt(max(V_f,0)/(2a)).
    반환 (h_f [mm], V_f [mm^3]).  [원본] process_physics.py:33-35"""
    Vf = V_mm3 - a_mm * a_mm * blt_um * 1e-3
    return math.sqrt(max(Vf, 0.0) / (2.0 * a_mm)), Vf


def fillet_pct(V_mm3, a_mm, blt_um, tdie_mm=0.3):
    """필렛 높이 / 다이 두께 (%).  [원본] education_calc.py:8-9"""
    return 100.0 * fillet_height_mm(V_mm3, a_mm, blt_um)[0] / tdie_mm


def dispense_volume_for_fillet_mm3(a_mm, blt_um, fillet_frac, tdie_mm):
    """목표 필렛 비율(필렛 높이/다이 두께)에 필요한 도포량. V = a^2*BLT + 2a*(frac*t_die)^2.
    [원본] process_physics.py:37"""
    return a_mm * a_mm * blt_um * 1e-3 + 2.0 * a_mm * (fillet_frac * tdie_mm) ** 2


R_GAS = 8.314  # [원본] process_physics.py:42


def cure_rate_1_s(T_C, Ea_J_mol, Tref_C=180.0, tref_s=30 * 60.0, alpha_ref=0.95):
    """1차 아레니우스 경화. k(T) = kref*exp(-Ea/R*(1/T - 1/Tref)), kref = -ln(1-alpha_ref)/tref.
    기본값: 180 C, 30 min 에서 95 %.  [원본] process_physics.py:43"""
    kref = -math.log(1.0 - alpha_ref) / tref_s
    return kref * math.exp(-Ea_J_mol / R_GAS * (1.0 / (T_C + 273.15) - 1.0 / (Tref_C + 273.15)))


def cure_time_to_s(alpha, T_C, Ea_J_mol, **kw):
    """경화도 alpha 도달 시간 t = -ln(1-alpha)/k.  [원본] process_physics.py:46 (alpha=0.95, 분 단위로 출력)"""
    return -math.log(1.0 - alpha) / cure_rate_1_s(T_C, Ea_J_mol, **kw)


def cure_conversion(t_s, T_C, Ea_J_mol, **kw):
    """등온 경화도 alpha(t) = 1 - exp(-k t).  [원본] process_physics.py:85"""
    return 1.0 - math.exp(-cure_rate_1_s(T_C, Ea_J_mol, **kw) * t_s)


def timoshenko_curvature_1_m(h1_m, E1_Pa, a1_1_K, h2_m, E2_Pa, a2_1_K, dT_K):
    """Timoshenko 2층판 곡률.
    kappa = 6 (a2-a1) dT (1+m)^2 / ( h [3(1+m)^2 + (1+mn)(m^2 + 1/(mn))] ),  m=h1/h2, n=E1/E2, h=h1+h2.
    층 1 = 다이(Si), 층 2 = 기판. 접착층 무시(상한값).  [원본] process_physics.py:50-52, education_calc.py:10-12"""
    m = h1_m / h2_m
    n = E1_Pa / E2_Pa
    h = h1_m + h2_m
    return 6 * (a2_1_K - a1_1_K) * dT_K * (1 + m) ** 2 / (h * (3 * (1 + m) ** 2 + (1 + m * n) * (m ** 2 + 1 / (m * n))))


def warp_sagitta_m(kappa_1_m, L_m):
    """길이 L 위의 휨(활꼴 높이) w = kappa L^2 / 8.  [원본] process_physics.py:60, education_calc.py:22"""
    return kappa_1_m * L_m ** 2 / 8.0


def tilt_blt_diff_um(die_mm, parallel_um_per_10mm=2.0):
    """평행도 -> 다이 양 끝 BLT 차이.  [원본] process_physics.py:64"""
    return parallel_um_per_10mm / 10.0 * die_mm


def washburn_fill_time_s(mu_Pa_s, L_m, gap_m, gamma_N_m=0.03, theta_deg=40.0):
    """평행판 모세관 충전 시간 t = 3 mu L^2 / (gamma h cos(theta)).  [원본] education_calc.py:25-31"""
    return 3.0 * mu_Pa_s * L_m ** 2 / (gamma_N_m * gap_m * math.cos(math.radians(theta_deg)))


def washburn_front_m(mu_Pa_s, t_s, gap_m, gamma_N_m=0.03, theta_deg=40.0):
    """위 식의 역: 유동 선단 위치 L(t) = sqrt(gamma h cos(theta) t / (3 mu)). 원본에는 없음 (같은 식의 역함수)."""
    return math.sqrt(gamma_N_m * gap_m * math.cos(math.radians(theta_deg)) * t_s / (3.0 * mu_Pa_s))


def force_limit_N(a_mm, mode):
    """다이 크기별 하중 상한 (설계 목표). epoxy 1 MPa, epoxy_thin 0.5 MPa, tcb 2 MPa (a>=5 mm 면 50 N), 상한 50 N.
    [원본] education_calc.py:35-37 (round(.,1) 포함)"""
    A = a_mm * a_mm
    if mode == "epoxy":
        return round(min(1.0 * A, 50), 1)
    if mode == "epoxy_thin":
        return round(min(0.5 * A, 50), 1)
    if mode == "tcb":
        return 50.0 if a_mm >= 5 else round(min(2.0 * A, 50), 1)
    raise ValueError(mode)


SI = (130e9, 2.6e-6)    # [원본] process_physics.py:53
FR4 = (22e9, 16e-6)     # [원본] process_physics.py:53
GLASS = (64e9, 3.3e-6)  # [원본] process_physics.py:53


def doe_predict(T_C, F_N, t_s, V_mm3, a_mm=5.0, tdie_mm=0.3):
    """13장 DoE 한 회의 예측 (BLT, 필렛 %, 5 mm 길이 휨). 반올림 없이 반환.  [원본] education_calc.py:20-22"""
    blt_um = squeeze_blt_m(F_N, a_mm, t_s) * 1e6
    fil = fillet_pct(V_mm3, a_mm, blt_um, tdie_mm)
    warp_um = timoshenko_curvature_1_m(0.3e-3, 130e9, 2.6e-6, 0.4e-3, 22e9, 16e-6, T_C - 25) * (5e-3) ** 2 / 8 * 1e6
    return dict(BLT_um=blt_um, fillet_pct=fil, warp_5mm_um=warp_um)


# =====================================================================
# 2. 열 (thermal.py)
# =====================================================================
ALN = dict(k=170, rho=3260, c=740, a=4.5e-6)     # [원본] thermal.py:6
MACOR = dict(k=1.46, rho=2520, c=790, a=9.3e-6)  # [원본] thermal.py:6
SST = dict(k=16, rho=7900, c=500, a=17e-6)       # [원본] thermal.py:6
T_AMB_C = 20.0                                    # [원본] thermal.py:7


def heater_tip_capacity_J_K(heater_mm=(20, 20, 5), collet_mm=(10, 10, 10)):
    """툴 팁 열용량 = AlN 히터 + 스테인리스 콜렛.  [원본] thermal.py:10-13"""
    hx, hy, hz = [v / 1000 for v in heater_mm]
    cx, cy, cz = [v / 1000 for v in collet_mm]
    return ALN["rho"] * (hx * hy * hz) * ALN["c"] + SST["rho"] * (cx * cy * cz) * SST["c"]


def head_sim(heater=(20, 20, 5), P_max=400.0, T_set=400.0, t_end=400.0, dt=0.005, cool_at=None, air_h=0.0,
             Kp=40.0, Ki=8.0, ramp=None, n_macor=16):
    """헤드 1D 집중정수 과도 해석 (툴 팁 1절점 + MACOR n절점 + 수냉 재킷 고정온도). 명시적 오일러.
    단위: W, J/K, C, s.  [원본] thermal.py:9-41 (n_macor=16 고정이던 것을 인자로 뺐다. 기본값이면 원본과 동일)
    반환: 0.1 s 마다 기록한 t, T(팁), Tm(MACOR 평균), P, Qj(재킷 열류) 배열과 C_tip, G_mac.
    주의: t 는 t+=dt 누적이고 기록 판정은 int(round(t/dt)) % int(0.1/dt) == 0 이다 (JS 에서도 같게)."""
    hx, hy, hz = [v / 1000 for v in heater]
    V_h = hx * hy * hz
    C_h = ALN["rho"] * V_h * ALN["c"]
    V_c = 0.01 * 0.01 * 0.01
    C_c = SST["rho"] * V_c * SST["c"]
    C_tip = C_h + C_c
    A_m = 0.04 * 0.04
    L_m = 0.016
    n = n_macor
    dx = L_m / n
    Cm = MACOR["rho"] * A_m * dx * MACOR["c"]
    Gm = MACOR["k"] * A_m / dx
    A_rad = 2 * (hx * hy) + 2 * (hx + hy) * hz + 5 * 1e-4
    h_nat = 10.0
    Tamb = T_AMB_C
    T_tip = Tamb
    Tm = np.full(n, Tamb)
    Tw = Tamb
    ts, Tt, Tmean, Pw, Q_j = [], [], [], [], []
    I = 0.0
    t = 0.0
    rec_every = int(0.1 / dt)
    while t < t_end:
        sp = T_set if ramp is None else min(T_set, Tamb + ramp * t)
        if cool_at is not None and t >= cool_at:
            sp = None
        if sp is not None:
            e = sp - T_tip
            I += e * dt
            I = np.clip(I, -50, 50)
            P = np.clip(Kp * e + Ki * I, 0, P_max)
        else:
            P = 0.0
        h = h_nat + (air_h if (cool_at is not None and t >= cool_at) else 0.0)
        eps = 0.3
        sig = 5.67e-8
        q_loss = h * A_rad * (T_tip - Tamb) + eps * sig * A_rad * ((T_tip + 273) ** 4 - (Tamb + 273) ** 4)
        q_m = Gm * 2 * (T_tip - Tm[0])
        T_tip += dt * (P - q_loss - q_m) / C_tip
        qin = np.zeros(n)
        qin[0] += q_m
        flux = Gm * (Tm[:-1] - Tm[1:])
        qin[:-1] -= flux
        qin[1:] += flux
        q_out = Gm * 2 * (Tm[-1] - Tw)
        qin[-1] -= q_out
        Tm += dt * qin / Cm
        if int(round(t / dt)) % rec_every == 0:
            ts.append(t); Tt.append(T_tip); Tmean.append(Tm.mean()); Pw.append(P); Q_j.append(q_out)
        t += dt
    return dict(t=np.array(ts), T=np.array(Tt), Tm=np.array(Tmean), P=np.array(Pw), Qj=np.array(Q_j),
                C_tip=C_tip, G_mac=MACOR["k"] * A_m / L_m)


def head_heatup_metrics(r, Tamb=T_AMB_C, thr=399.0, target=400.0):
    """승온 결과 요약.  [원본] thermal.py:44-47 (399 ℃ 넘는 첫 기록 시점을 도달 시간으로 쓴다)"""
    i400 = int(np.argmax(r["T"] >= thr))
    t400 = float(r["t"][i400])
    return dict(t_to_400_s=t400, avg_ramp_K_per_s=float((target - Tamb) / t400),
                P_hold_400_W=float(np.mean(r["P"][-200:])), Q_jacket_steady_W=float(r["Qj"][-1]))


def head_cooling_time_s(r, cool_at, T_end=100.0):
    """cool_at 이후 T_end 이하가 되는 데 걸린 시간 (없으면 None).  [원본] thermal.py:50-52"""
    m = r["t"] >= cool_at
    tc = r["t"][m]
    Tc = r["T"][m]
    j = int(np.argmax(Tc <= T_end))
    return float(tc[j] - cool_at) if Tc[j] <= T_end else None


def macor_drift_metrics(r, t400, lim_K_s=0.28, alpha=MACOR["a"], L_m=0.020, waits=(0, 10, 30, 60, 120)):
    """MACOR 평균온도 변화율 -> 드리프트 속도 상한 (비대칭 100 %). drift = alpha * L * |dTm/dt|.
    [원본] thermal.py:54-59. dTm/dt 는 np.gradient(Tm, t) (비균일 간격 2차 중심차분, 양 끝 1차)."""
    dTdt = np.gradient(r["Tm"], r["t"])
    after = r["t"] > t400
    k = int(np.argmax((np.abs(dTdt) < lim_K_s) & after))
    t_wait = float(r["t"][k] - t400)
    rate = {str(w): float(np.interp(t400 + w, r["t"], np.abs(dTdt)) * alpha * L_m * 1e6) for w in waits}
    tau = float(MACOR["rho"] * 0.04 * 0.04 * 0.016 * MACOR["c"] / (2 * r["G_mac"]))
    return dict(limit_K_per_s=lim_K_s, wait_after_setpoint_s=t_wait, drift_um_per_s_at=rate, macor_tau_s=tau)


def drift_um_per_s(dTdt_K_s, alpha_1_K=MACOR["a"], L_m=0.020):
    """열팽창 드리프트 속도 = alpha * L * dT/dt.  [원본] thermal.py:57"""
    return dTdt_K_s * alpha_1_K * L_m * 1e6


def conduction_Q_W(k_W_mK, A_m2, t_m, dT_K):
    """1D 평판 전도 Q = k A dT / t.  [원본] thermal.py:61-63"""
    return k_W_mK * A_m2 / t_m * dT_K


def coolplate_rise(Q_W, flow_L_min=1.0, h_W_m2K=3000.0, A_m2=0.006, cp=4180.0):
    """수냉판 온도 상승: 냉각수 상승 Q/(mdot cp), 경막 Q/(hA), 개루프 판 상승 = 냉각수/2 + 경막.
    [원본] thermal.py:65-68 (물 밀도 1 kg/L 가정)"""
    mdot = flow_L_min / 60.0
    w = Q_W / (mdot * cp)
    f = Q_W / (h_W_m2K * A_m2)
    return dict(water_rise_K=w, film_dT_K=f, plate_rise_open_loop_K=w / 2 + f)


def thermal_offset_um_per_K(alpha_1_K, L_m=0.020):
    """홀더 열팽창 -> 광학 오프셋 변화.  [원본] thermal.py:70"""
    return alpha_1_K * L_m * 1e6


# =====================================================================
# 3. 하중·온도 제어 (control_sim.py, contact_speed_study.py)
# =====================================================================
K_CONTACT_N_MM = 2000.0  # [원본] control_sim.py:8


def k_eff_N_mm(k_spring_N_mm, k_c_N_mm=K_CONTACT_N_MM):
    """판스프링과 접촉 강성 직렬.  [원본] control_sim.py:9"""
    return 1.0 / (1.0 / k_spring_N_mm + 1.0 / k_c_N_mm)


def force_gains(k_spring_N_mm, f_c_Hz=20.0, f_i_Hz=2.0):
    """Kp = 2 pi fc / k_eff  [(mm/s)/N],  Ki = (2 pi fc)(2 pi fi) / k_eff  [(mm/s)/(N s)].
    [원본] control_sim.py:10, 40 (contact_speed_study.py:6 도 같은 식)"""
    ke = k_eff_N_mm(k_spring_N_mm)
    return 2 * np.pi * f_c_Hz / ke, (2 * np.pi * f_c_Hz) * (2 * np.pi * f_i_Hz) / ke


def force_ctrl_step(st, Fm, t, F_target, ramp, Kp, Ki, Ts, approach, F_contact=0.1):
    """하중 제어기 1주기 (펌웨어로 옮길 부분). st: dict(mode, I, t_contact, sp, v_cmd).
    approach: 접근 속도 유지, Fm > F_contact 이면 force 모드로 전환하고 I=0.
    force: sp = min(F_target, F_contact + ramp (t - t_contact)), e = sp - Fm, I += e Ts, v = Kp e + Ki I.
    [원본] control_sim.py:22-28. 주의: 적분 제한·anti-windup 없음 (원본 그대로)."""
    if st["mode"] == "approach":
        st["v_cmd"] = approach
        if Fm > F_contact:
            st["mode"] = "force"; st["t_contact"] = t; st["I"] = 0.0
    if st["mode"] == "force":
        st["sp"] = min(F_target, F_contact + ramp * (t - st["t_contact"]))
        e = st["sp"] - Fm
        st["I"] += e * Ts
        st["v_cmd"] = Kp * e + Ki * st["I"]
    return st


def force_sim(k_spring, F_target, Ts=1e-3, ramp=5.0, t_end=9.0, dt=1e-5, delay_s=0.5e-3, Kp=None, Ki=None,
              therm=0.0, approach=20e-3, noise=0.002, rng=None, k_c=K_CONTACT_N_MM, tau=0.8e-3):
    """하중 루프 시뮬레이션. 단위 mm, N, s.  [원본] control_sim.py:6-35
    플랜트: z_cmd += v dt, z += (z_cmd - z) dt/tau (서보 1차 지연), F = max(0, k_eff (z + therm t)),
    측정: 0.5 ms 순수 지연(버퍼) + 정규 노이즈. rng=None 이면 노이즈 0 (결정론적, JS 대조용).
    rng 를 주면 원본처럼 매 샘플마다 rng.normal(0, noise) 를 뽑는다."""
    k_eff = 1 / (1 / k_spring + 1 / k_c)
    if Kp is None:
        Kp = 2 * np.pi * 20 / k_eff
    if Ki is None:
        Ki = 0.0
    z_cmd = -0.02; z = -0.02
    st = dict(mode="approach", I=0.0, t_contact=None, sp=0.0, v_cmd=approach)
    t = 0.0
    n = int(t_end / dt)
    step = int(round(Ts / dt))
    buf = [0.0] * max(1, int(round(delay_s / dt)))
    T = []; F = []; SP = []
    for i in range(n):
        x_th = therm * t
        F_true = max(0.0, k_eff * (z + x_th))
        buf.append(F_true); Fd = buf.pop(0)
        if i % step == 0:
            Fm = Fd + (rng.normal(0, noise) if rng is not None else 0.0)
            force_ctrl_step(st, Fm, t, F_target, ramp, Kp, Ki, Ts, approach)
        z_cmd += st["v_cmd"] * dt
        z += (z_cmd - z) * dt / tau
        if i % 100 == 0:
            T.append(t); F.append(F_true); SP.append(st["sp"])
        t += dt
    T = np.array(T); F = np.array(F); SP = np.array(SP)
    t_contact = st["t_contact"]
    hold = (T > t_contact + F_target / ramp + 0.5)
    return dict(t=T, F=F, sp=SP, t_contact=t_contact, overshoot=float(F.max() - F_target),
                ss_err=float(np.abs(F[hold] - F_target).max()) if hold.any() else None)


def contact_peak_N(r, window_s=0.3):
    """접촉 후 window 동안 (F - sp) 최대값.  [원본] contact_speed_study.py:7-8"""
    m = (r["t"] > r["t_contact"]) & (r["t"] < r["t_contact"] + window_s)
    return float((r["F"][m] - r["sp"][m]).max())


def tcncf_profile_C(t_s):
    """10장 온도 프로파일: 150 ℃ 유지(40 s 까지) -> 20 K/s 로 300 ℃ -> 유지.  [원본] control_sim.py:65"""
    return 150.0 if t_s < 40 else (min(300.0, 150 + 20 * (t_s - 40)) if t_s < 70 else 300.0)


def temp_ctrl_step(st, Tmeas, sp, Ts, Kp=25.0, Ki=6.0, Kd=0.0, P_max=400.0, I_lim=30.0):
    """온도 PI 1주기 (펌웨어로 옮길 부분). I = clip(I + e Ts, ±I_lim), P = clip(Kp e + Ki I + Kd de/Ts, 0, Pmax),
    포화 시 이번 적분을 되돌림(I -= e Ts).  [원본] control_sim.py:53-56"""
    e = sp - Tmeas
    st["I"] = float(np.clip(st["I"] + e * Ts, -I_lim, I_lim))
    st["P"] = float(np.clip(Kp * e + Ki * st["I"] + Kd * (e - st["prev_e"]) / Ts, 0, P_max))
    st["prev_e"] = e
    if st["P"] >= P_max or st["P"] <= 0:
        st["I"] -= e * Ts
    return st


def temp_sim(Ts=10e-3, profile=tcncf_profile_C, t_end=120, dt=1e-3, Kp=25.0, Ki=6.0, Kd=0.0, tc_tau=5e-3,
             P_max=400.0, noise_C=0.2, rng=None):
    """온도 루프 시뮬레이션 (툴 팁 C=8.77 J/K + MACOR 3절점, 대류 h=10, 복사 eps=0.3, A=0.0011 m^2, 열전대 1차 지연).
    [원본] control_sim.py:45-64. rng=None 이면 측정 노이즈 0. 원본은 노이즈 0.2 ℃ 고정(rng.normal(0,0.2)).
    주의: 원본 47행 Gm 은 쓰이지 않는다. 손실 면적 A=0.0011 은 thermal.py 의 A_rad(0.0017)와 다르다."""
    C = 8.77; A = 0.0011; Tamb = 20.0
    Cm = 2.52e3 * 790 * 0.04 * 0.04 * 0.016
    nM = 3
    Tm = np.full(nM, Tamb); T = Tamb; Ttc = Tamb
    st = dict(I=0.0, P=0.0, prev_e=0.0)
    Gseg = 1.46 * 0.0016 / (0.016 / nM)
    out_t = []; out_T = []; out_sp = []; out_P = []
    step = int(round(Ts / dt))
    for i in range(int(t_end / dt)):
        t = i * dt
        sp = profile(t)
        if i % step == 0:
            meas = Ttc + (rng.normal(0, noise_C) if rng is not None else 0.0)
            temp_ctrl_step(st, meas, sp, Ts, Kp, Ki, Kd, P_max)
        P = st["P"]
        q_loss = (10 * A * (T - Tamb) + 0.3 * 5.67e-8 * A * ((T + 273) ** 4 - (Tamb + 273) ** 4))
        q1 = Gseg * 2 * (T - Tm[0])
        T += dt * (P - q_loss - q1) / C
        q = np.zeros(nM); q[0] += q1
        fl = Gseg * (Tm[:-1] - Tm[1:]); q[:-1] -= fl; q[1:] += fl
        q[-1] -= Gseg * 2 * (Tm[-1] - Tamb)
        Tm += dt * q / (Cm / nM)
        Ttc += dt * (T - Ttc) / tc_tau
        if i % 50 == 0:
            out_t.append(t); out_T.append(T); out_sp.append(sp); out_P.append(P)
    return np.array(out_t), np.array(out_T), np.array(out_sp), np.array(out_P)


def temp_metrics(tt, TT, PP):
    """[원본] control_sim.py:69-72"""
    hold150 = (tt > 25) & (tt < 40)
    hold300 = (tt > 55 + 10) & (tt < 120)
    ramp_m = (tt > 41) & (tt < 47)
    return dict(overshoot_C=float(TT[(tt > 45)].max() - 300), stab_150_C=float(np.abs(TT[hold150] - 150).max()),
                stab_300_C=float(np.abs(TT[hold300] - 300).max()),
                ramp_K_s=float(np.polyfit(tt[ramp_m], TT[ramp_m], 1)[0]), P_hold_W=float(PP[hold300].mean()))


# =====================================================================
# 4. 비전 (vision.py, vision_robust.py)  -- OpenCV 없이 numpy 로 같은 연산
# =====================================================================
PX_UM = 1.725  # [원본] vision.py:5


def render_cross(dx, dy, N=128, arm=60, w=6, blur=1.0, bright=220, dark=30):
    """십자 피듀셜 합성 영상 (픽셀 면적 피복률 정확 계산) + 가우시안 블러.  [원본] vision.py:7-18
    픽셀 i 는 [i - N/2, i + 1 - N/2) 구간. 블러는 cv2.GaussianBlur(img,(0,0),sigma) 와 같은 규칙:
    커널 크기 = round(sigma*4*2+1) | 1 (float 영상), 경계 BORDER_REFLECT_101, 분리형."""
    edges = np.arange(N + 1) - N / 2

    def ov(a0, a1):
        lo = np.maximum(edges[:-1], a0); hi = np.minimum(edges[1:], a1)
        return np.clip(hi - lo, 0, 1)
    hx, hy = ov(dx - arm / 2, dx + arm / 2), ov(dy - w / 2, dy + w / 2)
    vx, vy = ov(dx - w / 2, dx + w / 2), ov(dy - arm / 2, dy + arm / 2)
    cx_, cy_ = ov(dx - w / 2, dx + w / 2), ov(dy - w / 2, dy + w / 2)
    cov = np.outer(hy, hx) + np.outer(vy, vx) - np.outer(cy_, cx_)
    img = (bright - (bright - dark) * cov).astype(np.float32).astype(np.float64)
    if blur > 0:
        img = gaussian_blur(img, blur)
    return img


def gaussian_kernel(sigma):
    """cv2.getGaussianKernel(ksize, sigma) 와 같은 정규화 1D 커널 (ksize = round(8 sigma + 1) | 1)."""
    k = int(round(sigma * 4 * 2 + 1)) | 1
    x = np.arange(k) - (k - 1) / 2
    g = np.exp(-x ** 2 / (2 * sigma ** 2))
    return g / g.sum()


def gaussian_blur(img, sigma):
    """분리형 가우시안 블러, 경계 reflect-101 (numpy pad 'reflect').  cv2.GaussianBlur 근사 (float64)."""
    g = gaussian_kernel(sigma)
    r = len(g) // 2
    p = np.pad(img, ((0, 0), (r, r)), mode="reflect")
    tmp = sum(g[i] * p[:, i:i + img.shape[1]] for i in range(len(g)))
    p = np.pad(tmp, ((r, r), (0, 0)), mode="reflect")
    return sum(g[i] * p[i:i + img.shape[0], :] for i in range(len(g)))


def ncc_map(img, tpl):
    """cv2.TM_CCOEFF_NORMED 와 같은 정의의 정규화 상호상관 맵.
    R(x,y) = sum(T' I') / sqrt(sum T'^2 * sum I'^2),  T' = T - mean(T), I' = 패치 - mean(패치)."""
    from numpy.lib.stride_tricks import sliding_window_view
    th, tw = tpl.shape
    W = sliding_window_view(img, (th, tw))
    Tp = tpl - tpl.mean()
    Wm = W.mean(axis=(2, 3), keepdims=True)
    Ip = W - Wm
    num = np.einsum("ijkl,kl->ij", Ip, Tp)
    den = np.sqrt((Tp ** 2).sum() * (Ip ** 2).sum(axis=(2, 3)))
    return num / den


def subpixel_peak(a, b, c, method="gauss"):
    """3점 피크 보간. gauss: 세 값이 모두 양수이면 로그를 취한 뒤 포물선. offset = 0.5 (a - c) / (a - 2b + c).
    [원본] vision.py:24-26"""
    if method == "gauss" and min(a, b, c) > 0:
        a, b, c = math.log(a), math.log(b), math.log(c)
    d = a - 2 * b + c
    return 0.0 if d == 0 else 0.5 * (a - c) / d


_TPL_CACHE = {}


def measure_cross(img, method="gauss", tpl=None):
    """NCC 최대 픽셀 + 서브픽셀 보간으로 마크 중심 (px, 영상 중심 기준).  [원본] vision.py:21-29
    템플릿 = render_cross(0,0,N=80) (blur 1)."""
    if tpl is None:
        if "tpl" not in _TPL_CACHE:
            _TPL_CACHE["tpl"] = render_cross(0, 0, N=80)
        tpl = _TPL_CACHE["tpl"]
    r = ncc_map(img, tpl)
    py, px = np.unravel_index(int(np.argmax(r)), r.shape)
    sx = subpixel_peak(r[py, px - 1], r[py, px], r[py, px + 1], method)
    sy = subpixel_peak(r[py - 1, px], r[py, px], r[py + 1, px], method)
    cx = px + sx + tpl.shape[1] / 2 - img.shape[1] / 2
    cy = py + sy + tpl.shape[0] / 2 - img.shape[0] / 2
    return float(cx), float(cy)


def affine_fit(P_px, S_um):
    """s = A p + b 최소제곱 (계수 6개). 반환 A(2x2), b(2), 회전[deg], 배율[um/px].  [원본] vision.py:67-68, 72-73"""
    P_px = np.asarray(P_px, float); S_um = np.asarray(S_um, float)
    M = np.hstack([P_px, np.ones((len(P_px), 1))])
    coef, _, _, _ = np.linalg.lstsq(M, S_um, rcond=None)
    A = coef[:2].T; b = coef[2]
    return A, b, float(np.rad2deg(np.arctan2(A[1, 0], A[0, 0]))), float(np.hypot(A[0, 0], A[1, 0]))


def affine_true(rot_deg=0.3, scale_err=0.002, shear=0.0005, px_um=PX_UM, b=(12.0, -7.0)):
    """시험용 참 아핀 (원본 값).  [원본] vision.py:61-62"""
    th = np.deg2rad(rot_deg); sc = px_um * (1 + scale_err)
    A = np.array([[sc * np.cos(th), -sc * np.sin(th) + shear * px_um], [sc * np.sin(th), sc * np.cos(th)]])
    return A, np.array(b)


def angle_sigma_deg(per_mark_sigma_um, L_um=4000.0, n_marks=4):
    """마크 간격 L 에서 각도 측정 sigma. 2 마크: sqrt2*sqrt2*s/L, 4 마크(대각 2쌍 평균): sqrt2*s/L.  [원본] vision.py:94-96"""
    f = math.sqrt(2) * math.sqrt(2) if n_marks == 2 else math.sqrt(2)
    return float(np.rad2deg(f * per_mark_sigma_um / L_um))


def align_once(rng, sig_ch_um, init_um=30.0, init_deg=0.3, tol_um=0.15, tol_deg=0.002, max_iter=3,
               map_err=5e-4, stage_sigma_um=0.02, theta_meas_deg=0.0005, theta_cmd_deg=0.0003):
    """폐루프 정렬 1회 (몬테카를로용, 확률적). 반환 (최종 오차 [um] 2벡터, 최종 각도 [rad], 반복 횟수).
    [원본] vision.py:78-86. 측정 노이즈 = sqrt(2)*sig_ch (칩·기판 두 채널)."""
    d = np.array([rng.uniform(-init_um, init_um), rng.uniform(-init_um, init_um)])
    t = np.deg2rad(rng.uniform(-init_deg, init_deg))
    for it in range(1, max_iter + 1):
        meas = d + rng.normal(0, np.sqrt(2) * sig_ch_um, 2)
        meas_t = t + rng.normal(0, np.deg2rad(theta_meas_deg))
        if np.all(np.abs(meas) <= tol_um) and abs(np.rad2deg(meas_t)) <= tol_deg:
            return d, t, it - 1
        d = d - meas * (1 + rng.normal(0, map_err)) + rng.normal(0, stage_sigma_um, 2)
        t = t - meas_t + np.deg2rad(rng.normal(0, theta_cmd_deg))
    meas = d + rng.normal(0, np.sqrt(2) * sig_ch_um, 2)
    return d, t, max_iter


# =====================================================================
# 5. 정합 오차 예산 (error_budget.py, integration.py)
# =====================================================================
def sigma_of(dist, p):
    """정규('n'): sigma = p, 균일('u', 반폭 p): sigma = p/sqrt3.  [원본] error_budget.py:18, integration.py:18"""
    return p if dist == "n" else p / np.sqrt(3)


def rss_sigma(terms):
    """terms = [(dist, p), ...] 의 RSS 1 sigma.  [원본] error_budget.py:23"""
    return float(np.sqrt(sum(sigma_of(d, p) ** 2 for d, p in terms)))


BUDGET_TERMS = [("n", 0.10), ("u", 0.15), ("n", 0.10), ("n", 0.02), ("n", 0.12), ("u", 0.26), ("u", 0.12),
                ("n", 0.12), ("n", 0.05)]  # [원본] error_budget.py:7-17 (X축, um)
TYPICAL_TERMS = [("n", 0.021), ("n", 0.030), ("n", 0.048), ("n", 0.02), ("n", 0.10), ("u", 0.25), ("u", 0.055),
                 ("n", 0.12), ("n", 0.05)]  # [원본] integration.py:8-16 (3번째 열)
CONSERVATIVE_TERMS = [("n", 0.075), ("u", 0.15), ("n", 0.10), ("n", 0.02), ("n", 0.12), ("u", 0.26), ("u", 0.20),
                      ("n", 0.12), ("n", 0.05)]  # [원본] integration.py:8-16 (4번째 열)


# =====================================================================
# 6. 구동부 (drive_calc.py) -- 사이클 시간 모델이 속도·가속도 값을 가져다 쓴다
# =====================================================================
def ballscrew(m, lead, d, L, eta, a, v, mu, Fext=0.0, vertical=False, Jm=0.0, Ca=None, support=3.927, eta2=10.0):
    """볼스크루 축 계산. 단위: m kg, lead/d/L mm, a m/s^2, v mm/s, F N, T N m.  [원본] drive_calc.py:3-25"""
    g = 9.81; rho = 7850; E = 206e3
    Jscrew = np.pi * rho * (L / 1000) * (d / 1000) ** 4 / 32
    Jload = m * (lead / 1000 / (2 * np.pi)) ** 2
    alpha = 2 * np.pi * a / (lead / 1000)
    Ffr = mu * m * g if not vertical else 0.0
    Fg = m * g if vertical else 0.0
    F = m * a + Ffr + Fg + Fext
    T_load = F * lead / 1000 / (2 * np.pi * eta)
    T_acc = (Jscrew + Jm) * alpha
    F_hold = Ffr + Fg + Fext
    T_hold = F_hold * lead / 1000 / (2 * np.pi * eta)
    rpm = v / lead * 60
    dr = d * 0.83
    n_crit = support ** 2 * 60 / (2 * np.pi * (L / 1000) ** 2) * np.sqrt(
        E * 1e6 * np.pi * (dr / 1000) ** 4 / 64 / (rho * np.pi * (dr / 1000) ** 2 / 4))
    P_buck = eta2 * dr ** 4 / L ** 2 * 1e4
    life = (Ca / (1.2 * max(F_hold, 1))) ** 3 * 1e6 * lead / 1000 / 1000 if Ca else None
    return dict(F_peak_N=F, T_load_Nm=T_load, T_acc_Nm=T_acc, T_peak_Nm=T_load + T_acc, T_hold_Nm=T_hold,
                J_screw=Jscrew, J_load=Jload, rpm_max=rpm, n_crit_rpm=n_crit, P_buckle_N=P_buck, life_km=life)


def leaf_flexure(k_N_mm, Fmax_N, E_MPa=200e3, b_mm=20.0, L_mm=25.0):
    """판스프링 4장: k = 4 E b t^3 / L^3 -> t, 처짐 F/k, 응력 3 E t d / L^2.  [원본] drive_calc.py:45-49"""
    t = (k_N_mm * L_mm ** 3 / (4 * E_MPa * b_mm)) ** (1 / 3)
    d = Fmax_N / k_N_mm
    return dict(t_mm=t, defl_mm=d, stress_MPa=3 * E_MPa * t * d / L_mm ** 2)


# =====================================================================
# golden vector 생성
# =====================================================================
def _v(vid, model, function, src, inputs, outputs, tol=None, note=None):
    d = dict(id=vid, model=model, function=function, source=src, inputs=inputs, output=outputs,
             tolerance=tol or dict(rel=1e-9, abs=1e-12))
    if note:
        d["note"] = note
    return d


def _q(value, unit):
    if isinstance(value, (np.floating, np.integer)):
        value = value.item()
    return dict(value=value, unit=unit)


def build_golden():
    V = []
    PP = "calc/process_physics.py"
    EC = "calc/education_calc.py"
    # --- squeeze BLT
    for F, a, t in [(0.2, 5, 10.0), (1.0, 5, 2.0), (5.0, 10, 5.0), (20.0, 2, 0.001), (2.0, 5, 10.0)]:
        V.append(_v(f"ncf.squeeze_blt.F{F}_a{a}_t{t}", "ncf(squeeze, Stefan)", "squeeze_blt_m", f"{PP}:13-16",
                    dict(F=_q(F, "N"), a=_q(a, "mm"), t=_q(t, "s"), mu=_q(EPOXY_MU_PA_S, "Pa*s"),
                         h0=_q(EPOXY_H0_M, "m"), h_min=_q(EPOXY_HMIN_M, "m")),
                    dict(h=_q(squeeze_blt_m(F, a, t), "m"))))
    for F, a in [(0.2, 2), (1, 5), (5, 10), (20, 10)]:
        V.append(_v(f"ncf.squeeze_time_to.F{F}_a{a}", "ncf(squeeze, Stefan)", "squeeze_time_to_m", f"{PP}:17-19",
                    dict(hT=_q(25e-6, "m"), F=_q(F, "N"), a=_q(a, "mm"), mu=_q(EPOXY_MU_PA_S, "Pa*s"),
                         h0=_q(EPOXY_H0_M, "m")),
                    dict(t=_q(squeeze_time_to_m(25e-6, F, a), "s"))))
    for h, F, a in [(150e-6, 1.0, 5), (50e-6, 1.0, 5), (25e-6, 5.0, 10)]:
        V.append(_v(f"ncf.squeeze_dhdt.h{h}_F{F}_a{a}", "ncf(squeeze, Stefan)", "squeeze_dhdt_m_s",
                    f"{PP}:8 (주석의 식, 원본 함수 없음)",
                    dict(h=_q(h, "m"), F=_q(F, "N"), a=_q(a, "mm"), mu=_q(EPOXY_MU_PA_S, "Pa*s")),
                    dict(dhdt=_q(squeeze_dhdt_m_s(h, F, a), "m/s")),
                    note="원본 squeeze_blt 의 시간 미분과 일치해야 함 (검증 스크립트가 수치미분으로 확인)"))
    # --- fillet
    for Vv, a, blt in [(0.66, 5, 25.0), (0.80, 5, 24.1), (0.66, 5, 51.3), (1.2, 10, 25.0)]:
        hf, Vf = fillet_height_mm(Vv, a, blt)
        V.append(_v(f"epoxy.fillet.V{Vv}_a{a}_blt{blt}", "epoxy(fillet, 체적 보존)", "fillet_height_mm / fillet_pct",
                    f"{PP}:33-35, {EC}:8-9",
                    dict(V=_q(Vv, "mm^3"), a=_q(a, "mm"), BLT=_q(blt, "um"), t_die=_q(0.3, "mm")),
                    dict(h_f=_q(hf, "mm"), V_f=_q(Vf, "mm^3"), fillet_pct=_q(fillet_pct(Vv, a, blt), "%"))))
    for frac in (0.2, 0.5):
        V.append(_v(f"epoxy.dispense_volume.frac{frac}", "epoxy(fillet, 체적 보존)", "dispense_volume_for_fillet_mm3",
                    f"{PP}:37", dict(a=_q(5.0, "mm"), BLT=_q(25.0, "um"), fillet_frac=_q(frac, "-"),
                                     t_die=_q(0.3, "mm")),
                    dict(V=_q(dispense_volume_for_fillet_mm3(5.0, 25.0, frac, 0.3), "mm^3"))))
    # --- cure
    for T, Ea in [(120, 60e3), (150, 80e3), (180, 80e3), (200, 100e3), (250, 80e3)]:
        V.append(_v(f"cure.arrhenius.T{T}_Ea{int(Ea/1e3)}", "cure(1차 아레니우스)", "cure_rate_1_s / cure_time_to_s",
                    f"{PP}:42-46",
                    dict(T=_q(T, "C"), Ea=_q(Ea, "J/mol"), T_ref=_q(180.0, "C"), t_ref=_q(1800.0, "s"),
                         alpha_ref=_q(0.95, "-")),
                    dict(k=_q(cure_rate_1_s(T, Ea), "1/s"), t95=_q(cure_time_to_s(0.95, T, Ea), "s"))))
    for t, T in [(60.0, 150), (600.0, 180), (1800.0, 180)]:
        V.append(_v(f"cure.conversion.t{t}_T{T}", "cure(1차 아레니우스)", "cure_conversion", f"{PP}:85",
                    dict(t=_q(t, "s"), T=_q(T, "C"), Ea=_q(80e3, "J/mol")),
                    dict(alpha=_q(cure_conversion(t, T, 80e3), "-"))))
    # --- warpage (Timoshenko)
    for name, (h1, E1, a1, h2, E2, a2, dT, L) in {
        "Si300_FR4_400_dT155_L10": (0.3e-3, 130e9, 2.6e-6, 0.4e-3, 22e9, 16e-6, 155, 10e-3),
        "Si100_FR4_400_dT125_L10": (0.1e-3, 130e9, 2.6e-6, 0.4e-3, 22e9, 16e-6, 125, 10e-3),
        "Si725_glass_400_dT155_L10": (0.725e-3, 130e9, 2.6e-6, 0.4e-3, 64e9, 3.3e-6, 155, 10e-3),
        "Si300_FR4_400_dT125_L5": (0.3e-3, 130e9, 2.6e-6, 0.4e-3, 22e9, 16e-6, 125, 5e-3),
    }.items():
        k = timoshenko_curvature_1_m(h1, E1, a1, h2, E2, a2, dT)
        V.append(_v(f"warpage.timoshenko.{name}", "warpage(Timoshenko 2층)", "timoshenko_curvature_1_m / warp_sagitta_m",
                    f"{PP}:50-52,60; {EC}:10-12,22",
                    dict(h1=_q(h1, "m"), E1=_q(E1, "Pa"), a1=_q(a1, "1/K"), h2=_q(h2, "m"), E2=_q(E2, "Pa"),
                         a2=_q(a2, "1/K"), dT=_q(dT, "K"), L=_q(L, "m")),
                    dict(kappa=_q(k, "1/m"), warp=_q(warp_sagitta_m(k, L), "m"))))
    for d in (2, 5, 10):
        V.append(_v(f"epoxy.tilt_blt.d{d}", "epoxy(평행도)", "tilt_blt_diff_um", f"{PP}:64",
                    dict(die=_q(d, "mm"), parallelism=_q(2.0, "um/10mm")), dict(dBLT=_q(tilt_blt_diff_um(d), "um"))))
    # --- Washburn
    for mu, L, h in [(0.8, 5e-3, 50e-6), (0.8, 10e-3, 30e-6), (0.1, 10e-3, 50e-6), (0.1, 5e-3, 30e-6)]:
        V.append(_v(f"muf.washburn.mu{mu}_L{L}_h{h}", "muf(capillary, Washburn 평행판)", "washburn_fill_time_s",
                    f"{EC}:25-31",
                    dict(mu=_q(mu, "Pa*s"), L=_q(L, "m"), gap=_q(h, "m"), gamma=_q(0.03, "N/m"),
                         theta=_q(40.0, "deg")),
                    dict(t_fill=_q(washburn_fill_time_s(mu, L, h), "s"))))
    for t in (1.0, 10.0, 26.1):
        V.append(_v(f"muf.washburn_front.t{t}", "muf(capillary, Washburn 평행판)", "washburn_front_m",
                    f"{EC}:31 의 역함수 (원본 함수 없음)",
                    dict(mu=_q(0.1, "Pa*s"), t=_q(t, "s"), gap=_q(50e-6, "m"), gamma=_q(0.03, "N/m"),
                         theta=_q(40.0, "deg")),
                    dict(L=_q(washburn_front_m(0.1, t, 50e-6), "m"))))
    for a in (2, 3, 5, 7, 10):
        V.append(_v(f"recipe.force_limit.a{a}", "recipe(하중 상한)", "force_limit_N", f"{EC}:34-37",
                    dict(a=_q(a, "mm")),
                    dict(epoxy=_q(force_limit_N(a, "epoxy"), "N"), epoxy_thin=_q(force_limit_N(a, "epoxy_thin"), "N"),
                         tcb=_q(force_limit_N(a, "tcb"), "N"))))
    for T, F, t, Vv in [(150, 0.5, 2, 0.66), (150, 2.0, 2, 0.80), (180, 0.5, 10, 0.66), (180, 2.0, 10, 0.80)]:
        r = doe_predict(T, F, t, Vv)
        V.append(_v(f"epoxy.doe.T{T}_F{F}_t{t}_V{Vv}", "epoxy(DoE 합성)", "doe_predict", f"{EC}:15-23",
                    dict(T=_q(T, "C"), F=_q(F, "N"), t=_q(t, "s"), V=_q(Vv, "mm^3"), a=_q(5.0, "mm"),
                         t_die=_q(0.3, "mm")),
                    dict(BLT=_q(r["BLT_um"], "um"), fillet_pct=_q(r["fillet_pct"], "%"),
                         warp_5mm=_q(r["warp_5mm_um"], "um"))))
    # --- thermal: algebraic
    TH = "calc/thermal.py"
    for hm in [(20, 20, 5), (30, 30, 12), (15, 15, 3)]:
        V.append(_v(f"thermal.tip_capacity.{hm[0]}x{hm[1]}x{hm[2]}", "thermal(헤드 집중정수)", "heater_tip_capacity_J_K",
                    f"{TH}:10-13", dict(heater=_q(list(hm), "mm"), collet=_q([10, 10, 10], "mm")),
                    dict(C_tip=_q(heater_tip_capacity_J_K(hm), "J/K"))))
    for name, k, t in [("MACOR6", 1.46, 0.006), ("CaSi10", 0.12, 0.010), ("CaSi15", 0.12, 0.015)]:
        V.append(_v(f"thermal.chuck_conduction.{name}", "thermal(척 1D 정상상태)", "conduction_Q_W", f"{TH}:61-63",
                    dict(k=_q(k, "W/mK"), A=_q(0.11 * 0.11, "m^2"), t=_q(t, "m"), dT=_q(180.0, "K")),
                    dict(Q=_q(conduction_Q_W(k, 0.11 * 0.11, t, 180.0), "W"))))
    for Q, fl in [(26.136, 1.0), (55.46, 0.5), (10.0, 2.0)]:
        r = coolplate_rise(Q, fl)
        V.append(_v(f"thermal.coolplate.Q{Q}_f{fl}", "thermal(수냉판)", "coolplate_rise", f"{TH}:65-68",
                    dict(Q=_q(Q, "W"), flow=_q(fl, "L/min"), h=_q(3000.0, "W/m2K"), A=_q(0.006, "m^2"),
                         cp=_q(4180.0, "J/kgK")),
                    {k2: _q(v2, "K") for k2, v2 in r.items()}))
    for name, al in [("Al6061", 23e-6), ("SUS304", 17e-6), ("Invar36", 1.2e-6)]:
        V.append(_v(f"thermal.offset_per_K.{name}", "thermal(광학 홀더)", "thermal_offset_um_per_K", f"{TH}:70",
                    dict(alpha=_q(al, "1/K"), L=_q(0.020, "m")), dict(offset=_q(thermal_offset_um_per_K(al), "um/K"))))
    for dTdt in (0.28, 1.0, 4.87):
        V.append(_v(f"thermal.drift_rate.{dTdt}", "thermal(MACOR 드리프트)", "drift_um_per_s", f"{TH}:57",
                    dict(dTdt=_q(dTdt, "K/s"), alpha=_q(MACOR["a"], "1/K"), L=_q(0.020, "m")),
                    dict(drift=_q(drift_um_per_s(dTdt), "um/s"))))
    # --- thermal: transient head_sim
    r = head_sim(T_set=400, t_end=300, Kp=1e6, Ki=0)
    hm_ = head_heatup_metrics(r)
    samp = {f"T_at_{tt}s": _q(float(np.interp(tt, r["t"], r["T"])), "C") for tt in (1.0, 5.0, 10.0, 60.0)}
    samp.update({f"Tm_at_{tt}s": _q(float(np.interp(tt, r["t"], r["Tm"])), "C") for tt in (10.0, 60.0, 300.0)})
    samp.update({k2: _q(v2, u) for (k2, v2), u in zip(hm_.items(), ["s", "K/s", "W", "W"])})
    V.append(_v("thermal.head_sim.heatup_400_bangbang", "thermal(헤드 집중정수 과도)", "head_sim + head_heatup_metrics",
                f"{TH}:9-47",
                dict(heater=_q([20, 20, 5], "mm"), P_max=_q(400.0, "W"), T_set=_q(400.0, "C"), t_end=_q(300.0, "s"),
                     dt=_q(0.005, "s"), Kp=_q(1e6, "W/K"), Ki=_q(0.0, "W/(K*s)"), n_macor=_q(16, "-")),
                samp, tol=dict(rel=1e-9, abs=1e-9),
                note="명시적 오일러, t+=dt 누적, 0.1 s 기록. T_at_* 는 기록 배열 선형보간"))
    md = macor_drift_metrics(r, hm_["t_to_400_s"])
    V.append(_v("thermal.head_sim.drift_after_400", "thermal(MACOR 드리프트)", "macor_drift_metrics", f"{TH}:54-59",
                dict(source_run=_q("thermal.head_sim.heatup_400_bangbang", "-"), lim=_q(0.28, "K/s")),
                dict(wait_after_setpoint=_q(md["wait_after_setpoint_s"], "s"),
                     **{f"drift_rate_at_{k2}s": _q(v2, "um/s") for k2, v2 in md["drift_um_per_s_at"].items()},
                     macor_tau=_q(md["macor_tau_s"], "s")), tol=dict(rel=1e-7, abs=1e-9)))
    for air_h, tend in [(400, 400), (0, 700)]:
        rc = head_sim(T_set=400, t_end=tend, Kp=1e6, Ki=0, cool_at=300, air_h=air_h)
        V.append(_v(f"thermal.head_sim.cool_400_100_h{air_h}", "thermal(헤드 집중정수 과도)",
                    "head_sim + head_cooling_time_s", f"{TH}:49-52",
                    dict(T_set=_q(400.0, "C"), cool_at=_q(300.0, "s"), air_h=_q(air_h, "W/m2K"), t_end=_q(tend, "s"),
                         Kp=_q(1e6, "W/K"), Ki=_q(0.0, "W/(K*s)")),
                    dict(t_400_to_100=_q(head_cooling_time_s(rc, 300), "s")), tol=dict(rel=1e-9, abs=1e-9)))
    rp = head_sim(T_set=250, t_end=60, Kp=40.0, Ki=8.0, ramp=20.0)
    V.append(_v("thermal.head_sim.pi_ramp20_250", "thermal(헤드 집중정수 과도)", "head_sim (PI, ramp)", f"{TH}:9-41",
                dict(T_set=_q(250.0, "C"), ramp=_q(20.0, "K/s"), t_end=_q(60.0, "s"), Kp=_q(40.0, "W/K"),
                     Ki=_q(8.0, "W/(K*s)"), dt=_q(0.005, "s")),
                dict(T_at_5s=_q(float(np.interp(5.0, rp["t"], rp["T"])), "C"),
                     T_at_12s=_q(float(np.interp(12.0, rp["t"], rp["T"])), "C"),
                     T_final=_q(float(rp["T"][-1]), "C"), P_final=_q(float(rp["P"][-1]), "W"),
                     Qj_final=_q(float(rp["Qj"][-1]), "W")), tol=dict(rel=1e-9, abs=1e-9),
                note="원본 결과 JSON 에는 없는 조건 (PI + 램프 경로 점검용)"))
    # --- control: force
    CS = "calc/control_sim.py"
    for k in (2.0, 50.0, 10.0):
        Kp, Ki = force_gains(k)
        V.append(_v(f"control.force_gains.k{k}", "control(하중 PI)", "k_eff_N_mm / force_gains", f"{CS}:9-10,40",
                    dict(k_spring=_q(k, "N/mm"), k_contact=_q(2000.0, "N/mm"), f_c=_q(20.0, "Hz"), f_i=_q(2.0, "Hz")),
                    dict(k_eff=_q(k_eff_N_mm(k), "N/mm"), Kp=_q(Kp, "(mm/s)/N"), Ki=_q(Ki, "(mm/s)/(N*s)"))))
    for name, k, Ft, Ts, therm in [("low1N_1ms", 2.0, 1.0, 1e-3, 0.0), ("high20N_1ms", 50.0, 20.0, 1e-3, 0.0),
                                    ("high20N_10ms", 50.0, 20.0, 10e-3, 0.0),
                                    ("high20N_1ms_therm", 50.0, 20.0, 1e-3, 2.6e-3)]:
        Kp, Ki = force_gains(k)
        r = force_sim(k, Ft, Ts=Ts, therm=therm, Ki=Ki, rng=None)
        V.append(_v(f"control.force_sim.{name}.noise0", "control(하중 PI)", "force_sim (noise=0)", f"{CS}:6-35",
                    dict(k_spring=_q(k, "N/mm"), F_target=_q(Ft, "N"), Ts=_q(Ts, "s"), ramp=_q(5.0, "N/s"),
                         t_end=_q(9.0, "s"), dt=_q(1e-5, "s"), delay=_q(0.5e-3, "s"), tau_servo=_q(0.8e-3, "s"),
                         approach=_q(0.02, "mm/s"), therm=_q(therm, "mm/s"), Kp=_q(Kp, "(mm/s)/N"),
                         Ki=_q(Ki, "(mm/s)/(N*s)"), noise=_q(0.0, "N")),
                    dict(t_contact=_q(r["t_contact"], "s"), overshoot=_q(r["overshoot"], "N"),
                         ss_err=_q(r["ss_err"], "N"), F_at_t_contact_plus_1s=_q(
                             float(np.interp(r["t_contact"] + 1.0, r["t"], r["F"])), "N")),
                    tol=dict(rel=1e-7, abs=1e-9),
                    note="원본 표(control.json)는 노이즈 0.002 N 포함값이라 이 값과 다르다. JS 결정론 대조는 noise=0 으로."))
    for Ts, ap in [(1e-3, 0.02), (1e-3, 0.5), (10e-3, 0.02), (10e-3, 0.5)]:
        Kp, Ki = force_gains(50.0)
        r = force_sim(50.0, 5.0, Ts=Ts, approach=ap, Ki=Ki, t_end=4.0, rng=None)
        V.append(_v(f"control.contact_peak.Ts{Ts}_ap{ap}.noise0", "control(하중 PI, 접촉 과도)",
                    "force_sim + contact_peak_N (noise=0)", "calc/contact_speed_study.py:3-8",
                    dict(k_spring=_q(50.0, "N/mm"), F_target=_q(5.0, "N"), Ts=_q(Ts, "s"), approach=_q(ap, "mm/s"),
                         t_end=_q(4.0, "s"), noise=_q(0.0, "N")),
                    dict(peak_over_sp_0p3s=_q(contact_peak_N(r), "N"), t_contact=_q(r["t_contact"], "s")),
                    tol=dict(rel=1e-7, abs=1e-9)))
    # --- control: temperature
    for name, Ts in [("10ms", 10e-3), ("100ms", 100e-3)]:
        tt, TT, ss, PPw = temp_sim(Ts=Ts, rng=None)
        m = temp_metrics(tt, TT, PPw)
        V.append(_v(f"control.temp_sim.{name}.noise0", "control(온도 PI)", "temp_sim + temp_metrics (noise=0)",
                    f"{CS}:45-72",
                    dict(Ts=_q(Ts, "s"), profile=_q("150C(<40s) -> 20K/s -> 300C", "-"), t_end=_q(120.0, "s"),
                         dt=_q(1e-3, "s"), Kp=_q(25.0, "W/K"), Ki=_q(6.0, "W/(K*s)"), tc_tau=_q(5e-3, "s"),
                         P_max=_q(400.0, "W"), noise=_q(0.0, "C")),
                    dict(overshoot=_q(m["overshoot_C"], "C"), stab_150=_q(m["stab_150_C"], "C"),
                         stab_300=_q(m["stab_300_C"], "C"), ramp=_q(m["ramp_K_s"], "K/s"), P_hold=_q(m["P_hold_W"], "W"),
                         T_at_50s=_q(float(np.interp(50.0, tt, TT)), "C")),
                    tol=dict(rel=1e-7, abs=1e-9)))
    for t in (0.0, 39.999, 40.0, 45.0, 47.5, 70.0):
        V.append(_v(f"control.tcncf_profile.t{t}", "control(온도 프로파일)", "tcncf_profile_C", f"{CS}:65",
                    dict(t=_q(t, "s")), dict(sp=_q(tcncf_profile_C(t), "C"))))
    # --- vision
    VS = "calc/vision.py"
    for a, b, c in [(0.9, 1.0, 0.95), (0.80, 0.99, 0.97), (0.5, 0.6, 0.5), (-0.1, 0.5, 0.4)]:
        V.append(_v(f"alignment.subpixel.{a}_{b}_{c}", "alignment(서브픽셀 보간)", "subpixel_peak", f"{VS}:24-26",
                    dict(a=_q(a, "-"), b=_q(b, "-"), c=_q(c, "-")),
                    dict(offset_gauss=_q(subpixel_peak(a, b, c, "gauss"), "px"),
                         offset_para=_q(subpixel_peak(a, b, c, "para"), "px"))))
    for dx, dy in [(0.0, 0.0), (0.37, -0.21), (1.5, 0.75)]:
        im0 = render_cross(dx, dy, blur=0)
        V.append(_v(f"alignment.render_noblur.{dx}_{dy}", "alignment(합성 영상)", "render_cross (blur=0)",
                    f"{VS}:7-16",
                    dict(dx=_q(dx, "px"), dy=_q(dy, "px"), N=_q(128, "px"), arm=_q(60, "px"), w=_q(6, "px"),
                         bright=_q(220, "gray"), dark=_q(30, "gray")),
                    dict(sum=_q(float(im0.sum()), "gray"), px_64_64=_q(float(im0[64, 64]), "gray"),
                         px_67_64=_q(float(im0[67, 64]), "gray"), px_64_94=_q(float(im0[64, 94]), "gray"),
                         px_61_64=_q(float(im0[61, 64]), "gray")),
                    note="px_r_c = img[row r, col c]"))
    for dx, dy in [(0.0, 0.0), (0.37, -0.21), (-1.3, 1.8), (0.5, 0.5)]:
        cx, cy = measure_cross(render_cross(dx, dy))
        V.append(_v(f"alignment.measure.{dx}_{dy}", "alignment(NCC + 가우시안 보간)", "render_cross + measure_cross",
                    f"{VS}:7-29",
                    dict(dx=_q(dx, "px"), dy=_q(dy, "px"), blur=_q(1.0, "px"), noise=_q(0.0, "gray"),
                         method=_q("gauss", "-"), template=_q("render_cross(0,0,N=80)", "-")),
                    dict(cx=_q(cx, "px"), cy=_q(cy, "px"), err_x=_q(cx - dx, "px"), err_y=_q(cy - dy, "px")),
                    tol=dict(rel=0, abs=2e-4),
                    note="원본은 cv2 float32 연산. numpy float64 참조와 차이 ~1e-5 px 이하 (검증 스크립트 확인)"))
    A_t, b_t = affine_true()
    grid = np.array([[x, y] for x in np.linspace(-1500, 1500, 5) for y in np.linspace(-1200, 1200, 5)])
    P = np.array([np.linalg.solve(A_t, g - b_t) for g in grid])
    A_f, b_f, rot, sc = affine_fit(P, grid)
    p1 = np.linalg.solve(A_t, np.array([1000.0, 0.0]) - b_t)
    nom_err = float(np.linalg.norm(p1 * PX_UM - (np.array([1000.0, 0.0]) - b_t)))
    V.append(_v("alignment.affine_fit.noisefree", "alignment(아핀 캘리브레이션)", "affine_true + affine_fit",
                f"{VS}:61-74",
                dict(rot=_q(0.3, "deg"), scale_err=_q(0.002, "-"), shear=_q(0.0005, "-"), b=_q([12.0, -7.0], "um"),
                     grid=_q("5x5, x ±1500, y ±1200", "um"), noise=_q(0.0, "-")),
                dict(fit_rot=_q(rot, "deg"), fit_scale=_q(sc, "um/px"), A=_q(A_f.tolist(), "um/px"),
                     b=_q(b_f.tolist(), "um"), nominal_err_at_x1000=_q(nom_err, "um")),
                tol=dict(rel=1e-9, abs=1e-9)))
    for s1, n in [(0.0148376851138047, 4), (0.0148376851138047, 2), (0.05, 4)]:
        V.append(_v(f"alignment.angle_sigma.s{s1}_n{n}", "alignment(각도)", "angle_sigma_deg", f"{VS}:94-96",
                    dict(per_mark_sigma=_q(s1, "um"), L=_q(4000.0, "um"), n_marks=_q(n, "-")),
                    dict(sigma=_q(angle_sigma_deg(s1, 4000.0, n), "deg"))))
    # --- error budget
    for name, T in [("budget", BUDGET_TERMS), ("typical", TYPICAL_TERMS), ("conservative", CONSERVATIVE_TERMS)]:
        s = rss_sigma(T)
        V.append(_v(f"alignment.rss.{name}", "alignment(정합 오차 예산 RSS)", "sigma_of / rss_sigma",
                    "calc/error_budget.py:7-23; calc/integration.py:7-24",
                    dict(terms=_q([list(x) for x in T], "um (n: sigma, u: half-width)")),
                    dict(rss_sigma=_q(s, "um"), rss_3s=_q(3 * s, "um"))))
    # --- drive
    DC = "calc/drive_calc.py"
    for name, kw in [("coarseY", dict(m=6.0, lead=5, d=12, L=250, eta=0.9, a=1.0, v=50, mu=0.005, Jm=3.0e-6, Ca=4000)),
                     ("coarseX", dict(m=10.0, lead=5, d=12, L=350, eta=0.9, a=1.0, v=50, mu=0.005, Jm=3.0e-6, Ca=4000)),
                     ("Z", dict(m=2.5, lead=2, d=12, L=150, eta=0.9, a=0.5, v=20, mu=0.0, Fext=100.0, vertical=True,
                                Jm=3.0e-6, Ca=3000))]:
        r = ballscrew(**kw)
        units = dict(m="kg", lead="mm", d="mm", L="mm", eta="-", a="m/s^2", v="mm/s", mu="-", Fext="N",
                     vertical="bool", Jm="kg*m^2", Ca="N")
        V.append(_v(f"cycle.ballscrew.{name}", "cycle(구동축 사양)", "ballscrew", f"{DC}:3-30",
                    {k2: _q(v2, units[k2]) for k2, v2 in kw.items()},
                    dict(F_peak=_q(r["F_peak_N"], "N"), T_peak=_q(r["T_load_Nm"] + r["T_acc_Nm"], "N*m"),
                         T_hold=_q(r["T_hold_Nm"], "N*m"), rpm_max=_q(r["rpm_max"], "rpm"),
                         n_crit=_q(r["n_crit_rpm"], "rpm"), P_buckle=_q(r["P_buckle_N"], "N"))))
    for k, Fm in [(2.0, 5.5), (50.0, 55.0)]:
        r = leaf_flexure(k, Fm)
        V.append(_v(f"control.leaf_flexure.k{k}", "control(판스프링 강성)", "leaf_flexure", f"{DC}:45-50",
                    dict(k=_q(k, "N/mm"), Fmax=_q(Fm, "N"), E=_q(200e3, "MPa"), b=_q(20.0, "mm"), L=_q(25.0, "mm")),
                    dict(t=_q(r["t_mm"], "mm"), defl=_q(r["defl_mm"], "mm"), stress=_q(r["stress_MPa"], "MPa"))))
    return V


def verify_original_json(calc_dir):
    """원본 결과 JSON 재현 확인 (같은 시드 난수 순서까지 따라 한다)."""
    import os
    ok = True

    def close(a, b, tol=1e-9):
        return a is None and b is None or (a is not None and b is not None and math.isclose(a, b, rel_tol=tol, abs_tol=1e-12))

    def chk(label, a, b, tol=1e-9):
        nonlocal ok
        good = close(a, b, tol)
        ok &= good
        print(("OK  " if good else "FAIL"), label, a, b)
    th = json.load(open(os.path.join(calc_dir, "thermal.json")))
    r = head_sim(T_set=400, t_end=300, Kp=1e6, Ki=0)
    hm = head_heatup_metrics(r)
    for k in hm:
        chk("thermal.heater." + k, hm[k], th["heater"][k])
    chk("thermal.C_tip", r["C_tip"], th["heater"]["C_tip_J_per_K"])
    rc = head_sim(T_set=400, t_end=400, Kp=1e6, Ki=0, cool_at=300, air_h=400)
    chk("thermal.cooling", head_cooling_time_s(rc, 300), th["cooling"]["t_400_to_100_s"])
    rc0 = head_sim(T_set=400, t_end=700, Kp=1e6, Ki=0, cool_at=300, air_h=0)
    chk("thermal.cooling_natural", head_cooling_time_s(rc0, 300), th["cooling_natural_s"])
    md = macor_drift_metrics(r, hm["t_to_400_s"])
    chk("thermal.drift.wait", md["wait_after_setpoint_s"], th["drift"]["wait_after_setpoint_s"])
    for w, v in md["drift_um_per_s_at"].items():
        chk("thermal.drift.rate" + w, v, th["drift"]["drift_um_per_s_at"][w])
    chk("thermal.drift.tau", md["macor_tau_s"], th["drift"]["macor_tau_s"])
    for name, k, t in [("MACOR 6 mm", 1.46, 0.006), ("규산칼슘 보드 10 mm", 0.12, 0.010), ("규산칼슘 보드 15 mm", 0.12, 0.015)]:
        chk("thermal.chuck." + name, conduction_Q_W(k, 0.11 * 0.11, t, 180.0), th["chuck"][name]["Q_W"])
    cp = coolplate_rise(th["coolplate"]["Q_W"])
    for k in cp:
        chk("thermal.coolplate." + k, cp[k], th["coolplate"][k])
    pp = json.load(open(os.path.join(calc_dir, "process_physics.json")))
    for row in pp["squeeze_t_to_25um"]:
        chk(f"pp.t25 a{row['die']} F{row['F']}", round(squeeze_time_to_m(25e-6, row["F"], row["die"]), 2), row["t25"])
    for Ea, d in pp["cure_t95_min"].items():
        for T, v in d.items():
            chk(f"pp.cure Ea{Ea} T{T}", round(cure_time_to_s(0.95, float(T), float(Ea) * 1e3) / 60, 1), v)
    lo = dispense_volume_for_fillet_mm3(5, 25, 0.2, 0.3); hi = dispense_volume_for_fillet_mm3(5, 25, 0.5, 0.3)
    chk("pp.V_min", round(lo, 3), pp["fillet_5mm_300um"]["V_min_mm3"]); chk("pp.V_max", round(hi, 3), pp["fillet_5mm_300um"]["V_max_mm3"])
    chk("pp.V_window", round(100 * (hi - lo) / lo, 1), pp["fillet_5mm_300um"]["V_window_pct"])
    tdie = np.linspace(0.1e-3, 0.725e-3, 40)
    for name, sub, key in (("FR-4", FR4, "FR-4"), ("유리", GLASS, "유리")):
        for Tc in (150, 180):
            w = np.array([warp_sagitta_m(timoshenko_curvature_1_m(t, SI[0], SI[1], 0.4e-3, sub[0], sub[1], Tc - 25), 10e-3) * 1e6 for t in tdie])
            ref = pp["warp_10mm_um"][f"{key}_{Tc}C"]
            chk(f"pp.warp {key} {Tc} t100", round(float(w[0]), 2), ref["t100"])
            chk(f"pp.warp {key} {Tc} t300", round(float(np.interp(0.3e-3, tdie, w)), 2), ref["t300"])
            chk(f"pp.warp {key} {Tc} t725", round(float(w[-1]), 2), ref["t725"])
    ed = json.load(open(os.path.join(calc_dir, "education_calc.json")))
    for row in ed["doe"]:
        r = doe_predict(row["T"], row["F"], row["t"], row["V"])
        chk(f"edu.doe{row['run']}.BLT", round(r["BLT_um"], 1), row["BLT_um"])
        chk(f"edu.doe{row['run']}.fillet", round(r["fillet_pct"], 0), row["fillet_pct"])
        chk(f"edu.doe{row['run']}.warp", round(r["warp_5mm_um"], 1), row["warp_5mm_um"])
    for mu, lab in ((0.8, "25C"), (0.1, "90C")):
        for L in (5, 10):
            for h in (30, 50):
                chk(f"edu.underfill {lab} L{L} h{h}", round(washburn_fill_time_s(mu, L * 1e-3, h * 1e-6), 1),
                    ed["underfill_s"][f"{lab}_L{L}_gap{h}"])
    for row in ed["force_limit_N"]:
        for mode in ("epoxy", "epoxy_thin", "tcb"):
            chk(f"edu.force_limit a{row['die']} {mode}", force_limit_N(row["die"], mode), row[mode])
    # control.json: 원본과 같은 시드 3 난수열을 같은 순서로 소비
    co = json.load(open(os.path.join(calc_dir, "control.json")))
    rng = np.random.default_rng(3)
    for name, k, Ft, Ts, therm in [("저레인지 1 N, 1 ms", 2.0, 1.0, 1e-3, 0), ("고레인지 20 N, 1 ms", 50.0, 20.0, 1e-3, 0),
                                    ("고레인지 20 N, 10 ms", 50.0, 20.0, 10e-3, 0),
                                    ("고레인지 20 N, 1 ms, 헤드 열팽창", 50.0, 20.0, 1e-3, 2.6e-3)]:
        r = force_sim(k, Ft, Ts=Ts, therm=therm, Ki=force_gains(k)[1], rng=rng)
        chk("control.force." + name + ".overshoot", r["overshoot"], co["force"][name]["overshoot_N"])
        chk("control.force." + name + ".ss_err", r["ss_err"], co["force"][name]["ss_err_N"])
    for name, Ts in [("10 ms 루프 (원문 요구)", 10e-3), ("100 ms 루프 (비교)", 100e-3)]:
        tt, TT, ss, PPw = temp_sim(Ts=Ts, rng=rng)
        m = temp_metrics(tt, TT, PPw)
        for k in m:
            chk("control.temp." + name + "." + k, m[k], co["temperature"][name][k])
    rng = np.random.default_rng(3)
    if "contact_transient_N" in co:
        for Ts, lab in ((1e-3, "1 ms"), (10e-3, "10 ms")):
            for ap, al in ((0.02, "20 μm/s"), (0.2, "200 μm/s"), (0.5, "500 μm/s")):
                r = force_sim(50.0, 5.0, Ts=Ts, approach=ap, Ki=force_gains(50.0)[1], t_end=4.0, rng=rng)
                chk(f"control.contact {lab} {al}", round(contact_peak_N(r), 3), co["contact_transient_N"][lab][al])
    vi = json.load(open(os.path.join(calc_dir, "vision.json")))
    chk("vision.angle 4marks", angle_sigma_deg(vi["angle"]["per_mark_sigma_um"], 4000, 4), vi["angle"]["sigma_deg_4marks"])
    chk("vision.angle 2marks", angle_sigma_deg(vi["angle"]["per_mark_sigma_um"], 4000, 2), vi["angle"]["sigma_deg_2marks"])
    eb = json.load(open(os.path.join(calc_dir, "error_budget.json")))
    chk("budget.rss", rss_sigma(BUDGET_TERMS), eb["rss_sigma"])
    ig = json.load(open(os.path.join(calc_dir, "integration.json")))
    chk("integration.typical.rss", rss_sigma(TYPICAL_TERMS), ig["typical"]["rss_sigma"])
    chk("integration.conservative.rss", rss_sigma(CONSERVATIVE_TERMS), ig["conservative"]["rss_sigma"])
    print("ALL OK" if ok else "SOME FAILED")
    return ok


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--verify-json":
        sys.exit(0 if verify_original_json(sys.argv[2]) else 1)
    out_path = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "sim" / "test" / "golden_vectors.json"
    vecs = build_golden()
    doc = dict(
        meta=dict(
            title="MSE489 교육용 본더 계산 모델 golden vectors (JS 포팅 대조용)",
            generator="reference_models.py (__main__)",
            source_root="중간보고서/02_설계보고서_작업/",
            python=sys.version.split()[0], numpy=np.__version__,
            tolerance_rule="|js - ref| <= abs + rel*|ref| (항목별 tolerance 사용)",
            notes=["노이즈가 들어가는 원본 계산(하중·온도 루프, 비전 MC)은 난수열이 JS 와 다르므로 noise=0 조건으로 만들었다.",
                   "inputs/output 의 각 값은 {value, unit}.",
                   "source 는 원본 calc 폴더 기준 파일:줄 번호."],
            n_vectors=len(vecs)),
        vectors=vecs)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print(f"wrote {len(vecs)} vectors -> {out_path}")
