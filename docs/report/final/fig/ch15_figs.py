"""저장된 단계4 결과만 읽어 기말 15장 그림을 재생성한다."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
fonts = {f.name for f in font_manager.fontManager.ttflist}
plt.rcParams['font.family'] = next((f for f in ['Noto Sans CJK KR', 'Apple SD Gothic Neo', 'AppleGothic'] if f in fonts), 'sans-serif')
plt.rcParams['axes.unicode_minus'] = False
s = json.loads((REPO/'sim/test/stage4_results.json').read_text())
sc = {x['id']: x['results'] for x in s['representative']}
rows = json.loads((REPO/'sim/test/scenario_results.json').read_text())['results']
def save(fig, name):
    fig.savefig(HERE/name, dpi=180, bbox_inches='tight'); plt.close(fig)
def main():
    fig, axs = plt.subplots(3, 1, figsize=(9, 9), constrained_layout=True)
    labels = ['TC-NCF 기본', 'TC-NCF 헤드 보정', 'MR-MUF']
    for ax, r, label in zip(axs, sc['S1'], labels):
        hist=r['thermal']['history']; n=r['recipe']['layers']
        for i in range(n):
            ax.plot([h['t_s'] for h in hist], [h['T'][i] if i<len(h['T']) and h['T'][i] is not None else np.nan for h in hist], lw=.8, color=plt.cm.tab20(i), label=f'{i+1}층')
        ax.axhline(r['thermal_layers'][0]['liquidus_C'],ls='--',color='black',lw=.8,label='액상선')
        ax.set(title=label,ylabel='다이 중심 온도 (℃)',xlabel='시간 (s)');ax.grid(alpha=.2)
    axs[0].legend(ncol=7,fontsize=7,loc='lower center',bbox_to_anchor=(.5,1.15))
    save(fig,'ch15_thermal.png')
    fig, ax=plt.subplots(figsize=(8,4.2))
    for mode in ['TC-NCF','MR-MUF']:
        for thick in [100,50]:
            rr=sorted([r for r in rows if r['recipe']['mode']==mode and r['recipe']['thickness_um']==thick],key=lambda r:r['recipe']['layers'])
            ax.plot([r['recipe']['layers'] for r in rr],[r['warpage']['max_um'] for r in rr],marker='o',label=f'{mode} / {thick} μm')
    ax.set(xlabel='층수',ylabel='전 공정 최대 절대 휨 (μm)',title='저층 공정 최대가 지배하여 층수별 최대값이 같음');ax.legend(fontsize=8);ax.grid(alpha=.2)
    save(fig,'ch15_warpage.png')
    gaps=sorted({r['recipe']['gap_um'] for r in sc['S5']});ps=sorted({r['recipe']['inlet_pressure_MPa'] for r in sc['S5']})
    fig,axs=plt.subplots(1,2,figsize=(10,4),constrained_layout=True)
    for ax,key,title in zip(axs,['fill_time_s','defect_area_pct'],['충전 시간 (s)','미충전 면적률 (%)']):
        z=np.array([[next((r['muf'][key] if key=='fill_time_s' else r[key]) for r in sc['S5'] if r['recipe']['gap_um']==g and r['recipe']['inlet_pressure_MPa']==p) for p in ps] for g in gaps])
        im=ax.imshow(np.log10(z+1) if key=='fill_time_s' else z,cmap='YlOrRd',aspect='auto')
        for i in range(len(gaps)):
            for j in range(len(ps)):
                rgb=im.cmap(im.norm(im.get_array()[i,j]))[:3]
                ink='white' if sum(rgb)/3 < .5 else 'black'
                ax.text(j,i,f'{z[i,j]:.3g}',ha='center',va='center',fontsize=9,color=ink)
        ax.set(xticks=range(len(ps)),xticklabels=ps,yticks=range(len(gaps)),yticklabels=gaps,xlabel='입구 유효 압력 (MPa)',ylabel='간격 (μm)',title=title+(' / 색: log10(t+1)' if key=='fill_time_s' else ''))
    save(fig,'ch15_s5.png')
    fig,axs=plt.subplots(1,2,figsize=(10,4),constrained_layout=True)
    for ax,kind,title in zip(axs,['layer_totals','once'],['본더 점유 시간','배치 후공정 시간']):
        keys=list(dict.fromkeys(k for r in sc['S4'] for k in r['cycle']['breakdown'][kind]));left=np.zeros(2)
        for key in keys:
            v=[r['cycle']['breakdown'][kind].get(key,0) for r in sc['S4']]
            ax.barh(['TC-NCF','MR-MUF'],width=v,left=left,label=key.removesuffix('_s'));left+=v
        ax.set(title=title,xlabel='시간 (s)');ax.legend(fontsize=7,loc='upper center',bbox_to_anchor=(.5,-.18),ncol=3)
    save(fig,'ch15_cycle.png')
if __name__=='__main__': main()
