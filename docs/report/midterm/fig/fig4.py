import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
plt.rcParams["font.family"]="Noto Sans CJK JP"
fig,a=plt.subplots(figsize=(10,7.5))
layers=[ # (name, height, width, color, note)
("콜렛 툴",10,70,"#f4b183","교체식(다이 크기별), 진공 흡착, 툴 면 평탄도 ≤ 1 μm"),
("AlN 세라믹 히터 + K형 열전대",12,110,"#f08a6b","최고 400 ℃, ≥ 20 K/s, 공랭 노즐로 냉각"),
("MACOR 단열 블록",16,110,"#ffffff","압축 하중만 받도록 설계, 나사는 인서트"),
("수냉 재킷",12,116,"#9fd0f0","상부 부품 온도 상승 ≤ 0.5 K 목표"),
("잠금형 짐벌 (구면 시트 + 공압 클램프)",16,124,"#d5c4e6","레벨링 후 잠금, 평행도 ≤ 2 μm/10 mm"),
("로드셀 100 N",16,116,"#b4d7a8","24 bit ADC 2 kSPS, 1 ms 하중 루프"),
("판스프링 플렉셔 (교체식 2종)",18,124,"#ffe699","저: 2 N/mm (0.2–5 N) / 고: 50 N/mm (2–50 N), XY 강성 확보"),
("θ 회전 스테이지 (크로스 롤러)",16,124,"#e8d9f0","±5°, 0.001°, 축 하중 지지"),
("Z 캐리지 (볼스크류 2 mm + AC 서보)",24,130,"#e8d9f0","행정 60 mm, 0.1 μm 분해능, 저속 접근"),
]
y=0
for n,h,w,c,note in layers:
    a.add_patch(Rectangle((-w/2,y),w,h,fc=c,ec="#333",lw=1))
    a.text(0,y+h/2,n,ha="center",va="center",fontsize=8)
    a.annotate(note,(w/2,y+h/2),(80,y+h/2),fontsize=8,va="center",arrowprops=dict(arrowstyle="-",lw=.5,color="#666"))
    y+=h
a.add_patch(Rectangle((-10,-3),20,3,fc="#999",ec="#333")); a.text(0,-8,"다이",ha="center",fontsize=8)
a.annotate("",(-100,0),(-100,y),arrowprops=dict(arrowstyle="->",lw=1.2,color="#c00"))
a.text(-106,y/2,"하중 경로\n(Z → θ → 스프링\n→ 로드셀 → 짐벌\n→ 단열 → 히터 → 다이)",ha="right",va="center",fontsize=8,color="#c00")
a.annotate("",(-80,y-60),(-80,10),arrowprops=dict(arrowstyle="->",lw=1.2,color="#e67e22"))
a.text(-80,y-50,"열 흐름\n(재킷에서 차단)",ha="center",va="center",fontsize=7.5,color="#e67e22")
a.set_xlim(-200,260); a.set_ylim(-15,y+8); a.set_aspect("equal"); a.axis("off")
a.set_title("본딩 헤드 적층 구조 (개념 단면, 축척 없음)",fontsize=11)
plt.tight_layout(); plt.savefig("fig4_head.png",dpi=200,bbox_inches="tight")
