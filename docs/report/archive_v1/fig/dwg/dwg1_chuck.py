from drafting import Sheet
s=Sheet("진공 척 (Vacuum Chuck)","MSE489-ST-004","A6061-T6","경질 아노다이징 (윗면 래핑)","0.47 kg",scale="1.3:1")
S=1.3
# TOP VIEW
ox,oy=40,128; W=100*S
s.label(ox+W/2,oy+W+16,"평면도")
s.rect(ox,oy,W,W)
for k in (1,2,3):  # vacuum grooves
    g=(46-12*k)*S; s.rect(ox+W/2-g,oy+W/2-g,2*g,2*g,lw=.6)
s.circ(ox+W/2,oy+W/2,7.5*S); s.center(ox+W/2-12*S,oy+W/2,ox+W/2+12*S,oy+W/2); s.center(ox+W/2,oy+W/2-12*S,ox+W/2,oy+W/2+12*S)
for dx in (-40,40):
    for dy in (-40,40):
        s.circ(ox+W/2+dx*S,oy+W/2+dy*S,2.25*S); s.circ(ox+W/2+dx*S,oy+W/2+dy*S,4*S,lw=.5,ls="--")
s.dim(ox,oy+W,ox+W,oy+W,"100 ±0.05",off=8)
s.dim(ox+W/2-40*S,oy,ox+W/2+40*S,oy,"80 ±0.02 (구멍 피치)",off=-10)
s.dim(ox+W,oy,ox+W,oy+W,"100 ±0.05",off=8,horiz=False)
s.leader(ox+W/2+5*S,oy+W/2+5*S,ox+W+22,oy+W-5,"Ø15 H7 (+0.018/0) 관통\n석영 창 끼움 (H7/g6)")
s.leader(ox+W/2+40*S+2,oy+W/2-40*S-2,ox+W+22,oy+18,"4 × Ø4.5 관통, 카운터보어 Ø8 깊이 4.5\n(M4 육각구멍붙이 볼트)")
s.leader(ox+W/2+34*S,oy+W/2,ox+W+22,oy+W/2+10,"진공 홈 3열 폭 1.0 × 깊이 0.5\n(동심 사각, 간격 12)")
# FRONT SECTION
fx,fy=40,50; H=18*S
s.label(fx+W/2,fy-24,"정면도 (A-A 단면)")
s.rect(fx,fy,W,H)
s.a.add_patch(__import__("matplotlib.patches",fromlist=["Rectangle"]).Rectangle((fx+W/2-7.5*S,fy),15*S,H,fc="white",ec="k",lw=1.1))
for xx in (fx+W/2-7.5*S,fx+W/2+7.5*S): s.line(xx,fy,xx,fy+H)
for k in range(0,int(W),6):
    x=fx+k
    if not (fx+W/2-7.5*S<x<fx+W/2+7.5*S): s.line(x,fy,min(x+H,fx+W),fy+min(H,fx+W-x),lw=.3,c="#777")
s.center(fx+W/2,fy-5,fx+W/2,fy+H+5)
# heater holes (side)
for yy in (fy+H/2,):
    for xx in (fx+18*S,fx+W-18*S): s.circ(xx,yy,3.25*S,lw=.8)
s.dim(fx+W,fy,fx+W,fy+H,"18 ±0.01",off=8,horiz=False)
s.leader(fx+18*S,fy+H/2,fx-2,fy-12,"2 × Ø6.5 H8 깊이 90 (카트리지 히터)")
s.leader(fx+W/2,fy+H*0.75,fx+W/2+28,fy-12,"측온공 Ø1.6 깊이 50 (열전대)")
# GD&T on top face
s.datum(fx+W*0.93,fy,"A")
s.rough(fx+W*0.25,fy+H,"Ra 0.4 (래핑)")
X=s.fcf(fx+W*0.42,fy+H+6,["FLAT","0.002"]); s.line(fx+W*0.5,fy+H+6,fx+W*0.5,fy+H,lw=.5)
s.fcf(fx+W*0.42,fy+H+13,["∥","0.005","A"])
s.fcf(fx+W+18,fy+H/2,["⊥","0.01","A"]); s.a.text(fx+W+18,fy+H/2+8,"측면 4곳",fontsize=6.8)
s.note(260,280,[
 "1. 윗면(본딩면)은 래핑 후 평면도 0.002 (2 μm): 툴–척 평행도 2 μm/10 mm 요구(2.4절)를 지키기 위함.",
 "2. 윗면은 바닥면(데이텀 A)에 평행도 0.005. 규산칼슘 단열판 위에 MACOR 스페이서 4점으로 지지.",
 "3. 석영 창 구멍 Ø15 H7, 창 외경 Ø15 g6 → 헐거운 끼워맞춤(틈새 6~34 μm) + 내열 접착제.",
 "   H7/g6는 '미끄럼'용이므로 위치결정이 아니라 조립성 확보에만 쓴다(PBL 8쪽 공차의 올바른 적용).",
 "4. 카트리지 히터 구멍 Ø6.5 H8: 히터 외경 Ø6.5 h7과 틈새 끼워맞춤, 열전달용 내열 페이스트 도포.",
 "5. 진공 홈은 중앙 창 둘레를 피해 배치, 측면 M5 진공 포트로 연결(도시 생략).",
 "6. 200 ℃ 사용 시 열팽창(23 ppm/K × 50 mm × 180 K = 0.21 mm)을 고려해 볼트 구멍은 Ø4.5 여유공.",
],fs=7.0)
s.save("dwg1_chuck.png")
