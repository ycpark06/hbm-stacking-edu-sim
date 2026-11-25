import numpy as np,cv2,sys,json
exec(open('vision.py').read().split('out={}')[0])
def run(label,blur=1.0,bright=220,dark=30,grad=0.0,sig=2,n=300):
    e=[]
    N=128; ramp=1+grad*(np.arange(N)/N-0.5)[None,:]
    for k in range(n):
        dx,dy=rng.uniform(-2,2,2); im=render(dx,dy,blur=blur,bright=bright,dark=dark)*ramp
        x,y,_=measure(noisy(im,sig,1)); e.append([x-dx,y-dy])
    e=np.array(e); r=float(np.sqrt((e**2).mean())); return dict(case=label,rms_px=r,rms_um=r*PX)
R=[run("기준 (블러 1 px, 대비 190, 노이즈 2)"),run("초점 이탈 (블러 2.5 px)",blur=2.5),run("저대비 (대비 50)",bright=120,dark=70),
   run("조명 기울기 ±10 %",grad=0.2),run("최악 복합 (블러 2.5, 대비 50, 기울기, 노이즈 4)",blur=2.5,bright=120,dark=70,grad=0.2,sig=4)]
for r in R: print(r)
json.dump(R,open('vision_robust.json','w'),ensure_ascii=False,indent=1)
R2=run("최악 복합 + 평탄화 보정 (기울기 제거)",blur=2.5,bright=120,dark=70,grad=0.0,sig=4)
print(R2); R.append(R2); json.dump(R,open('vision_robust.json','w'),ensure_ascii=False,indent=1)
