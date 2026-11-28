"""S1~S4 보조 그래프. 저장 JSON을 읽으며 물리 모델을 재실행하지 않는다."""
from pathlib import Path
import hashlib,json
from matplotlib import pyplot as plt
from matplotlib import ticker
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
NAVY,ORANGE,INK,GRID='#14365A','#C2622A','#44505F','#E6ECF3'

def main():
    data=json.loads((REPO/'sim/test/stage4_results.json').read_text())
    scenes={s['id']:s['results'] for s in data['representative']}
    evidence=[]
    def save(fig,name,keys,values):
        fig.tight_layout(pad=1.4)
        fig.savefig(HERE/'fig'/name,dpi=220)
        plt.close(fig)
        evidence.append({'file':name,'source':'sim/test/stage4_results.json','keys':keys,'stored_values':values,'kind':'계산 결과'})
    # S1: 재가열과 가접 노출은 별도 축에 표시한다.
    fig,axs=plt.subplots(1,2,figsize=(10,4))
    vals=[]
    for ax,r,key,title,color in zip(axs,[scenes['S1'][0],scenes['S1'][2]],['reheat_count','tack_exposures'],['TC 후속 재가열','MR 후속 가접 노출'],[ORANGE,NAVY]):
        y=[x[key] for x in r['thermal_layers']];vals.append(y)
        ax.bar(range(1,13),y,color=color);ax.set(title=title,xlabel='층 번호',ylabel='후속 노출 (회)',xticks=[1,4,8,12],yticks=[0,5,11])
        ax.spines[['top','right']].set_visible(False)
    save(fig,'s1_history.png',['S1.results[0].thermal_layers[].reheat_count','S1.results[2].thermal_layers[].tack_exposures'],vals)
    fig,axs=plt.subplots(1,2,figsize=(10,4),sharey=True)
    vals=[]
    for ax,r,title,color in zip(axs,scenes['S2'],['TC-NCF','MR-MUF'],[ORANGE,NAVY]):
        xy=r['alignment']['layer_errors_um']; vals.append(xy)
        x=[p[0] for p in xy];y=[p[1] for p in xy]
        ax.scatter(x,y,color=color,s=45)
        ax.axhline(0,c=GRID);ax.axvline(0,c=GRID)
        ax.set(xlabel='층간 x 오차 (μm)',ylabel='층간 y 오차 (μm)',title=title,xlim=(-.65,.65),ylim=(-.6,.6),xticks=[-.5,0,.5])
        ax.spines[['top','right']].set_visible(False)
    save(fig,'s2_alignment.png',['S2.results[].alignment.layer_errors_um'],vals)
    fig,ax=plt.subplots(figsize=(8,4))
    vals=[r['warpage']['max_um'] for r in scenes['S3']]
    labels=['TC 100','TC 50','MR 100','MR 50']
    ax.bar(labels,vals,color=[NAVY,ORANGE,NAVY,ORANGE]);ax.set(ylabel='最大 휨 (μm)'.replace('最大','최대'),xlabel='모드 · 다이 두께 (μm)')
    ax.spines[['top','right']].set_visible(False)
    save(fig,'s3_warpage.png',['S3.results[].warpage.max_um'],vals)
    fig,axs=plt.subplots(1,2,figsize=(10,4))
    vals=[]
    for ax,key,title in zip(axs,['bonder_s','batch_post_s'],['본더 점유','배치 후공정']):
        y=[r['cycle'][key] for r in scenes['S4']];vals.append(y)
        ax.bar(['TC-NCF','MR-MUF'],y,color=[ORANGE,NAVY]);ax.set(title=title,ylabel='시간 (s)')
        ax.yaxis.set_major_locator(ticker.MaxNLocator(4));ax.spines[['top','right']].set_visible(False)
    save(fig,'s4_cycle.png',['S4.results[].cycle.bonder_s','S4.results[].cycle.batch_post_s'],vals)
    (HERE/'fig/extra_sources.json').write_text(json.dumps({'sha256':hashlib.sha256((REPO/'sim/test/stage4_results.json').read_bytes()).hexdigest(),'figures':evidence},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    import make_figs
    make_figs.main()
    main()
