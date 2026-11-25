import numpy as np, json
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"]="Noto Sans CJK JP"
out={}
# ---------- materials ----------
AlN=dict(k=170,rho=3260,c=740,a=4.5e-6); MAC=dict(k=1.46,rho=2520,c=790,a=9.3e-6); ST=dict(k=16,rho=7900,c=500,a=17e-6)  # collet: stainless
Tamb=20.0
# ---------- 1) head: heater + collet lumped, MACOR 1D chain, water jacket boundary ----------
def head_sim(heater=(20,20,5),P_max=400.0,T_set=400.0,t_end=400.0,dt=0.005,cool_at=None,air_h=0.0,Kp=40.0,Ki=8.0,ramp=None):
    hx,hy,hz=[v/1000 for v in heater]
    V_h=hx*hy*hz; C_h=AlN["rho"]*V_h*AlN["c"]
    V_c=0.01*0.01*0.01; C_c=ST["rho"]*V_c*ST["c"]
    C_tip=C_h+C_c
    A_m=0.04*0.04; L_m=0.016; n=16; dx=L_m/n
    Cm=MAC["rho"]*A_m*dx*MAC["c"]; Gm=MAC["k"]*A_m/dx
    A_rad=2*(hx*hy)+2*(hx+hy)*hz+5*1e-4    # exposed heater+collet area
    h_nat=10.0
    T_tip=Tamb; Tm=np.full(n,Tamb); Tw=Tamb  # jacket held at water temp
    ts=[];Tt=[];Tmean=[];Pw=[];Q_j=[]; I=0.0
    t=0.0
    while t<t_end:
        sp=T_set if ramp is None else min(T_set,Tamb+ramp*t)
        if cool_at is not None and t>=cool_at: sp=None
        if sp is not None:
            e=sp-T_tip; I+=e*dt; I=np.clip(I,-50,50)
            P=np.clip(Kp*e+Ki*I,0,P_max)
        else: P=0.0
        h=h_nat+(air_h if (cool_at is not None and t>=cool_at) else 0.0)
        eps=0.3; sig=5.67e-8
        q_loss=h*A_rad*(T_tip-Tamb)+eps*sig*A_rad*((T_tip+273)**4-(Tamb+273)**4)
        q_m=Gm*2*(T_tip-Tm[0])   # half-cell to first node
        T_tip+=dt*(P-q_loss-q_m)/C_tip
        # MACOR chain
        qin=np.zeros(n); qin[0]+=q_m
        flux=Gm*(Tm[:-1]-Tm[1:]); qin[:-1]-=flux; qin[1:]+=flux
        q_out=Gm*2*(Tm[-1]-Tw); qin[-1]-=q_out
        Tm+=dt*qin/Cm
        if int(round(t/dt))%int(0.1/dt)==0:
            ts.append(t);Tt.append(T_tip);Tmean.append(Tm.mean());Pw.append(P);Q_j.append(q_out)
        t+=dt
    return dict(t=np.array(ts),T=np.array(Tt),Tm=np.array(Tmean),P=np.array(Pw),Qj=np.array(Q_j),C_tip=C_tip,G_mac=MAC["k"]*A_m/L_m)
# (a) open-loop capability: max ramp with 250 W
r=head_sim(T_set=400,t_end=300,Kp=1e6,Ki=0)   # bang-bang ~ full power until setpoint
i400=np.argmax(r["T"]>=399); t400=r["t"][i400]
out["heater"]=dict(size_mm=[20,20,5],C_tip_J_per_K=r["C_tip"],G_macor_W_per_K=r["G_mac"],P_max_W=400,
                   t_to_400_s=float(t400),avg_ramp_K_per_s=float((400-Tamb)/t400),
                   P_hold_400_W=float(np.mean(r["P"][-200:])),Q_jacket_steady_W=float(r["Qj"][-1]))
# (b) cooling 400 -> 100 with air jet h=150 W/m2K
rc=head_sim(T_set=400,t_end=400,Kp=1e6,Ki=0,cool_at=300,air_h=400)
m=rc["t"]>=300; tc=rc["t"][m]; Tc=rc["T"][m]; j=np.argmax(Tc<=100); out["cooling"]=dict(air_h=400,t_400_to_100_s=float(tc[j]-300) if Tc[j]<=100 else None)
rc0=head_sim(T_set=400,t_end=700,Kp=1e6,Ki=0,cool_at=300,air_h=0)
m0=rc0["t"]>=300; Tc0=rc0["T"][m0]; j0=np.argmax(Tc0<=100); out["cooling_natural_s"]=float(rc0["t"][m0][j0]-300) if Tc0[j0]<=100 else ">400"
# (c) drift: MACOR mean temperature rate after reaching setpoint
dTdt=np.gradient(r["Tm"],r["t"])
lim=0.28  # K/s -> 0.26 um in 5 s with 100% asymmetry over 20 mm half-width
after=r["t"]>t400; k=np.argmax((np.abs(dTdt)<lim)&after); t_wait=float(r["t"][k]-t400)
drift_rate_at=lambda tw: float(np.interp(t400+tw,r["t"],np.abs(dTdt))*MAC["a"]*0.020*1e6)  # um/s worst-case
out["drift"]=dict(limit_K_per_s=lim,wait_after_setpoint_s=t_wait,drift_um_per_s_at={str(w):drift_rate_at(w) for w in (0,10,30,60,120)},
                  macor_tau_s=float(MAC["rho"]*0.04*0.04*0.016*MAC["c"]/(2*r["G_mac"])))
# ---------- 2) chuck insulation & cooling plate ----------
A=0.11*0.11; dT=200-Tamb
for name,k,t in [("MACOR 6 mm",1.46,0.006),("규산칼슘 보드 10 mm",0.12,0.010),("규산칼슘 보드 15 mm",0.12,0.015)]:
    out.setdefault("chuck",{})[name]=dict(Q_W=k*A/t*dT)
Q=out["chuck"]["규산칼슘 보드 10 mm"]["Q_W"]
mdot=1.0/60  # kg/s (1 L/min)
h_ch=3000; A_ch=0.006
out["coolplate"]=dict(flow_L_min=1.0,Q_W=Q,water_rise_K=Q/(mdot*4180),film_dT_K=Q/(h_ch*A_ch),
                      plate_rise_open_loop_K=Q/(mdot*4180)/2+Q/(h_ch*A_ch))
# ---------- 3) Invar prism holder ----------
out["prism_holder"]={m:dict(alpha=a,um_per_K=a*0.020*1e6) for m,a in [("알루미늄 6061",23e-6),("스테인리스 304",17e-6),("인바 36",1.2e-6)]}
json.dump(out,open("thermal.json","w"),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False,indent=1))
# ---------- figures ----------
fig,ax=plt.subplots(1,3,figsize=(15,4.3))
ax[0].plot(r["t"],r["T"],color="#c0392b",label="툴 팁 (히터+콜렛)"); ax[0].plot(r["t"],r["Tm"],color="#3b6ea8",label="MACOR 평균")
ax[0].axhline(400,ls="--",color="#999",lw=.8); ax[0].set_xlim(0,120); ax[0].set_xlabel("시간 (s)"); ax[0].set_ylabel("온도 (℃)")
ax[0].set_title(f"(a) 승온: 400 W, 400 ℃ 도달 {t400:.1f} s",fontsize=10); ax[0].legend(fontsize=8)
ax[1].plot(tc-300,Tc,color="#c0392b",label="N2·공기 제트 h = 400 W/m²K"); ax[1].plot(rc0["t"][m0]-300,Tc0,color="#999",label="자연냉각")
ax[1].axhline(100,ls="--",color="#999",lw=.8); ax[1].set_xlim(0,200); ax[1].set_xlabel("냉각 시작 후 시간 (s)"); ax[1].set_ylabel("툴 팁 온도 (℃)")
ax[1].set_title(f"(b) 냉각 400→100 ℃: {out['cooling']['t_400_to_100_s']:.0f} s",fontsize=10); ax[1].legend(fontsize=8)
tt=r["t"]-t400; mm=tt>0
ax[2].semilogy(tt[mm],np.abs(dTdt[mm])*MAC["a"]*0.020*1e6*5,color="#5b8c5a")
ax[2].axhline(0.26,ls="--",color="#c0392b",lw=1); ax[2].text(150,0.3,"예산 0.26 μm / 5 s",color="#c0392b",fontsize=8)
ax[2].axvline(t_wait,ls=":",color="#333"); ax[2].text(t_wait+3,5,f"대기 {t_wait:.0f} s",fontsize=8)
ax[2].set_xlim(0,250); ax[2].set_xlabel("설정 온도 도달 후 시간 (s)"); ax[2].set_ylabel("5 s 동안 최대 드리프트 (μm)")
ax[2].set_title("(c) MACOR 열팽창 드리프트 (비대칭 100 % 가정)",fontsize=10)
for a in ax: a.spines[["top","right"]].set_visible(False)
plt.tight_layout(); plt.savefig("../fig/fig7_thermal.png",dpi=180)
