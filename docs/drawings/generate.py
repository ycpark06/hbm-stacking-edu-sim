"""A3 third-angle drawings from exact Fusion geometry; unresolved items clearly marked."""
from pathlib import Path
import importlib.util, json
import matplotlib.font_manager as fm
from drafting import Sheet, plt
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('stacker',ROOT/'cad/stacker/spec_stacker.py'); G=importlib.util.module_from_spec(s); s.loader.exec_module(G)
if not any(f.name=='Noto Sans CJK JP' for f in fm.fontManager.ttflist):
    print('FONT NOTICE: Noto Sans CJK JP unavailable; using Apple SD Gothic Neo')
    plt.rcParams['font.family']='Apple SD Gothic Neo'
plt.rcParams['pdf.fonttype']=42

def save(sheet,name):
    sheet.fig.savefig(HERE/(name+'.png'),dpi=150)
    sheet.fig.savefig(HERE/(name+'.pdf'))
    plt.close(sheet.fig)
def specs(sheet,lines):
    sheet.note(250,275,lines,fs=7,title='제작 주기 / 설계 검토 (단위 mm)')
    sheet.a.text(12,281,'설계 검토용 · 계산 FAIL/REVIEW 해소 및 조립 시험 전 제작 승인 아님',fontsize=8,color='#a33')
def plate(key,c,title,no):
    sheet=Sheet(title,no,G.MATERIALS[key],'윗면 래핑 / 기타 버 제거','참고값',scale='1:1' if c['w']==100 else '3:1')
    scale=1 if c['w']==100 else 3
    x,y=35,140; w,d,t=[c[k]*scale for k in ('w','d','t')]
    sheet.rect(x,y,w,d); sheet.label(x+w/2,y+d+14,'평면도')
    pitch=c['pitch']*scale
    for dx in (-pitch/2,pitch/2):
        for dy in (-pitch/2,pitch/2): sheet.circ(x+w/2+dx,y+d/2+dy,c['bolt']/2*scale)
    sheet.center(x+w/2,y-5,x+w/2,y+d+5); sheet.center(x-5,y+d/2,x+w+5,y+d/2)
    sheet.dim(x,y+d,x+w,y+d,f"{c['w']} ±{G.TOL['outline']}",off=9)
    sheet.dim(x+w,y,x+w,y+d,f"{c['d']} ±{G.TOL['outline']}",off=10,horiz=False)
    sheet.dim(x+w/2-pitch/2,y,x+w/2+pitch/2,y,f"{c['pitch']} ±0.02 구멍 피치",off=-12)
    fy=70; sheet.rect(x,fy,w,t); sheet.label(x+w/2,fy-22,'정면도 / 3각법')
    sheet.dim(x+w,fy,x+w,fy+t,f"{c['t']} ±{G.TOL['thickness']}",off=10,horiz=False)
    sheet.datum(x+10,fy,'A'); sheet.rough(x+10,fy+t,f"Ra {G.TOL['ra_top']}")
    sheet.fcf(170,117,['FLAT',str(c['flat'])]); sheet.fcf(170,105,['∥',str(G.TOL['parallel']),'A']); sheet.fcf(170,93,['⊥',str(G.TOL['perpendicular']),'A'])
    return sheet,(x,y,w,d,scale)

def stack():
    c=G.CHUCK; a,(x,y,w,d,k)=plate('stack_chuck',c,'적층 진공 척','HBM-ST-001')
    a.circ(x+w/2,y+d/2,c['window']/2)
    span=c['groove_span']; gw=c['groove_w']
    for off in (-gw/2,gw/2): a.rect(x+w/2-span/2+off,y+d/2-span/2+off,span-2*off,span-2*off,lw=.5)
    a.line(x+w/2,y+d/2+span/2,x+w/2,y+d)
    for dx in (-c['pin_pitch']/2,c['pin_pitch']/2): a.circ(x+w/2+dx,y+d/2,c['pin']/2)
    a.circ(x+w/2,y+d/2+30,c['pilot']/2)
    a.leader(x+w/2+5,y+d/2+5,170,236,f"Ø{c['window']} H7 관통\n창 Ø{c['window']} g6 × 길이 {c['t']}")
    a.leader(x+w/2-30,y+d/2,170,215,f"2×Ø{c['pin']} H7 / 다웰 m6\n피치 {c['pin_pitch']}, 중심선상")
    a.leader(x+w/2,y+d/2+30,170,192,f"Ø{c['pilot']} H7 / 기준 핀 h6\n중심에서 +Y 30")
    specs(a,[f"1. 외형 {c['w']}×{c['d']}×{c['t']}, 원점은 평면 중심.",f"2. 4×Ø{c['bolt']} 관통, XY ±{c['pitch']/2}.",f"3. 사각 진공 홈 중심선 {span}×{span}, 폭 {gw}, 깊이 {c['groove_depth']}.",
      '   +Y 중심 개방 홈은 외곽까지 연결; 상부 호스 어댑터 필요.',f"4. 중앙 Ø{c['window']} H7/g6 석영 창은 전체 두께 지지.",'   창-척 하중 전달 접착층/밀봉은 시험 필요, 무지지 다이 금지.',
      '5. 위치결정 H7/h6, 다웰 H7/m6, 창 조립 H7/g6.', '6. A=바닥, 윗면 평면도·평행도 / 측면 직각도는 좌측 공차틀.',
      '7. 소재 A6061-T6; 추가 열처리 없음. 래핑 후 Ra 0.4.', '8. 중간 11장 ST-004 확장, calc/hardware/load_path.json.', '9. 지지점 피치80/MACOR는 계산 가정. 조립 치구 별도 검토.'])
    save(a,'stack_chuck')
def reflow():
    c=G.REFLOW; a,(x,y,w,d,k)=plate('reflow_chuck',c,'리플로우 척 히터 플레이트','HBM-RF-001')
    a.circ(x+w/2,y+d/2,c['tc_d']/2*k)
    a.rect(x+(w-c['heater_w']*k)/2,y+(d-c['heater_w']*k)/2,c['heater_w']*k,c['heater_w']*k,ls='--')
    a.leader(x+w/2,y+d/2,180,230,f"Ø{c['tc_d']} 깊이 {c['tc_depth']}\n상부 열전대 맹공")
    specs(a,[f"1. 외형 {c['w']}×{c['d']}×{c['t']}; 4×Ø{c['bolt']} 관통.",f"2. 구멍 중심 XY ±{c['pitch']/2}, 피치 ±0.02.",f"3. 하부 AlN 히터 {c['heater_w']}×{c['heater_w']}×{c['heater_t']} (점선).",f"4. 규산칼슘 단열판 {c['w']}×{c['d']}×{c['ins_t']}.",
     '5. 히터 48 V /120 W (설계값). 250 ℃ 목표는 헤드400 ℃ KPI와 별도.', '6. 2 K/s 가능, 3 K/s 전력 부족. 자연냉각4 K/s 불가.', '7. 헤드와 동시 정격 사용620 W: 전원600 W 초과.', '   출력 금지 시퀀스 또는 전원 변경안 승인 후 제작.',
     '8. 소재 A6061-T6; 추가 열처리 없음, 고온 시효 변화 검토.', '9. 상부 래핑 Ra 0.4, 기타 Ra 1.6. A=바닥.', '10. 윗면 평면도/평행도, 측면 직각도는 좌측 공차틀.', '11. 고온 재정렬/미끄럼 체결 필요; 냉간 치수만 규정.', '12. calc/hardware/reflow_heater.json / thermal_expansion.json.'])
    save(a,'reflow_chuck')
def mold():
    m=G.MOLD; a=Sheet('가압 충전 지그 / 캐비티·플런저','HBM-MJ-001','SUS304','슬라이딩 면 연삭 / 부동태화','참고값',scale='3:1')
    k=3; x,y=35,150; W=m['w']*k; a.rect(x,y,W,W); a.label(x+W/2,y+W+14,'밑면도 (캐비티 개방면)')
    cx,cy=x+W/2,y+W/2; cw=m['cavity_w']*k; a.rect(cx-cw/2,cy-cw/2,cw,cw)
    bx=cx+(m['cavity_w']/2+m['gate_l'])*k
    a.circ(bx,cy,m['bore']/2*k); a.rect(cx+cw/2,cy-m['gate_w']*k/2,m['gate_l']*k,m['gate_w']*k)
    vl=(m['w']-m['cavity_w'])/2*k; a.rect(x,cy-m['vent_w']*k/2,vl,m['vent_w']*k)
    for dx in (-m['pitch']/2,m['pitch']/2):
        for dy in (-m['pitch']/2,m['pitch']/2): a.circ(cx+dx*k,cy+dy*k,m['bolt']/2*k)
    a.dim(x,y+W,x+W,y+W,f"{m['w']} ±0.05",off=8)
    a.dim(x+W,y,x+W,y+W,f"{m['d']} ±0.05",off=9,horiz=False)
    a.leader(cx,cy,165,249,f"캐비티 {m['cavity_w']}×{m['cavity_w']}\n깊이 {m['cavity_d']} ±0.02")
    a.leader(bx,cy,165,220,f"Ø{m['bore']} H7 관통\n중심 X +{m['cavity_w']/2+m['gate_l']}, Y 0")
    a.leader(x+15,cy,165,192,f"진공 벤트 폭 {m['vent_w']}\n깊이 {m['vent_d']} ±0.005")
    # Section at Y=0, cavity and gate drawn as open steps; dimensions unexaggerated.
    fy=80; a.rect(x,fy,W,m['t']*k); a.rect(cx-cw/2,fy,cw,m['cavity_d']*k)
    a.rect(cx+cw/2,fy,m['gate_l']*k,m['gate_d']*k)
    a.line(bx-m['bore']/2*k,fy,bx-m['bore']/2*k,fy+m['t']*k); a.line(bx+m['bore']/2*k,fy,bx+m['bore']/2*k,fy+m['t']*k)
    a.label(cx,fy-18,'정면 단면 (Y=0)'); a.datum(x+8,fy,'A')
    a.dim(x+W,fy,x+W,fy+m['t']*k,f"{m['t']} ±0.01",off=9,horiz=False)
    px,py=192,69; a.rect(px,py,m['bore']*k,m['plunger_l']*k); a.label(px+6,py-10,'플런저')
    a.dim(px,py,px,py+m['plunger_l']*k,f"{m['plunger_l']} ±0.05",off=8,horiz=False)
    a.leader(px,py+35,164,144,f"Ø{m['bore']} g6\nRa {G.TOL['ra_slide']}")
    a.fcf(160,175,['FLAT','0.002']); a.fcf(160,165,['∥','0.005','A']); a.fcf(160,155,['⊥','0.01','A'])
    specs(a,[f"1. 4×Ø{m['bolt']} 관통, XY ±{m['pitch']/2}; M3 독립 체결 제안.",f"2. 게이트 폭{m['gate_w']}×깊이{m['gate_d']}×길이{m['gate_l']}.",f"3. Ø{m['bore']} H7: 4.000~4.012 / g6: 3.988~3.996.", '   냉간 직경 틈새 0.004~0.024; 수지 실링 기능은 없음.',f"4. 플런저 유효 스트로크 {m['stroke']}; 전체 길이 {m['plunger_l']}.",
     '5. 3 MPa 이상 하중37.70 N + 마찰예약5 N = 42.70 N.', '   50 N KPI 여유7.30 N, 52 N 경고 여유9.30 N.', '6. 캐비티 개방력108 N → Z축만 형체결 불가.', '   독립 체결 총예압216 N 이상은 제안값, 내압 시험 필요.',
     '7. A=캐비티 개방/밀봉면, 평면도0.002 / 평행도0.005.', '   보어 축 직각도0.01 A. 보어·축 Ra0.2, 밀봉면 Ra0.4.', '8. SUS304 용체화 소재; 추가 열처리 없음. 부동태화.', '9. 수지량/스트로크/누설 한계: calc/hardware/mold_jig.json.', '10. 플런저 가이드·씰·벤트 트랩 상세는 검토 대기.', '11. 독립클램프 내압 미검증으로 제작 승인 전 도면.'])
    save(a,'mold_jig')
if __name__=='__main__':
    stack(); reflow(); mold()
    (HERE/'dimensions.json').write_text(json.dumps(dict(source='cad/stacker/spec_stacker.py',stack=G.CHUCK,reflow=G.REFLOW,mold=G.MOLD,fit=G.FIT,tolerances=G.TOL),ensure_ascii=False,indent=2)+'\n')
    print('PASS: A3 drawings 3 PNG + 3 PDF; dimensions.json from shared spec')
