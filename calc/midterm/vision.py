import numpy as np, cv2, json
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"]="Noto Sans CJK JP"
rng=np.random.default_rng(7)
PX=1.725   # um/px (3.45 um sensor, 2x telecentric)
SS=8       # supersampling
def render(dx,dy,N=128,arm=60,w=6,blur=1.0,bright=220,dark=30):
    # exact area coverage of the cross (two axis-aligned rectangles), pixel i spans [i,i+1) centred at i+0.5-N/2
    edges=np.arange(N+1)-N/2
    def ov(a0,a1):
        lo=np.maximum(edges[:-1],a0); hi=np.minimum(edges[1:],a1); return np.clip(hi-lo,0,1)
    hx,hy=ov(dx-arm/2,dx+arm/2),ov(dy-w/2,dy+w/2)      # horizontal bar
    vx,vy=ov(dx-w/2,dx+w/2),ov(dy-arm/2,dy+arm/2)      # vertical bar
    cx_,cy_=ov(dx-w/2,dx+w/2),ov(dy-w/2,dy+w/2)        # overlap square
    cov=np.outer(hy,hx)+np.outer(vy,vx)-np.outer(cy_,cx_)
    img=(bright-(bright-dark)*cov).astype(np.float32)
    if blur>0: img=cv2.GaussianBlur(img,(0,0),blur)
    return img
TPL=render(0,0,N=80)
METHOD="gauss"
def measure(img,frames=1):
    r=cv2.matchTemplate(img.astype(np.float32),TPL,cv2.TM_CCOEFF_NORMED)
    _,_,_,(px,py)=cv2.minMaxLoc(r)
    def para(a,b,c):
        if METHOD=="gauss" and min(a,b,c)>0: a,b,c=np.log(a),np.log(b),np.log(c)
        d=a-2*b+c; return 0.0 if d==0 else 0.5*(a-c)/d
    sx=para(r[py,px-1],r[py,px],r[py,px+1]); sy=para(r[py-1,px],r[py,px],r[py+1,px])
    cx=px+sx+TPL.shape[1]/2-img.shape[1]/2; cy=py+sy+TPL.shape[0]/2-img.shape[0]/2
    return cx,cy,r
def noisy(img,sig,frames=1):
    acc=np.zeros_like(img)
    for _ in range(frames): acc+=np.clip(np.round(img+rng.normal(0,sig,img.shape)),0,1023)
    return acc/frames
out={}
# 1) accuracy vs noise and frames: random subpixel positions, two subpixel methods
res=[]
for METHOD in ["para","gauss"]:
    for sig in [1,2,4,8]:
        for fr in [1,4]:
            err=[]
            for k in range(300):
                dx,dy=rng.uniform(-2,2,2)
                cx,cy,_=measure(noisy(render(dx,dy),sig,fr))
                err.append([cx-dx,cy-dy])
            e=np.array(err)
            rep=[]; base=render(0.37,-0.21)
            for k in range(200):
                cx,cy,_=measure(noisy(base,sig,fr)); rep.append([cx,cy])
            rep=np.array(rep)
            res.append(dict(method=METHOD,noise_gray=sig,frames=fr,SNR=190/sig,rms_err_px=float(np.sqrt((e**2).mean())),
                            repeat_sigma_px=float(rep.std(0).max()),total_sigma_um=float(np.sqrt((e**2).mean())*PX)))
METHOD="gauss"
out["detection"]=res
for r in res: print(r)
# pixel-locking bias curve
sub=np.linspace(-0.5,0.5,41); bias=[]
for s in sub:
    cx,cy,_=measure(render(s,0)); bias.append(cx-s)
out["pixel_locking_max_px"]=float(np.max(np.abs(bias)))
# 2) affine calibration
th=np.deg2rad(0.3); sc=PX*(1+0.002); shear=0.0005
A_true=np.array([[sc*np.cos(th),-sc*np.sin(th)+shear*PX],[sc*np.sin(th),sc*np.cos(th)]]); b_true=np.array([12.0,-7.0])
def stage_to_px(s): return np.linalg.solve(A_true,s-b_true)
grid=np.array([[x,y] for x in np.linspace(-1500,1500,5) for y in np.linspace(-1200,1200,5)])
sig_px=0.03
P=np.array([stage_to_px(g)+rng.normal(0,sig_px,2) for g in grid]); S=grid+rng.normal(0,0.01,grid.shape)
M=np.hstack([P,np.ones((len(P),1))]); coef,_,_,_=np.linalg.lstsq(M,S,rcond=None)
A_fit=coef[:2].T; b_fit=coef[2]
test=rng.uniform([-1800,-1500],[1800,1500],(500,2)); Ptest=np.array([stage_to_px(t) for t in test])
pred=Ptest@A_fit.T+b_fit; cal_err=np.linalg.norm(pred-test,axis=1)
nominal=Ptest*PX; nom_err=np.linalg.norm((nominal-(test-b_true)),axis=1)
out["affine"]=dict(true_rot_deg=0.3,true_scale_err=0.002,fit_rot_deg=float(np.rad2deg(np.arctan2(A_fit[1,0],A_fit[0,0]))),
    fit_scale_um_px=float(np.hypot(A_fit[0,0],A_fit[1,0])),cal_err_rms_um=float(np.sqrt((cal_err**2).mean())),
    nominal_err_at_1mm_um=float(np.median(nom_err[np.abs(np.linalg.norm(test,axis=1)-1000)<200])))
print(out["affine"])
# 3) closed-loop alignment simulation (die vs substrate, stage+theta)
sig_ch=[r for r in res if r["method"]=="gauss" and r["noise_gray"]==2 and r["frames"]==4][0]["total_sigma_um"]
def align_once():
    d=np.array([rng.uniform(-30,30),rng.uniform(-30,30)]); t=np.deg2rad(rng.uniform(-0.3,0.3))
    for it in range(1,4):
        meas=d+rng.normal(0,np.sqrt(2)*sig_ch,2); meas_t=t+rng.normal(0,np.deg2rad(0.0005))
        if np.all(np.abs(meas)<=0.15) and abs(np.rad2deg(meas_t))<=0.002: return d,t,it-1
        # command through calibrated mapping (residual mapping error 0.05%) + fine stage noise 0.02 um
        d=d-meas*(1+rng.normal(0,5e-4))+rng.normal(0,0.02,2); t=t-meas_t+np.deg2rad(rng.normal(0,0.0003))
    meas=d+rng.normal(0,np.sqrt(2)*sig_ch,2)
    return d,t,3
R=[align_once() for _ in range(5000)]
fin=np.array([r[0] for r in R]); its=np.array([r[2] for r in R]); tf=np.rad2deg(np.array([r[1] for r in R]))
out["closed_loop"]=dict(final_sigma_um=float(fin.std(0).max()),final_3sigma_um=float(3*fin.std(0).max()),
    pct_within_0p15=float(np.mean(np.all(np.abs(fin)<=0.15,1))*100),iter_hist={int(k):int((its==k).sum()) for k in range(4)},
    theta_3sigma_deg=float(3*tf.std()))
print(out["closed_loop"])
# angle from 4 fiducials, 4 frames
s1=sig_ch
L=4000.0
out["angle"]=dict(per_mark_sigma_um=s1,sigma_deg_2marks=float(np.rad2deg(np.sqrt(2)*np.sqrt(2)*s1/L)),sigma_deg_4marks=float(np.rad2deg(np.sqrt(2)*s1/L)))
json.dump(out,open("vision.json","w"),indent=1,ensure_ascii=False)
# ---------- figure ----------
fig=plt.figure(figsize=(15,4.4))
a1=fig.add_subplot(1,4,1); im=noisy(render(0.37,-0.21),2); a1.imshow(im,cmap="gray"); a1.set_title("(a) 합성 피듀셜 영상\n(1.73 μm/px, 노이즈 σ 2 계조)",fontsize=9); a1.axis("off")
a2=fig.add_subplot(1,4,2); _,_,r=measure(im); a2.imshow(r,cmap="viridis"); a2.set_title("(b) NCC 상관 맵",fontsize=9); a2.axis("off")
a3=fig.add_subplot(1,4,3)
for meth,fr,c,ls in [("para",1,"#e08a3c","--"),("gauss",1,"#3b6ea8","-"),("gauss",4,"#5b8c5a","-")]:
    rr=[x for x in res if x["frames"]==fr and x["method"]==meth]
    a3.plot([x["noise_gray"] for x in rr],[x["total_sigma_um"] for x in rr],"o"+ls,color=c,label=("포물선" if meth=="para" else "가우시안")+f" 보간, {fr}프레임")
a3.axhline(0.07,ls="--",color="#c0392b",lw=1); a3.text(1.05,0.066,"예산 0.07 μm/채널",color="#c0392b",fontsize=8)
a3.set_xscale("log",base=2); a3.set_xlabel("영상 노이즈 σ (계조, 대비 190)"); a3.set_ylabel("위치 오차 RMS (μm)"); a3.set_title("(c) 서브픽셀 검출 정확도",fontsize=9); a3.legend(fontsize=8)
a4=fig.add_subplot(1,4,4); a4.hist(fin[:,0],bins=60,color="#5b8c5a")
for v in (-0.15,0.15): a4.axvline(v,ls="--",color="#c0392b",lw=1)
a4.set_xlabel("정렬 후 잔차 X (μm)"); a4.set_title(f"(d) 폐루프 정렬 5,000회\n3σ = {out['closed_loop']['final_3sigma_um']:.2f} μm",fontsize=9); a4.set_yticks([])
for a in (a3,a4): a.spines[["top","right"]].set_visible(False)
plt.tight_layout(); plt.savefig("../fig/fig9_vision.png",dpi=180)
