"""Stored results only: no simulation runs, interpolation or invented evidence."""
import os,json,argparse,hashlib
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/mse489-mpl')
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt,font_manager
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
C=['#14365A','#C2622A','#44505F','#E6ECF3','#FFFFFF']
FONT=Path.home()/'Library/Fonts/Pretendard-Regular.otf'
font_manager.fontManager.addfont(str(FONT))
plt.rcParams.update({'font.family':'Pretendard','font.size':18,'text.color':C[2],'axes.labelcolor':C[2],'xtick.color':C[2],'ytick.color':C[2],'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.edgecolor':C[3],'axes.unicode_minus':False,'figure.facecolor':'white','savefig.facecolor':'white'})
records=[]
def read(file):return json.loads((ROOT/file).read_text())
def evidence(slide,file,key,category):
 v=read(file)
 for k in key:v=v[k]
 records.append(dict(slide=slide,file=file,key=key,category=category,raw=v));return v
S='sim/test/stage4_results.json'; P='sim/params.json';F='docs/report/archive_v1/fig/ch17_force_data.json'
data=read(S); ids={v['id']:i for i,v in enumerate(data['representative'])}
def val(slide,sid,i,*key):return evidence(slide,S,['representative',ids[sid],'results',i,*key],'계산 결과')
def axes(w=11.75,h=4.18):
 fig,ax=plt.subplots(figsize=(w,h));fig.subplots_adjust(left=.08,right=.98,bottom=.17,top=.87);ax.grid(axis='y',color=C[3]);ax.set_axisbelow(True);return fig,ax
def save(fig,name):fig.savefig(HERE/'assets'/f'{name}.png',dpi=160);plt.close(fig)
def temp(ax,i,slide):
 ys=[l['peak_C'] for l in val(slide,'S1',i,'thermal_layers')];x=range(1,13)
 ax.bar(x,ys,color=[C[1] if y<221 else C[0] for y in ys],width=.65)
 ax.axhline(221,color=C[2],ls='--',lw=1.3);ax.text(12.6,285,'221 ℃ 기준',ha='right',fontsize=16)
 ax.set(ylim=(0,300),xticks=list(x),yticks=[0,100,200,300]);ax.grid(axis='y',color=C[3]);ax.set_axisbelow(True)
fig,ax=axes();temp(ax,0,9);ax.set_title('층별 최고 온도 (℃)',loc='left',fontsize=18);save(fig,'temperature')
fig,axs=plt.subplots(1,2,figsize=(11.75,3.2));fig.subplots_adjust(left=.07,right=.98,bottom=.18,top=.81,wspace=.22)
for i,ax in enumerate(axs):temp(ax,i,11);ax.set_title(['보정 전','보정 후'][i],loc='left',fontsize=20)
save(fig,'comparison')
fig,ax=axes();xs=np.arange(2)
for j,(mode,indices) in enumerate([('TC-NCF',[0,1]),('MR-MUF',[2,3])]):
 ys=[val(12,'S3',i,'warpage','max_um') for i in indices];ax.bar(xs+(j-.5)*.28,ys,.28,color=C[j],label=mode)
ax.set(xticks=xs,xticklabels=['100 μm','50 μm'],ylim=(0,36));ax.set_title('최대 휨 (μm)',loc='left');ax.legend(frameon=False);save(fig,'warpage')
fig,ax=axes();fig.subplots_adjust(left=.16);ys=[val(13,'S4',i,'cycle','bonder_s') for i in range(2)];ax.barh(['TC-NCF','MR-MUF'],ys,color=C[:2],height=.45);ax.invert_yaxis();ax.set(xlim=(0,285),xlabel='본더 점유 시간 (s)');ax.grid(False)
for i,y in enumerate(ys):ax.text(y+5,i,f'{y:.0f} s',va='center')
save(fig,'occupancy')
fig,ax=axes();fig.subplots_adjust(left=.16);ys=[val(14,'S5',i,'muf','fill_time_s') for i in [4,5]];ax.barh(['0 MPa','1 MPa'],ys,color=C[:2],height=.45);ax.invert_yaxis();ax.set(xlim=(0,1050),xlabel='15 μm 간격의 충전 시간 (s)');ax.grid(False)
for i,y in enumerate(ys):ax.text(y+12,i,f'{y:.0f} s' if i==0 else f'{y:.1f} s',va='center')
save(fig,'fill')
fig,ax=axes();runs=evidence(16,F,['runs'],'노이즈 없는 계산 시험')
for r,c,label in zip(runs,C[:2],['보정 전','적분 제한 후']):
 rows=np.array(r['rows']);ax.plot(rows[:,0]-r['contact_s'],rows[:,1],color=c,label=label,lw=2)
rows=np.array(runs[0]['rows']);ax.plot(rows[:,0]-runs[0]['contact_s'],rows[:,2],color=C[2],ls='--',lw=1,label='설정 하중')
ax.axvspan(3.7,4.2,color=C[3]);ax.set(xlim=(0,6),ylim=(0,26),xlabel='접촉 후 시간 (s)');ax.set_title('하중 (N)',loc='left');ax.legend(frameon=False,fontsize=16,loc='upper left');save(fig,'force')
# All numerical claims from notes, including inputs and caveats.
for slide,sid,idx,keys in [(9,'S1',0,[['recipe'],['thermal_layers']]),(11,'S1',1,[['head_setpoints_C']]),(13,'S4',1,[['cycle','batch_post_s']]),(15,'S5',3,[['recipe'],['muf','fill_time_s'],['muf','unfilled_fraction'],['muf','filler_blocked'],['defect_judgement']])]:
 for key in keys:val(slide,sid,idx,*key)
for key in [['solder','liquidus_snag'],['judgement','bond_temp_margin_C'],['equipment_limits','head_max_temp_C'],['thermal_stack','tool_contact_R_area'],['thermal_stack','chuck_contact_R_area'],['muf','applied_pressure'],['muf','viscosity_at_fill']]:
 evidence(11 if key[0]!='muf' else 14,P,key,'입력 kind 참조')
for key in [['results','forced_cooling_design_segment'],['verdict','status']]:evidence(20,'calc/hardware/reflow_heater.json',key,'설계 목표 / 계산 결과')
# Exact text claims are checked against the report; no numbers synthesized from labels.
report='docs/report/archive_v1/17_트러블슈팅_개선성과.md'
for slide,claim,cat in [(17,'저레인지 기본을 1 N/s','설계 선택'),(18,'14,400 출력값','저장된 독립 SIL 검증 결과'),(18,'8.1e-6','저장된 독립 SIL 검증 결과')]:
 assert claim in (ROOT/report).read_text(),claim
 records.append(dict(slide=slide,file=report,key=claim,category=cat,raw=claim))
(HERE/'numeric_manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
print(f'charts=6, provenance records={len(records)}')

(HERE/'chart_hashes.json').write_text(json.dumps({n:hashlib.sha256((HERE/'assets'/f'{n}.png').read_bytes()).hexdigest() for n in ['temperature','comparison','warpage','occupancy','fill','force']},indent=2)+'\n')
