"""13장 교육·안전 계산: DoE 예측값, 언더필 모세관 유동 시간, 다이 크기별 하중 상한, 평행도 측정 불확도."""
import numpy as np, json, itertools, importlib.util, sys
spec=importlib.util.spec_from_file_location("pp","calc/process_physics.py")
# reuse model functions without re-running the figure: copy minimal formulas
mu=20.0; h0=150e-6; h_fill=15e-6
def h_t(F,a_mm,t):
    R=a_mm*1e-3/np.sqrt(np.pi); return max(1/np.sqrt(1/h0**2+4*F*t/(3*np.pi*mu*R**4)),h_fill)
def fillet_pct(V,a,blt_um,tdie=0.3):
    Vf=V-a*a*blt_um*1e-3; return 100*np.sqrt(max(Vf,0)/(2*a))/tdie
def timo(h1,E1,a1,h2,E2,a2,dT):
    m=h1/h2; n=E1/E2; h=h1+h2
    return 6*(a2-a1)*dT*(1+m)**2/(h*(3*(1+m)**2+(1+m*n)*(m**2+1/(m*n))))
out={}
# ---- 1) 2^(4-1) fractional factorial, D = ABC ----
lv=dict(T=(150,180),F=(0.5,2.0),t=(2,10),V=(0.66,0.80))
runs=[]
for a,b,c in itertools.product((-1,1),repeat=3):
    d=a*b*c
    T=lv["T"][a>0]; F=lv["F"][b>0]; t=lv["t"][c>0]; V=lv["V"][d>0]
    blt=h_t(F,5,t)*1e6
    fil=fillet_pct(V,5,blt)
    warp=timo(0.3e-3,130e9,2.6e-6,0.4e-3,22e9,16e-6,T-25)*(5e-3)**2/8*1e6
    runs.append(dict(run=len(runs)+1,T=T,F=F,t=t,V=V,BLT_um=round(blt,1),fillet_pct=round(fil,0),warp_5mm_um=round(warp,1)))
out["doe"]=runs
# ---- 2) capillary underfill flow time (Washburn, parallel plates): t = 3 mu L^2 / (gamma h cos th) ----
g=0.03; cth=np.cos(np.radians(40))
cap={}
for mu_u,lab in ((0.8,"25C"),(0.1,"90C")):
    for L in (5,10):
        for h in (30,50):
            cap[f"{lab}_L{L}_gap{h}"]=round(3*mu_u*(L*1e-3)**2/(g*h*1e-6*cth),1)
out["underfill_s"]=cap
# ---- 3) force limits by die size (operating limit, design target) ----
lim=[]
for a in (2,3,5,7,10):
    A=a*a
    lim.append(dict(die=a,epoxy=round(min(1.0*A,50),1),epoxy_thin=round(min(0.5*A,50),1),tcb=50.0 if a>=5 else round(min(2.0*A,50),1)))
out["force_limit_N"]=lim
# ---- 4) parallelism measurement uncertainty: plane fit, laser sigma 0.5 um, grid scan of 10x10 mm die ----
rng=np.random.default_rng(1); est=[]
xs=np.linspace(-5,5,15); X,Y=np.meshgrid(xs,xs); X=X.ravel(); Y=Y.ravel()
A=np.c_[X,Y,np.ones_like(X)]
for _ in range(5000):
    z=0.2*X/10*0+ rng.normal(0,0.5,X.size)   # true tilt 0, noise only
    c,*_=np.linalg.lstsq(A,z,rcond=None); est.append(np.hypot(c[0],c[1])*10)
out["parallel_meas"]=dict(points=int(X.size),laser_sigma_um=0.5,tilt_est_95pct_um_per_10mm=round(float(np.percentile(est,95)),3))
json.dump(out,open("calc/education_calc.json","w"),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False,indent=1))
