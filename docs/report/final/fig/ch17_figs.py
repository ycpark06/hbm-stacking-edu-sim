"""17장 비교 그림. 기존 결과와 wasm 기록을 읽고 GitHub 조회 이력을 저장한다.
재현: node docs/report/final/fig/ch17_force_data.mjs
      python3 docs/report/final/fig/ch17_figs.py [--refresh-history]
"""
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager, dates as mdates
import numpy as np
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
fonts={f.name for f in font_manager.fontManager.ttflist}
plt.rcParams.update({'font.family':next((f for f in ['Noto Sans CJK KR','Apple SD Gothic Neo','AppleGothic'] if f in fonts),'sans-serif'), 'axes.unicode_minus':False,'font.size':10})
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def save(fig,name):
    fig.savefig(HERE/name,dpi=180,bbox_inches='tight');plt.close(fig)
def command(args): return subprocess.check_output(args,cwd=REPO,text=True)
def history_data():
    path=HERE/'ch17_history.json'
    if path.exists() and '--refresh-history' not in sys.argv: return read(path)
    raw=command(['git','log','main','--date=short','--pretty=%h|%ad|%s'])
    commits=[dict(zip(['hash','date','subject'],line.split('|',2))) for line in raw.splitlines()]
    data={'commit_source':'git log main --date=short --pretty=%h|%ad|%s', 'date_basis':'commit: git author short date; GitHub events: Asia/Seoul', 'commits':commits}
    try:
        data['prs']=json.loads(command(['gh','pr','list','--state','merged','--limit','100','--json','number,mergedAt,title']))
        data['issues']=json.loads(command(['gh','issue','list','--state','all','--limit','100','--json','number,createdAt,closedAt,labels']))
        data['event_source']='GitHub gh pr list / gh issue list (read-only)'
    except (subprocess.CalledProcessError,FileNotFoundError) as exc:
        data['event_source']='fallback: main Merge PR commit dates; README section 6 issue dates; issue closure dates unavailable'
        data['query_error']=str(exc)
        data['prs']=[{'number':None,'mergedAt':c['date'],'title':c['subject']} for c in commits if 'Merge PR' in c['subject']]
        table=(REPO/'README.md').read_text().split('## 6.')[1].split('\n## 7.')[0]
        data['issues']=[{'number':int(n),'createdAt':d,'closedAt':None,'labels':[]} for d,n in re.findall(r'\| (2026-\d\d-\d\d) \| (?:\[)?#(\d+)',table)]
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return data

def main():
    force=read(HERE/'ch17_force_data.json')
    fig,axs=plt.subplots(1,2,figsize=(10,4.3),gridspec_kw={'width_ratios':[2.3,1]},layout='constrained')
    for r,c in zip(force['runs'],['#c45a35','#246ca0']):
        rows=np.array(r['rows']);t=rows[:,0]-r['contact_s']
        axs[0].plot(t,rows[:,1],label=r['mode'],color=c,lw=1.4)
        axs[1].bar(r['mode'],r['overshoot_N'],color=c)
        axs[1].text(r['mode'],r['overshoot_N']+.07,f"{r['overshoot_N']:.3g} N",ha='center')
    rows=np.array(force['runs'][0]['rows'])
    axs[0].plot(rows[:,0]-force['runs'][0]['contact_s'],rows[:,2],ls='--',c='black',lw=.9,label='설정 하중')
    axs[0].axvspan(3.7,4.2,color='gray',alpha=.2,label='구동기 고착 0.5 s (가정)')
    axs[0].set(xlim=(0,6),xlabel='접촉 후 시간 (s)',ylabel='하중 (N)',title='같은 레시피: 20 N · 5 N/s · 속도 한계 ±0.5 mm/s')
    axs[0].legend(fontsize=8,loc='upper left');axs[0].grid(alpha=.2)
    axs[1].set(ylabel='최대 하중 - 목표 하중 (N)',ylim=(0,4.1),title='초과량');axs[1].grid(axis='y',alpha=.2)
    save(fig,'ch17_force_ref_vs_fw.png')
    s5=read(REPO/'sim/test/stage4_results.json')['representative'][-1]['results']
    fig,axs=plt.subplots(1,2,figsize=(10,4.3),layout='constrained')
    for p,c in zip([0,.1,1,3],['#c45a35','#b28a18','#246ca0','#397c4b']):
        rr=sorted([r for r in s5 if r['recipe']['inlet_pressure_MPa']==p],key=lambda r:r['recipe']['gap_um'])
        gaps=[r['recipe']['gap_um'] for r in rr]
        label='모세관만 (0 MPa)' if p==0 else f'{p:g} MPa'+(' (기본 가정값)' if p==1 else ' (가정 범위)')
        for ax,vals in zip(axs,[[r['muf']['fill_time_s'] for r in rr],[r['muf']['unfilled_fraction']*100 for r in rr]]):
            ax.plot(gaps,vals,'o-',label=label,color=c);ax.set(xticks=gaps,xlabel='층간 간격 (μm)');ax.grid(alpha=.2)
    axs[0].set(yscale='log',ylabel='완료 시간 (s, 로그축)',title='Hele-Shaw 가압 + 모세관 보정')
    axs[0].axhline(10,c='black',ls='--',label='충전 허용 10 s (문헌값)');axs[0].legend(fontsize=7)
    axs[1].set(ylabel='10 s 후 미충전 면적률 (%)',title='7 μm는 미충전 0 %여도 필러 규칙상 불량',ylim=(-3,103))
    save(fig,'ch17_fill_capillary_vs_pressure.png')
    base,comp,_=read(REPO/'sim/test/bond_temp_results.json')['S1']
    x=np.arange(1,len(base['thermal_layers'])+1)
    fig,axs=plt.subplots(2,1,figsize=(9,5.5),layout='constrained',sharex=True)
    for r,label,c in [(base,'기본','#c45a35'),(comp,'헤드 보정','#246ca0')]:
        axs[0].plot(x,[l['bond_peak_C'] for l in r['thermal_layers']],'o-',label=label,c=c)
    axs[0].axhline(221,c='black',ls='--',label='액상선 221 ℃ (문헌값)')
    axs[0].axhline(231,c='#397c4b',ls=':',label='목표 231 ℃ (설계값)')
    axs[0].set(ylabel='자기 접합 최고 온도 (℃)');axs[0].legend(ncol=2,fontsize=8)
    axs[1].plot(x,comp['head_setpoints_C'],'o-',c='#246ca0',label='층별 필요 헤드 온도')
    axs[1].axhline(400,c='black',ls='--',label='원문 KPI 400 ℃')
    axs[1].set(xticks=x,xlabel='아래층 → 위층',ylabel='헤드 설정 온도 (℃)',ylim=(250,415));axs[1].legend(fontsize=8)
    for ax in axs: ax.grid(alpha=.2)
    save(fig,'ch17_head_comp.png')
    hist=history_data()
    def day(t): return datetime.fromisoformat(t.replace('Z','+00:00')).astimezone(ZoneInfo('Asia/Seoul')).date() if 'T' in t else datetime.fromisoformat(t).date()
    counts=Counter(day(c['date']) for c in hist['commits']); days=sorted(counts)
    fig,axs=plt.subplots(2,1,figsize=(10,5.5),layout='constrained',sharex=True)
    axs[0].step(days,np.cumsum([counts[d] for d in days]),where='post',marker='o',label='main 전체 커밋 누적 (병합 포함)')
    prc=Counter(day(r['mergedAt']) for r in hist['prs'])
    for d,n in sorted(prc.items()):
        axs[0].axvline(d,alpha=.15,c='#397c4b');axs[0].text(d,.03,f'PR 병합 {n}건',transform=axs[0].get_xaxis_transform(),rotation=90,fontsize=8,va='bottom',ha='left',color='#397c4b')
    axs[0].set(ylabel='누적 커밋 수',ylim=(0,sum(counts.values())*1.12));axs[0].legend(loc='upper left',fontsize=8);axs[0].grid(alpha=.2)
    for r in hist['issues']:
        n=r['number'];op=day(r['createdAt']);cl=day(r['closedAt']) if r['closedAt'] else None
        axs[1].scatter(op,n,c='#c45a35',marker='o',s=24)
        if cl:
            axs[1].plot([op,cl],[n,n],c='gray',alpha=.45);axs[1].scatter(cl,n,c='#246ca0',marker='x',s=35)
    axs[1].scatter([],[],c='#c45a35',label='Issue 열림');axs[1].scatter([],[],c='#246ca0',marker='x',label='Issue 닫힘')
    axs[1].set(ylabel='Issue 번호',xlabel='2026년 날짜 (GitHub 이벤트: 한국 시간)');axs[1].legend(fontsize=8,ncol=2);axs[1].grid(alpha=.2)
    axs[1].xaxis.set_major_locator(mdates.DayLocator());axs[1].xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    save(fig,'ch17_history.png')
if __name__=='__main__':main()
