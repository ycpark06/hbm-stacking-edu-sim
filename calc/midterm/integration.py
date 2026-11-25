"""12장 통합 검증: 각 장 결과값으로 정합 오차 예산을 다시 합산 (설계 결과 기반)."""
import numpy as np, json
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"]="Noto Sans CJK JP"; plt.rcParams["axes.unicode_minus"]=False
rng=np.random.default_rng(2); N=1_000_000
# name, budget(dist,param), result-typical(dist,param,source), result-conservative(dist,param)
T=[
("#1 비전 검출",("n",0.10),("n",0.021,"9장 기준 조건"),("n",0.075,"9장 최악+평탄화")),
("#2 정렬 수렴",("u",0.15),("n",0.030,"9장 폐루프 5,000회"),("u",0.15,"판정 기준 그대로")),
("#3 광학 오프셋",("n",0.10),("n",0.048,"7장 인바 홀더"),("n",0.10,"예산 유지")),
("#4 미동 스테이지",("n",0.02),("n",0.02,"6장 센서 10 nm"),("n",0.02,"")),
("#5 Z 측면 비반복",("n",0.12),("n",0.10,"6장 가이드 사양 환산"),("n",0.12,"예산 유지")),
("#6 열드리프트",("u",0.26),("u",0.25,"7장 90 s 대기"),("u",0.26,"")),
("#7 가압 변형",("u",0.12),("u",0.055,"8장 v5, 편심 1 mm"),("u",0.20,"8장 v5, 편심 3.7 mm, 보정 없음")),
("#8 다이 미끄러짐",("n",0.12),("n",0.12,"모델 없음, 예산 유지"),("n",0.12,"")),
("#9 바닥 진동",("n",0.05),("n",0.05,"8장 177 Hz, 진폭은 예산 유지"),("n",0.05,"")),
]
def s(d,p): return p if d=="n" else p/np.sqrt(3)
def run(idx):
    tot=np.zeros(N); sig2=0
    for row in T:
        d,p=row[idx][0],row[idx][1]
        tot+= rng.normal(0,p,N) if d=="n" else rng.uniform(-p,p,N); sig2+=s(d,p)**2
    return dict(rss_sigma=float(np.sqrt(sig2)),rss_3s=float(3*np.sqrt(sig2)),mc_p9973=float(np.percentile(np.abs(tot),99.73)),within=float(np.mean(np.abs(tot)<=1))),tot
out={}; tots={}
for k,i in (("budget",1),("typical",2),("conservative",3)):
    out[k],tots[k]=run(i)
out["rows"]=[dict(item=r[0],budget=round(s(*r[1]),3),typical=round(s(r[2][0],r[2][1]),3),src=r[2][2],conservative=round(s(r[3][0],r[3][1]),3)) for r in T]
# sensitivity on conservative case: #8 doubled
T8=list(T); 
json.dump(out,open("calc/integration.json","w"),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False,indent=1))
fig,ax=plt.subplots(1,2,figsize=(12,4.4))
names=[r["item"] for r in out["rows"]]; y=np.arange(len(names))
ax[0].barh(y+0.25,[r["budget"] for r in out["rows"]],0.25,label="5장 배정 예산",color="#bdbdbd")
ax[0].barh(y,[r["conservative"] for r in out["rows"]],0.25,label="설계 결과 (보수)",color="#6baed6")
ax[0].barh(y-0.25,[r["typical"] for r in out["rows"]],0.25,label="설계 결과 (대표)",color="#08519c")
ax[0].set_yticks(y); ax[0].set_yticklabels(names,fontsize=8.5); ax[0].invert_yaxis(); ax[0].set_xlabel("1σ (μm)")
ax[0].set_title("(a) 항목별 예산과 설계 결과",fontsize=10); ax[0].legend(fontsize=8)
for k,c in (("budget","#969696"),("conservative","#6baed6"),("typical","#08519c")):
    h,b=np.histogram(tots[k],bins=300,range=(-1.2,1.2),density=True); ax[1].plot((b[1:]+b[:-1])/2,h,color=c,label=f'{ {"budget":"예산","conservative":"보수","typical":"대표"}[k]}: 3σ {out[k]["rss_3s"]:.2f} μm')
for v in (-1,1): ax[1].axvline(v,color="#c0392b",ls="--",lw=1)
ax[1].set_xlabel("본딩 후 배치 오차 X (μm)"); ax[1].set_title("(b) 몬테카를로 100만 회",fontsize=10); ax[1].legend(fontsize=8)
fig.tight_layout(); fig.savefig("fig/fig12_budget.png",dpi=150)
