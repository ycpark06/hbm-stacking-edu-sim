import numpy as np, json
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"]="Noto Sans CJK JP"
rng=np.random.default_rng(1)
N=1_000_000
# (name, distribution, parameter) ; parameter = sigma for normal, half-width for uniform  [um, per axis]
terms=[
("비전 검출 (칩·기판 2채널)","n",0.10),
("정렬 수렴 잔차 (|Δ|≤0.15 μm)","u",0.15),
("광학 채널 오프셋 보정 잔차","n",0.10),
("미동 스테이지 위치결정","n",0.02),
("Z 하강 중 측면 비반복 변위","n",0.12),
("정렬→접합 사이 열드리프트","u",0.26),
("가압 변형 보정 잔차 (50 N)","u",0.12),
("접촉 시 다이 미끄러짐","n",0.12),
("바닥 진동","n",0.05),
]
def sig(d,p): return p if d=="n" else p/np.sqrt(3)
tot=np.zeros(N); rows=[]
for n,d,p in terms:
    x=rng.normal(0,p,N) if d=="n" else rng.uniform(-p,p,N)
    tot+=x; rows.append((n,"정규" if d=="n" else "균일",p,sig(d,p)))
s_rss=np.sqrt(sum(r[3]**2 for r in rows))
mc_sigma=tot.std(); p9973=np.percentile(np.abs(tot),99.73); within=np.mean(np.abs(tot)<=1.0)
res=dict(rss_sigma=s_rss,rss_3s=3*s_rss,mc_sigma=mc_sigma,mc_p9973=p9973,within_1um=within,
 rows=[dict(name=r[0],dist=r[1],param=r[2],sigma=r[3],share=r[3]**2/s_rss**2) for r in rows])
json.dump(res,open("calc/error_budget.json","w"),ensure_ascii=False,indent=1)
print(json.dumps(res,ensure_ascii=False,indent=1))
# figure
fig,ax=plt.subplots(1,2,figsize=(13,4.6))
srt=sorted(res["rows"],key=lambda r:r["share"])
ax[0].barh([r["name"] for r in srt],[r["share"]*100 for r in srt],color="#3b6ea8")
for i,r in enumerate(srt): ax[0].text(r["share"]*100+0.5,i,f'{r["share"]*100:.1f}% (σ {r["sigma"]:.3f})',va="center",fontsize=8)
ax[0].set_xlabel("분산 기여율 (%)"); ax[0].set_xlim(0,45); ax[0].set_title("(a) 항목별 분산 기여 (X축, 1σ)",fontsize=10)
ax[0].spines[["top","right"]].set_visible(False)
ax[1].hist(tot,bins=200,density=True,color="#9bb7d9")
for v in (-1,1): ax[1].axvline(v,color="#c0392b",ls="--",lw=1)
for v in (-p9973,p9973): ax[1].axvline(v,color="#333",ls=":",lw=1)
ax[1].text(1.02,ax[1].get_ylim()[1]*0.9,"KPI ±1 μm",color="#c0392b",fontsize=8)
ax[1].text(p9973+0.02,ax[1].get_ylim()[1]*0.6,f"99.73 %\n±{p9973:.2f} μm",fontsize=8)
ax[1].set_xlabel("본딩 후 배치 오차 X (μm)"); ax[1].set_yticks([]); ax[1].set_title(f"(b) 몬테카를로 {N:,}회 (σ = {mc_sigma:.3f} μm)",fontsize=10)
ax[1].spines[["top","right","left"]].set_visible(False)
plt.tight_layout(); plt.savefig("fig/fig5_budget.png",dpi=190)
