"""기존 JSON의 저장값만 다시 그린다. 모델 실행·입력 변경 없음.
실행: /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 make_figs.py
"""
from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parent / '.mplconfig'))
import json, hashlib, argparse
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt, font_manager, ticker
import numpy as np

HERE = Path(__file__).resolve().parent
DEFAULT_REPO = HERE.parents[2]
NAVY, ORANGE, GRAY, GRID = '#14365A', '#C2622A', '#44505F', '#E6ECF3'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=DEFAULT_REPO)
    repo=parser.parse_args().repo
    # 사용자 설치 OFL 글꼴을 등록한 뒤 지정한 순서로 대체한다.
    for path in sorted((Path.home()/'Library/Fonts').glob('Pretendard-*.otf')):
        font_manager.fontManager.addfont(str(path))
    apple=Path('/System/Library/Fonts/AppleSDGothicNeo.ttc')
    if apple.exists(): font_manager.fontManager.addfont(str(apple))
    available={f.name for f in font_manager.fontManager.ttflist}
    font=next(f for f in ['Pretendard','Malgun Gothic','Apple SD Gothic Neo'] if f in available)
    plt.rcParams.update({'font.family':font,'font.size':14,'axes.labelsize':14,
                        'xtick.labelsize':14,'ytick.labelsize':14,'axes.titlesize':15,
                        'axes.unicode_minus':False,'text.color':GRAY,'axes.labelcolor':GRAY,
                        'xtick.color':GRAY,'ytick.color':GRAY,'figure.facecolor':'white',
                        'axes.facecolor':'white','savefig.facecolor':'white'})
    src=repo/'sim/test/stage4_results.json'
    raw=src.read_bytes(); data=json.loads(raw)
    scenes={s['id']:s for s in data['representative']}
    base,comp,_=scenes['S1']['results']
    b=[l['bond_peak_C'] for l in base['thermal_layers']]
    c=[l['bond_peak_C'] for l in comp['thermal_layers']]
    liquidus=base['thermal_layers'][0]['liquidus_C']
    assert len(b)==len(c)==12 and [i+1 for i,v in enumerate(b) if v<liquidus]==[1,2]
    assert all(l['bond_temp_ok'] for l in comp['thermal_layers'])
    # 같은 기본·보정 값이 별도 접합 온도 검증 JSON에도 저장되어 있는지 확인.
    bond_path=repo/'sim/test/bond_temp_results.json'
    bond=json.loads(bond_path.read_bytes())
    for i,r in enumerate([base,comp]):
        assert [x['bond_peak_C'] for x in r['thermal_layers']]==[x['bond_peak_C'] for x in bond['S1'][i]['thermal_layers']]
    (HERE/'fig').mkdir(exist_ok=True)
    fig,axs=plt.subplots(1,2,figsize=(10,4.7),sharey=True)
    fig.subplots_adjust(left=.07,right=.99,bottom=.18,top=.78,wspace=.13)
    x=np.arange(1,13)
    for ax,vals,title in zip(axs,[b,c],['보정 전 · 기본','보정 후 · 선택 실행']):
        ax.bar(x, vals, color=[ORANGE if v<liquidus else NAVY for v in vals],width=.73,zorder=3)
        ax.axhline(liquidus,c=GRAY,ls=(0,(4,3)),lw=1.4,zorder=4)
        ax.set(xticks=x,xlim=(.3,12.7),ylim=(0,275),yticks=[0,100,221],title=title)
        ax.title.set_fontsize(19)
        ax.title.set_position((.5,1.05))
        ax.grid(axis='y',color=GRID,zorder=0)
        ax.spines[['top','right']].set_visible(False)
        ax.spines[['left','bottom']].set_color(GRID)
        ax.tick_params(axis='x',length=0,labelsize=14)
        ax.tick_params(axis='y',labelsize=16)
        ax.text(12.2,max(vals)+5,'221 ℃ 기준선',ha='right',va='bottom',
                fontsize=16,color=GRAY,zorder=5)
    # 세로축 제목은 회전 없이 그림 위에 가로 한 줄로 둔다.
    fig.text(.07,.95,'층별 최고 온도 (℃)',ha='left',va='top',fontsize=19)
    axs[0].text(.6,266,'1·2층 미달',color=ORANGE,fontsize=18,va='top')
    axs[1].text(.6,266,'전 층 약 231 ℃',color=NAVY,fontsize=18,va='top')
    fig.text(.53,.04,'층 번호 · 1층이 맨 아래',ha='center',fontsize=18)
    fig.savefig(HERE/'fig/fig_trouble_v2.png',dpi=240);plt.close(fig)
    s5=scenes['S5']['results']; gaps=sorted({r['recipe']['gap_um'] for r in s5})
    selected=[]
    fig,ax=plt.subplots(figsize=(7,3.7))
    fig.subplots_adjust(left=.16,right=.96,bottom=.23,top=.80)
    for pressure,color,marker,label in [(0,ORANGE,'o','모세관 단독 · 0 MPa'),(1,NAVY,'s','가압 + 모세관 · 1 MPa')]:
        rows=sorted([r for r in s5 if r['recipe']['inlet_pressure_MPa']==pressure],key=lambda r:r['recipe']['gap_um'])
        assert [r['recipe']['gap_um'] for r in rows]==gaps
        vals=[r['muf']['fill_time_s'] for r in rows]
        ax.plot(gaps,vals,color=color,marker=marker,lw=2.2,ms=8,label=label,zorder=3)
        for r in rows:
            selected.append({'gap_um':r['recipe']['gap_um'],'inlet_pressure_MPa':pressure,
                             'fill_time_s':r['muf']['fill_time_s'], 'unfilled_fraction':r['muf']['unfilled_fraction'],
                             'judgement':r['defect_judgement']})
    ax.axhline(10,c=GRAY,ls=(0,(5,3)),lw=1.4,zorder=2)
    ax.text(20.2,10,'10 s',fontsize=14,va='center',ha='right',backgroundcolor='white')
    ax.set(yscale='log',ylim=(1,4000),xlim=(6,21),xticks=gaps,xlabel='층간 간격 (μm)',ylabel='충전 완료 시간 (s · 로그축)')
    ax.yaxis.set_major_locator(ticker.FixedLocator([1,10,100,1000]))
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:g}'))
    ax.yaxis.set_minor_locator(ticker.NullLocator())
    ax.grid(axis='y',color=GRID); ax.spines[['top','right']].set_visible(False)
    ax.spines[['left','bottom']].set_color(GRID)
    ax.legend(loc='lower left',bbox_to_anchor=(-.10,1.02),frameon=False,fontsize=14,borderaxespad=0)
    fig.savefig(HERE/'fig/fig_result.png',dpi=240);plt.close(fig)
    evidence={'source':str(src.relative_to(repo)),'sha256':hashlib.sha256(raw).hexdigest(),'font':font,
              'S1':{'selector':'representative[id=S1].results[0:2]','recipe':base['recipe'],
                    'base_bond_peak_C':b,'comp_bond_peak_C':c,'liquidus_C':liquidus,
                    'comp_required_head_C':comp['head_setpoints_C']},
              'S5':{'selector':'representative[id=S5].results; inlet_pressure_MPa in [0,1]','rows':selected},
              'cross_check':{'source':str(bond_path.relative_to(repo)),'sha256':hashlib.sha256(bond_path.read_bytes()).hexdigest(),'S1_values_equal':True},
              'note':'저장값 재도식화. 표시 반올림 외 수치 생성·모델 재실행 없음. 두 그림 축·눈금 최소 14 pt. 문제 그림 세로축 제목은 가로 표시.'}
    (HERE/'fig/figure_sources.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    print('Generated fig_trouble_v2.png, fig_result.png, figure_sources.json; font:',font)

if __name__=='__main__':
    main()
    from figures_extra import main as extra
    extra()
