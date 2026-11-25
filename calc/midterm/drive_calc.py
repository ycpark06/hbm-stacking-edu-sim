import numpy as np, json
g=9.81; out={}
def ballscrew(name,m,lead,d,L,eta,a,v,mu,Fext=0.0,vertical=False,Jm=0.0,Ca=None,support=3.927,eta2=10.0):
    rho=7850; E=206e3
    Jscrew=np.pi*rho*(L/1000)*(d/1000)**4/32          # kg m2
    Jload=m*(lead/1000/(2*np.pi))**2
    alpha=2*np.pi*a/(lead/1000)                       # rad/s2
    Ffr=mu*m*g if not vertical else 0.0
    Fg=m*g if vertical else 0.0
    F=m*a+Ffr+Fg+Fext
    T_load=F*lead/1000/(2*np.pi*eta)
    T_acc=(Jscrew+Jm)*alpha
    T_peak=T_load+T_acc
    F_hold=Ffr+Fg+Fext
    T_hold=F_hold*lead/1000/(2*np.pi*eta)
    rpm=v/lead*60
    dr=d*0.83
    n_crit=support**2*60/(2*np.pi*(L/1000)**2)*np.sqrt(E*1e6*np.pi*(dr/1000)**4/64/(rho*np.pi*(dr/1000)**2/4))
    P_buck=eta2*dr**4/L**2*1e4                        # N (THK, fixed-supported eta2=10)
    life=None
    if Ca: life=(Ca/(1.2*max(F_hold,1)))**3*1e6*lead/1000/1000  # km
    r=dict(m_kg=m,lead_mm=lead,d_mm=d,L_mm=L,F_peak_N=F,T_load_Nm=T_load,T_acc_Nm=T_acc,T_peak_Nm=T_peak,
           T_hold_Nm=T_hold,J_screw=Jscrew,J_load=Jload,rpm_max=rpm,n_crit_rpm=n_crit,P_buckle_N=P_buck,
           life_km=life,res_per_rev_um=lead*1000)
    out[name]=r; return r
# Coarse X: carries Y stage + fine + chuck + camera ; Y: fine + chuck + camera + tray
Ycar=ballscrew("조동 Y",m=6.0,lead=5,d=12,L=250,eta=0.9,a=1.0,v=50,mu=0.005,Jm=3.0e-6,Ca=4000)
Xcar=ballscrew("조동 X",m=10.0,lead=5,d=12,L=350,eta=0.9,a=1.0,v=50,mu=0.005,Jm=3.0e-6,Ca=4000)
# Z: head 2.5 kg, design bonding force 100 N (2x 50 N)
Z=ballscrew("Z",m=2.5,lead=2,d=12,L=150,eta=0.9,a=0.5,v=20,mu=0.0,Fext=100.0,vertical=True,Jm=3.0e-6,Ca=3000)
# motor candidates
motors={"50 W AC 서보":dict(T_rated=0.16,T_peak=0.48,J=2.5e-6,rpm=3000),"100 W AC 서보":dict(T_rated=0.32,T_peak=0.95,J=5.1e-6,rpm=3000)}
sel={}
for ax,r in out.items():
    m=motors["50 W AC 서보"]
    sel[ax]=dict(motor="50 W AC 서보",SF_peak=m["T_peak"]/r["T_peak_Nm"],SF_rated=m["T_rated"]/r["T_hold_Nm"] if r["T_hold_Nm"]>0 else None,
                 inertia_ratio=(r["J_screw"]+r["J_load"])/m["J"],rpm_ok=r["rpm_max"]<min(m["rpm"],0.8*r["n_crit_rpm"]))
# Z resolution & force command resolution
Z_res_um=0.1; k_low=2.0; k_high=50.0  # N/mm
out["Z_force_cmd_res_mN"]={"low":k_low*Z_res_um*1e-3*1e3,"high":k_high*Z_res_um*1e-3*1e3}
# approach speed 20 um/s -> rpm
out["Z_approach_rpm"]=0.020/2*60
# theta: worm 180:1, stepper 200 x 16
th_res=360/(180*200*16); out["theta_res_deg"]=th_res
# flexure leaves: k = 4 E b t^3 / L^3 (two parallel planes, 4 guided leaves)
E=200e3; b=20; Lf=25
def leaf(k,Fmax):
    t=(k*Lf**3/(4*E*b))**(1/3); d=Fmax/k; s=3*E*t*d/Lf**2
    return dict(k_N_per_mm=k,t_mm=t,defl_mm=d,stress_MPa=s)
out["flexure_low"]=leaf(2.0,5.5); out["flexure_high"]=leaf(50.0,55.0)
# fine stage: piezo 100 um stroke, lever 10x
out["fine_stage"]=dict(stroke_um=100*10/2,lever=10)
res=dict(axes=out,selection=sel)
json.dump(res,open("calc/drive_calc.json","w"),ensure_ascii=False,indent=1,default=float)
for k,v in out.items(): print(k,v)
for k,v in sel.items(): print(k,v)
