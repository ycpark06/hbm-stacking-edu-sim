import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams["font.family"]="Noto Sans CJK JP"
fig,a=plt.subplots(figsize=(15,9.5)); a.axis("off"); a.set_xlim(0,150); a.set_ylim(0,95)
P={}
def box(k,x,y,w,h,t,c="#f2f2f2",fs=8.2):
    a.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.3,rounding_size=0.8",fc=c,ec="#444",lw=.9))
    a.text(x+w/2,y+h/2,t,ha="center",va="center",fontsize=fs); P[k]=(x,y,w,h)
def grp(x,y,w,h,t,c):
    a.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.5",fc=c,ec="#999",lw=.8,ls="--")); a.text(x+1,y+h-1.5,t,fontsize=9.5,weight="bold",va="top")
def arr(k1,k2,side1="r",side2="l",t="",c="#333",ls="-",dy1=0,dy2=0):
    x1,y1,w1,h1=P[k1]; x2,y2,w2,h2=P[k2]
    p1={"r":(x1+w1+.3,y1+h1/2+dy1),"l":(x1-.3,y1+h1/2+dy1),"t":(x1+w1/2,y1+h1+.3),"b":(x1+w1/2,y1-.3)}[side1]
    p2={"r":(x2+w2+.3,y2+h2/2+dy2),"l":(x2-.3,y2+h2/2+dy2),"t":(x2+w2/2,y2+h2+.3),"b":(x2+w2/2,y2-.3)}[side2]
    a.annotate("",p2,p1,arrowprops=dict(arrowstyle="->",lw=.9,color=c,ls=ls,shrinkA=0,shrinkB=0))
    if t: a.text((p1[0]+p2[0])/2,(p1[1]+p2[1])/2+0.8,t,fontsize=7.2,ha="center",color=c)
grp(1,5,30,86,"센서","#eef5ff"); grp(40,52,44,39,"상위 PC (Python · OpenCV)","#f3fbef"); grp(40,5,44,44,"실시간 제어기 (STM32H7)","#fff7e8"); grp(93,5,30,86,"구동기","#fbeff5")
S=[("cam","듀얼 비전 · 측면 · 하부 카메라"),("laser","레이저 변위센서\n높이 · 휨 · BLT"),("vs","진공 · 냉각수 유량 센서"),("mpg","MPG 핸드휠 0.1/1/10 μm"),("enc","조동 엔코더 1 μm\n미동 정전용량 10 nm"),("lc","로드셀 100 N\n24 bit ADC 2 kSPS"),("tc","열전대 (툴 팁 · 척)\nAD8495 아날로그")]
for i,(k,t) in enumerate(S): box(k,3,80-i*11.3,26,7.5,t,"#ffffff")
box("vis",43,77,18,8,"피듀셜 NCC 검출\n+ 아핀 보정\n→ Δx · Δy · Δθ","#ffffff")
box("img",63,77,18,8,"보이드 면적 · 필렛\n언더필 유동 분석","#ffffff")
box("gui",43,60,38,8,"레시피 (구간 프로파일) · GUI · 로깅","#ffffff")
box("sm",43,37,38,7.5,"시퀀스 상태기계 · 모드 전환\n수동 / 자동 / 관찰 / KPI 검증","#ffffff")
box("mc",43,27,38,6.5,"모션 제어: 조동 → 미동 2단 위치결정","#ffffff")
box("fp",43,17.5,38,6,"하중 PID 1 ms","#ffffff"); box("tp",43,8,38,6,"온도 PID 10 ms","#ffffff")
A=[("dsp","디스펜서 · 스탬핑 · 진공 밸브"),("gas","N2 유량 · 짐벌 클램프"),("mxy","조동 XY 서보"),("pz","미동 XY 피에조 플렉셔"),("mt","θ 스테이지"),("mz","Z 서보 + 판스프링"),("ht","AlN 히터 PWM · 공랭 밸브"),("hb","척 히터 · 수냉 펌프")]
for i,(k,t) in enumerate(A): box(k,95,81-i*9.9,26,6.8,t,"#ffffff")
box("safe",126,40,23,22,"독립 안전 회로\n(하드웨어)\n\n비상정지 · 도어\n과하중 55 N\n과온 420 ℃\n냉각수 끊김\n→ 구동기 전원 차단","#ffe5e5",7.8)
arr("cam","vis","r","l"); arr("cam","img","r","t")
arr("laser","gui","r","l"); arr("vs","sm","r","l"); arr("mpg","mc","r","l",dy2=1.2); arr("enc","mc","r","l",dy2=-1.2)
arr("lc","fp","r","l"); arr("tc","tp","r","l")
arr("vis","gui","b","t"); arr("img","gui","b","t")
arr("gui","sm","b","t",c="#1f5fa8"); a.text(63,52,"보정량 · 레시피 ↓   로그 ↑",fontsize=7.4,color="#1f5fa8")
arr("sm","mc","b","t"); arr("sm","dsp","r","l"); arr("sm","gas","r","l")
arr("mc","mxy","r","l"); arr("mc","pz","r","l"); arr("mc","mt","r","l")
arr("fp","mz","r","l"); arr("tp","ht","r","l"); arr("tp","hb","r","l")
a.annotate("",(121.5,50),(126,50),arrowprops=dict(arrowstyle="->",ls="--",color="#c00"))
plt.savefig("fig1_control.png",dpi=180,bbox_inches="tight")
