import numpy as np, json
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"]="Noto Sans CJK JP"
rng=np.random.default_rng(3); out={}
# ================= FORCE LOOP =================
def force_sim(k_spring,F_target,Ts=1e-3,ramp=5.0,t_end=9.0,dt=1e-5,delay_s=0.5e-3,Kp=None,Ki=None,therm=0.0,approach=20e-3,noise=0.002):
    # units: mm, N, s. Servo position loop ~ 1st order tau 0.8 ms. Contact at z=0 (head moves down = +z here)
    k_c=2000.0   # die/substrate contact stiffness N/mm (very stiff vs spring)
    k_eff=1/(1/k_spring+1/k_c)
    if Kp is None: Kp=2*np.pi*20/k_eff     # loop crossover ~20 Hz
    if Ki is None: Ki=0.0
    tau=0.8e-3; z_cmd=-0.02; z=-0.02; I=0.0; v_cmd=approach
    mode="approach"; F_meas_hist=[]; t=0.0; n=int(t_end/dt); step=int(round(Ts/dt))
    buf=[0.0]*max(1,int(round(delay_s/dt)))
    T=[];F=[];SP=[]; t_contact=None; sp=0.0
    for i in range(n):
        x_th=therm*t   # thermal expansion pushes tool down (mm)
        F_true=max(0.0,k_eff*(z+x_th))
        buf.append(F_true); Fd=buf.pop(0)
        if i%step==0:
            Fm=Fd+rng.normal(0,noise)
            if mode=="approach":
                v_cmd=approach
                if Fm>0.1: mode="force"; t_contact=t; I=0.0
            if mode=="force":
                sp=min(F_target,0.1+ramp*(t-t_contact))
                e=sp-Fm; I+=e*Ts
                v_cmd=Kp*e+Ki*I
        z_cmd+=v_cmd*dt
        z+=(z_cmd-z)*dt/tau
        if i%100==0: T.append(t);F.append(F_true);SP.append(sp)
        t+=dt
    T=np.array(T);F=np.array(F);SP=np.array(SP)
    hold=(T>t_contact+F_target/ramp+0.5)
    return dict(t=T,F=F,sp=SP,t_contact=t_contact,overshoot=float(F.max()-F_target),ss_err=float(np.abs(F[hold]-F_target).max()) if hold.any() else None)
cases={}
for name,k,Ft,Ts,therm in [("저레인지 1 N, 1 ms",2.0,1.0,1e-3,0),("고레인지 20 N, 1 ms",50.0,20.0,1e-3,0),
                             ("고레인지 20 N, 10 ms",50.0,20.0,10e-3,0),("고레인지 20 N, 1 ms, 헤드 열팽창",50.0,20.0,1e-3,2.6e-3)]:
    Ki=None
    r=force_sim(k,Ft,Ts=Ts,therm=therm,Ki=(2*np.pi*20)*(2*np.pi*2)/(1/(1/k+1/2000)))
    spec=0.05+0.01*Ft if k==2.0 else 0.1+0.01*Ft
    cases[name]=dict(overshoot_N=r["overshoot"],ss_err_N=r["ss_err"],spec_N=spec,pass_=bool(r["overshoot"]<=spec and (r["ss_err"] or 0)<=spec)); cases[name]["_r"]=r
out["force"]={k:{kk:vv for kk,vv in v.items() if kk!="_r"} for k,v in cases.items()}
# ================= TEMPERATURE LOOP =================
def temp_sim(Ts=10e-3,profile=None,t_end=120,dt=1e-3,Kp=25.0,Ki=6.0,Kd=0.0,tc_tau=5e-3,P_max=400.0):
    C=8.77; Gm=0.146*2; A=0.0011; Tamb=20.0
    # tip + 3-node MACOR lumped
    Cm=2.52e3*790*0.04*0.04*0.016; nM=3; Tm=np.full(nM,Tamb); T=Tamb; Ttc=Tamb; I=0.0; P=0.0
    Gseg=1.46*0.0016/(0.016/nM)
    out_t=[];out_T=[];out_sp=[];out_P=[]; prev_e=0.0
    for i in range(int(t_end/dt)):
        t=i*dt; sp=profile(t)
        if i%int(round(Ts/dt))==0:
            e=sp-(Ttc+rng.normal(0,0.2)); I=np.clip(I+e*Ts,-30,30)
            P=float(np.clip(Kp*e+Ki*I+Kd*(e-prev_e)/Ts,0,P_max)); prev_e=e
            if P>=P_max or P<=0: I-=e*Ts   # anti-windup
        q_loss=(10*A*(T-Tamb)+0.3*5.67e-8*A*((T+273)**4-(Tamb+273)**4))
        q1=Gseg*2*(T-Tm[0])
        T+=dt*(P-q_loss-q1)/C
        q=np.zeros(nM); q[0]+=q1; fl=Gseg*(Tm[:-1]-Tm[1:]); q[:-1]-=fl; q[1:]+=fl; q[-1]-=Gseg*2*(Tm[-1]-Tamb)
        Tm+=dt*q/(Cm/nM)
        Ttc+=dt*(T-Ttc)/tc_tau
        if i%50==0: out_t.append(t);out_T.append(T);out_sp.append(sp);out_P.append(P)
    return np.array(out_t),np.array(out_T),np.array(out_sp),np.array(out_P)
prof=lambda t: 150.0 if t<40 else (min(300.0,150+20*(t-40)) if t<70 else 300.0)
res_T={}
for name,Ts,tau in [("10 ms 루프 (원문 요구)",10e-3,5e-3),("100 ms 루프 (비교)",100e-3,5e-3)]:
    tt,TT,ss,PP=temp_sim(Ts=Ts,profile=prof,tc_tau=tau)
    hold150=(tt>25)&(tt<40); hold300=(tt>55+10)&(tt<120)
    ramp_m=(tt>41)&(tt<47)
    res_T[name]=dict(t=tt,T=TT,sp=ss,P=PP,overshoot_C=float(TT[(tt>45)].max()-300),stab_150_C=float(np.abs(TT[hold150]-150).max()),
                     stab_300_C=float(np.abs(TT[hold300]-300).max()),ramp_K_s=float(np.polyfit(tt[ramp_m],TT[ramp_m],1)[0]),P_hold_W=float(PP[hold300].mean()))
out["temperature"]={k:{kk:vv for kk,vv in v.items() if kk not in("t","T","sp","P")} for k,v in res_T.items()}
print(json.dumps(out,ensure_ascii=False,indent=1))
json.dump(out,open("control.json","w"),ensure_ascii=False,indent=1)
# ================= FIGURE =================
fig,ax=plt.subplots(1,3,figsize=(15,4.3))
CT={"1 ms":[0.002,0.010,0.035],"10 ms":[0.052,0.088,0.131]}; sp_lab=["20","200","500"]
for j,(k,c) in enumerate([("1 ms","#3b6ea8"),("10 ms","#e08a3c")]):
    ax[0].bar([i+(j-0.5)*0.36 for i in range(3)],CT[k],0.36,color=c,label=f"하중 루프 {k}")
    for i,v in enumerate(CT[k]): ax[0].text(i+(j-0.5)*0.36,v+0.003,f"{v:.3f}",ha="center",fontsize=7)
ax[0].axhline(0.15,ls="--",color="#c0392b",lw=1); ax[0].text(-0.4,0.153,"5 N 설정 시 허용 오차 0.15 N",color="#c0392b",fontsize=8); ax[0].set_ylim(0,0.17)
ax[0].set_xticks(range(3)); ax[0].set_xticklabels([f"{x} μm/s" for x in sp_lab]); ax[0].set_xlabel("접촉 직전 접근 속도"); ax[0].set_ylabel("접촉 직후 하중 초과 (N)")
ax[0].set_title("(a) 접촉 순간 하중 초과 (5 N 목표)",fontsize=10); ax[0].legend(fontsize=8)
r=cases["고레인지 20 N, 1 ms, 헤드 열팽창"]["_r"]; m=r["t"]>r["t_contact"]+4.3
ax[1].plot(r["t"][m]-r["t_contact"],r["F"][m]-20,color="#5b8c5a",label="1 ms PI 루프 (열팽창 2.6 μm/s)")
ax[1].axhline(0.3,ls="--",color="#c0392b",lw=1); ax[1].axhline(-0.3,ls="--",color="#c0392b",lw=1); ax[1].text(4.4,0.31,"허용 ±0.3 N",color="#c0392b",fontsize=8)
ax[1].set_ylim(-0.4,0.4); ax[1].set_xlabel("접촉 후 시간 (s)"); ax[1].set_ylabel("하중 오차 (N)"); ax[1].set_title("(b) 유지 중 헤드 열팽창 외란",fontsize=10); ax[1].legend(fontsize=8)
for name,c in [("10 ms 루프 (원문 요구)","#c0392b"),("100 ms 루프 (비교)","#999")]:
    d=res_T[name]; ax[2].plot(d["t"],d["T"],color=c,label=name)
ax[2].plot(d["t"],d["sp"],"k--",lw=.8,label="설정 프로파일")
ax[2].set_xlabel("시간 (s)"); ax[2].set_ylabel("툴 온도 (℃)"); ax[2].set_title("(c) 온도 프로파일 추종 (150 → 300 ℃, 20 K/s)",fontsize=10); ax[2].legend(fontsize=7)
for a in ax: a.spines[["top","right"]].set_visible(False)
plt.tight_layout(); plt.savefig("../fig/fig10_control.png",dpi=180)
