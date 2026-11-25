"""4장 공정 물리 모델: 스퀴즈 유동(BLT), 도포량-필렛, 경화 반응, 휨, 기울기-BLT 편차."""
import numpy as np, json
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"]="Noto Sans CJK JP"; plt.rcParams["axes.unicode_minus"]=False
out={}

# ---------- 1) Squeeze flow (Stefan) : BLT vs time ----------
# Newtonian, disk of equal area (R = a/sqrt(pi)).  F = 3*pi*mu*R^4/(2 h^3) * (-dh/dt)
# -> 1/h^2 = 1/h0^2 + 4 F t / (3 pi mu R^4)
mu=20.0        # Pa.s, Ag-filled epoxy (assumption, datasheet range 10-40)
h0=150e-6      # initial dot height after dispensing (assumption)
h_fill=15e-6   # filler-limited minimum BLT (Ag flake ~10-20 um, assumption)
def h_t(F,a_mm,t,mu=mu):
    R=a_mm*1e-3/np.sqrt(np.pi)
    h=1/np.sqrt(1/h0**2+4*F*t/(3*np.pi*mu*R**4))
    return np.maximum(h,h_fill)
def t_to(hT,F,a_mm,mu=mu):
    R=a_mm*1e-3/np.sqrt(np.pi)
    return (1/hT**2-1/h0**2)*3*np.pi*mu*R**4/(4*F)
tab=[]
for a in (2,5,10):
    for F in (0.2,1,5,20):
        p=F/(a*a)  # MPa
        tab.append(dict(die=a,F=F,p_MPa=round(p,3),t25=round(float(t_to(25e-6,F,a)),2)))
out["squeeze_t_to_25um"]=tab

# ---------- 2) dispensed volume -> BLT + fillet ----------
# V = A*BLT + V_fillet ; fillet = 45-deg triangular bead around perimeter: V_f = 4a * h_f^2/2
def fillet_h(V_nl,a_mm,blt_um):
    A=a_mm**2; Vf=V_nl - A*blt_um*1e-3   # mm^3 (1 nl = 1e-3 mm^3? no: 1 nl = 1e-3 mm^3? -> 1 mm^3 = 1 ul = 1000 nl)
    return np.sqrt(np.maximum(Vf,0)/(2*a_mm))  # mm
# use V in mm^3
def fillet_h_mm3(V,a,blt_um):
    Vf=V-a*a*blt_um*1e-3
    return np.sqrt(np.maximum(Vf,0)/(2*a)), Vf
a=5.0; t_die=0.3
V_need_lo=a*a*25e-3+2*a*(0.2*t_die)**2; V_need_hi=a*a*25e-3+2*a*(0.5*t_die)**2
out["fillet_5mm_300um"]=dict(V_min_mm3=round(V_need_lo,3),V_max_mm3=round(V_need_hi,3),
     V_window_pct=round(100*(V_need_hi-V_need_lo)/V_need_lo,1))

# ---------- 3) cure kinetics (1st order Arrhenius, anchored 180C/30min -> 95%) ----------
Rg=8.314
def k_of(T,Ea): kref=-np.log(0.05)/(30*60); return kref*np.exp(-Ea/Rg*(1/(T+273.15)-1/(180+273.15)))
cure={}
for Ea in (60e3,80e3,100e3):
    cure[int(Ea/1e3)]={T:round(float(-np.log(0.05)/k_of(T,Ea)/60),1) for T in (120,150,180,200)}
out["cure_t95_min"]=cure

# ---------- 4) warpage: Si die on substrate (Timoshenko bimaterial), stress-free at cure T ----------
def timo(h1,E1,a1,h2,E2,a2,dT):
    m=h1/h2; n=E1/E2; h=h1+h2
    return 6*(a2-a1)*dT*(1+m)**2/(h*(3*(1+m)**2+(1+m*n)*(m**2+1/(m*n))))
Si=(130e9,2.6e-6); FR4=(22e9,16e-6); GL=(64e9,3.3e-6)
L=10e-3; hs=0.4e-3
tdie=np.linspace(0.1e-3,0.725e-3,40)
warp={}
for name,sub in (("FR-4",FR4),("유리",GL)):
    for Tc in (150,180):
        k=np.array([timo(t,Si[0],Si[1],hs,sub[0],sub[1],Tc-25) for t in tdie])
        warp[(name,Tc)]=k*L**2/8*1e6   # um
out["warp_10mm_um"]={f"{k[0]}_{k[1]}C":{"t100":round(float(v[0]),2),"t300":round(float(np.interp(0.3e-3,tdie,v)),2),"t725":round(float(v[-1]),2)} for k,v in warp.items()}

# ---------- 5) tilt -> BLT variation ----------
out["tilt_blt"]={f"{d}mm":round(2.0/10*d,2) for d in (2,5,10)}  # um, at 2 um/10 mm parallelism

json.dump(out,open("calc/process_physics.json","w"),ensure_ascii=False,indent=1)

# ---------- figure ----------
fig,ax=plt.subplots(2,2,figsize=(11,7.6))
t=np.logspace(-1,3,300)
for F,c in ((0.2,"#9ecae1"),(1,"#4292c6"),(5,"#08519c"),(20,"#08306b")):
    ax[0,0].plot(t,h_t(F,5,t)*1e6,color=c,label=f"5×5 mm, {F} N")
ax[0,0].plot(t,h_t(5,10,t)*1e6,"--",color="#d94801",label="10×10 mm, 5 N")
ax[0,0].axhline(25,color="gray",lw=.8,ls=":"); ax[0,0].text(150,28,"목표 BLT 25 μm",fontsize=8,color="gray")
ax[0,0].set_xscale("log"); ax[0,0].set_xlabel("가압 유지 시간 (s)"); ax[0,0].set_ylabel("BLT (μm)")
ax[0,0].set_title("(a) 하중·시간 → BLT (스퀴즈 유동, μ = 20 Pa·s)",fontsize=10); ax[0,0].legend(fontsize=7.5); ax[0,0].set_ylim(0,160)
V=np.linspace(0.4,1.6,200)
for blt,c in ((15,"#41ab5d"),(25,"#238b45"),(40,"#00441b")):
    hf,_=fillet_h_mm3(V,5,blt); ax[0,1].plot(V,hf/t_die*100,color=c,label=f"BLT {blt} μm")
ax[0,1].axhspan(20,50,color="#fee391",alpha=.5); ax[0,1].text(0.42,35,"목표 필렛 20~50 %",fontsize=8)
ax[0,1].set_xlabel("도포량 (mm³)"); ax[0,1].set_ylabel("필렛 높이 / 다이 두께 (%)")
ax[0,1].set_title("(b) 도포량 → 필렛 (5×5 mm, 두께 300 μm)",fontsize=10); ax[0,1].legend(fontsize=7.5); ax[0,1].set_ylim(0,100)
tm=np.linspace(0,150,400)
for T,c in ((120,"#fdae6b"),(150,"#f16913"),(180,"#d94801"),(200,"#7f2704")):
    ax[1,0].plot(tm,100*(1-np.exp(-k_of(T,80e3)*tm*60)),color=c,label=f"{T} ℃")
ax[1,0].axhline(95,color="gray",lw=.8,ls=":"); ax[1,0].set_xlabel("시간 (min)"); ax[1,0].set_ylabel("경화도 (%)")
ax[1,0].set_title("(c) 온도·시간 → 경화도 (180 ℃·30 min = 95 % 기준, Ea 80 kJ/mol)",fontsize=10); ax[1,0].legend(fontsize=7.5)
for (name,Tc),v in warp.items():
    ax[1,1].plot(tdie*1e3,v,("-" if name=="FR-4" else "--"),color=("#cb181d" if Tc==180 else "#fb6a4a"),label=f"{name} 기판, 경화 {Tc} ℃")
ax[1,1].set_xlabel("다이 두께 (mm)"); ax[1,1].set_ylabel("10 mm 길이 휨 (μm)")
ax[1,1].set_title("(d) 다이 두께·경화 온도 → 휨 (기판 0.4 mm)",fontsize=10); ax[1,1].legend(fontsize=7.5)
for a_ in ax.flat: a_.grid(alpha=.3)
fig.tight_layout(); fig.savefig("fig/fig4_process.png",dpi=150)
print(json.dumps(out,ensure_ascii=False,indent=1))
