from drafting import Sheet
s=Sheet("하중 판스프링 (교체식 2종)","MSE489-HD-003","SK85 스프링강, 담금질·뜨임 HV 450","와이어 컷 후 모서리 버 제거, 응력 제거 소둔","0.9 g / 2.6 g",scale="3:1")
S=3.0
# PLAN VIEW 45 x 20
ox,oy=40,170; L,B=45*S,20*S
s.label(ox+L/2,oy+B+24,"평면도"); s.rect(ox,oy,L,B)
s.center(ox-6,oy+B/2,ox+L+6,oy+B/2)
for xx in (5,40):
    s.center(ox+xx*S,oy-5,ox+xx*S,oy+B+5)
    for yy in (5,15): s.circ(ox+xx*S,oy+yy*S,1.6*S,lw=.8)
# clamp zones hatched boundary
for xx in (10,35): s.line(ox+xx*S,oy,ox+xx*S,oy+B,lw=.5,ls="--")
s.dim(ox,oy+B,ox+L,oy+B,"45 ±0.05",off=14)
s.dim(ox+10*S,oy+B,ox+35*S,oy+B,"25 ±0.02 (유효 길이 L)",off=6)
s.dim(ox+L,oy,ox+L,oy+B,"20 ±0.02 (폭 b)",off=10,horiz=False)
s.dim(ox,oy,ox+5*S,oy,"5",off=-8); s.dim(ox+5*S,oy,ox+40*S,oy,"35 ±0.01",off=-8)
s.leader(ox+40*S+1.6*S,oy+5*S,ox+L+18,oy-14,"4 × Ø3.2 H8 관통\n(클램프 다웰 Ø3 g6 + M3 체결)")
s.a.text(ox+2,oy+B+3,"클램프 영역",fontsize=6.5); s.a.text(ox+35*S+2,oy+B+3,"클램프 영역",fontsize=6.5)
s.fcf(ox,oy-26,["POS","Ø0.01","A"]); s.a.text(ox,oy-18,"구멍 4개 (기준 A = 판 면)",fontsize=6.8)
# EDGE VIEW (thickness exaggerated x10)
ex,ey=40,105
s.label(ex+L/2,ey+16,"측면도 (두께 방향 10배 과장)")
s.rect(ex,ey,L,0.37*S*10)
s.dim(ex+L,ey,ex+L,ey+0.37*S*10,"t (표 참조)",off=10,horiz=False)
s.datum(ex+L*0.3,ey,"A",dirn="down")
s.fcf(ex+L*0.55,ey-22,["FLAT","0.01"]); s.rough(ex+L*0.25,ey+0.37*S*10+3,"Ra 0.4")
# TABLE
tx,ty=245,240
rows=[["구분","두께 t","강성 k (4장)","정격 하중","최대 응력"],
      ["저 레인지 (HD-003-L)","0.125 ±0.003","2.0 N/mm ±7 %","0.2–5 N","330 MPa"],
      ["고 레인지 (HD-003-H)","0.37 ±0.005","51.9 N/mm ±4 %","2–50 N","386 MPa"]]
cw=[46,26,30,20,22]
for i,r in enumerate(rows):
    x=tx
    for j,c in enumerate(r):
        s.rect(x,ty-i*9,cw[j],9,lw=.6); s.a.text(x+cw[j]/2,ty-i*9+4.5,c,ha="center",va="center",fontsize=6.8,weight="bold" if i==0 else "normal"); x+=cw[j]
s.a.text(tx,ty+13,"치수표 (k = 4·E·b·t³ / L³, E = 200 GPa, b = 20, L = 25)",fontsize=7.4,weight="bold")
s.note(245,195,[
 "1. 4장을 두 평면에 2장씩, 양단 고정–안내 배치로 조립한다(6.5절).",
 "   같은 세트의 4장은 같은 소재 로트에서 잘라 두께 차 ≤ 0.002로 맞춘다.",
 "2. 강성 공차 ±4~7 %는 하중 정확도에 영향을 주지 않는다.",
 "   하중은 로드셀로 직접 재고(10장), 강성은 제어 이득에만 들어간다.",
 "   조립 후 세트별 k를 실측해 제어기 파라미터로 등록한다.",
 "3. 유효 길이 L은 클램프 블록 모서리가 정한다. 모서리 R ≤ 0.1.",
 "4. 열처리 후 가공(와이어 컷). 모서리 버가 남으면 피로 균열의 시작점이 된다.",
 "5. 안전율: 항복강도 1,000 MPa 이상 / 최대 응력 386 MPa → 2.5 이상.",
 "   과하중 스토퍼: 처짐 1.2 mm(고), 3 mm(저)에서 접촉.",
],fs=7.0)
s.save("dwg3_flexure.png")
