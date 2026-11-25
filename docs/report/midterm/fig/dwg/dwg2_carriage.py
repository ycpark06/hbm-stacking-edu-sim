from drafting import Sheet
from matplotlib.patches import Rectangle
s=Sheet("Z 캐리지 (헤드 장착 블록)","MSE489-HD-002","A6061-T6","경질 아노다이징, 기준면 연삭 후 처리","0.56 kg",scale="1.3:1")
S=1.3
# FRONT VIEW (X-Z): 70 x 74
ox,oy=35,165; W,H=70*S,74*S
s.label(ox+W/2,oy+H+16,"정면도"); s.rect(ox,oy,W,H)
s.center(ox+W/2,oy-6,ox+W/2,oy+H+6)
# ball nut bore top (hidden)
s.rect(ox+W/2-12*S,oy+H-12*S,24*S,12*S,lw=.6,ls="--")
# theta pilot bore bottom (hidden)
s.rect(ox+W/2-20*S,oy,40*S,6*S,lw=.6,ls="--")
s.dim(ox,oy+H,ox+W,oy+H,"70 ±0.01 (레일 간 맞춤폭)",off=8)
s.dim(ox+W,oy,ox+W,oy+H,"74",off=8,horiz=False)
s.datum(ox,oy+H*0.5-12,"B",dirn="down"); s.line(ox,oy+H*0.5-12,ox,oy+H*0.5-12,lw=0)
s.leader(ox+W/2+12*S,oy+H-6*S,ox+W+24,oy+H-4,"Ø24 H7 (+0.021/0) 깊이 12\n볼너트 플랜지 위치결정 (H7/h6)")
s.leader(ox+W/2+20*S,oy+3*S,ox+W+24,oy+10,"Ø40 H7 (+0.025/0) 깊이 6\nθ 스테이지 파일럿 (H7/h6)")
X=s.fcf(ox+W+6,oy+H*0.55,["∥","0.005","B"]); s.a.text(ox+W+6,oy+H*0.55+8,"우측면 (레일 장착면)",fontsize=6.8)
s.rough(ox-18,oy+H*0.7,"Ra 0.8")
# SIDE VIEW (Y-Z): 40 x 74
sx,sy=165,165; Wy=40*S
s.label(sx+Wy/2,sy+H+16,"우측면도"); s.rect(sx,sy,Wy,H)
for zz in (sy+14*S,sy+H-14*S):
    for yy in (sx+10*S,sx+Wy-10*S): s.circ(yy,zz,2.5*S,lw=.8)
for zz in (sy+H/2,):
    for yy in (sx+6*S,sx+Wy-6*S): s.circ(yy,zz,2*S,lw=.8)
s.dim(sx,sy+H,sx+Wy,sy+H,"40",off=8)
s.dim(sx+10*S,sy,sx+Wy-10*S,sy,"20 ±0.02",off=-8)
s.leader(sx+Wy-10*S,sy+H-14*S,sx+Wy+14,sy+H+6,"4 × M5 깊이 10\n(가이드 블록 체결, 양측면)")
s.leader(sx+Wy-6*S,sy+H/2,sx+Wy+14,sy+H/2-20,"2 × Ø4 H7 깊이 8\n다웰 핀 Ø4 m6 (H7/m6, 억지)")
s.fcf(sx+Wy+14,sy+8,["⊥","0.005","B"]); s.a.text(sx+Wy+14,sy+16,"윗면·아랫면",fontsize=6.8)
# BOTTOM VIEW
bx,by=35,62; Hb=40*S
s.label(bx+W/2,by-14,"저면도"); s.rect(bx,by,W,Hb)
s.circ(bx+W/2,by+Hb/2,20*S); s.circ(bx+W/2,by+Hb/2,7*S,lw=.6)
import math
for k in range(4):
    a=math.radians(45+90*k); s.circ(bx+W/2+26*S*math.cos(a)*0.55,by+Hb/2+26*S*math.sin(a)*0.55,1.7*S,lw=.7)
s.center(bx-5,by+Hb/2,bx+W+5,by+Hb/2); s.center(bx+W/2,by-5,bx+W/2,by+Hb+5)
s.leader(bx+W/2+10*S,by+Hb/2+10*S,bx+W+24,by+Hb-2,"4 × M4 깊이 8, PCD 28.6\n(θ 스테이지 체결)")
s.fcf(bx+W+24,by+10,["POS","Ø0.01","B"]); s.a.text(bx+W+24,by+18,"Ø40 H7 구멍 위치",fontsize=6.8)
s.note(255,255,[
 "1. 좌·우 측면은 Z 레일 가이드 블록 장착면. 서로 평행도 0.005, 맞춤폭 70 ±0.01.",
 "   레일 2개가 헤드 축 좌우 대칭으로 하중을 받는다(8장 v5 설계 원칙).",
 "2. 끼워맞춤 선정 (PBL 8쪽 'H7/g6'를 용도별로 구분해 적용)",
 "   · 위치결정 (볼너트 플랜지, θ 파일럿): H7/h6 — 틈새 0~34 μm, 분해 가능",
 "   · 고정 위치결정 (다웰 핀): H7/m6 — 억지, 재조립 시 반복위치 확보",
 "   · H7/g6(미끄럼)는 이 부품에 쓰지 않는다. 덜컥거림이 정합 오차가 되기 때문.",
 "3. 재질 A6061-T6: 가볍고(Z 관성 감소, 6장) 가공성이 좋다. 수냉 재킷 위쪽이라 온도 상승이 작다(7장).",
 "4. 윗면·아랫면은 측면 B에 직각도 0.005: 하중축 기울기 → 측면 변위 억제(8장).",
],fs=7.0)
s.save("dwg2_carriage.png")
