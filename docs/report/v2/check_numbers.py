"""원고 span의 표시값·저장 JSON을 대조하고 미표시 숫자를 수동 대조 목록에 낸다."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib,json,re,sys
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
NUM=re.compile(r'(?<![A-Za-z])[-−±]?(?:\d[\d,]*(?:\.\d+)?(?:e[-+]?\d+)?|[⁰¹²³⁴⁵⁶⁷⁸⁹]+)',re.I)
class Read(HTMLParser):
    def __init__(self):
        super().__init__();self.stack=[];self.automatic=[];self.manual=[];self.text=[]
    def handle_starttag(self,tag,attrs):
        if tag in ['img','br','hr','meta','link','input']:return
        self.stack.append((tag,dict(attrs)))
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:
                del self.stack[i:];break
    def handle_data(self,text):
        self.text.append(text)
        ids=[a['data-number'] for _,a in self.stack if 'data-number' in a]
        if ids:self.automatic.append((ids[-1],text))
        elif NUM.search(text):self.manual.append(text.strip())
def resolve(file,path):
    v=json.loads((REPO/file).read_text(encoding='utf-8'))
    for k in path:v=v[k]
    return v

def main():
    registry=json.loads((HERE/'numbers.json').read_text())
    manifest=json.loads((HERE/'pages.json').read_text());automatic=[];manual=[];errors=[]
    def cell(x):return str(x).replace('|',' / ').replace('\n',' ')
    for kind in ['report','summary']:
        for item in manifest[kind]:
            parser=Read();parser.feed((HERE/item['file']).read_text())
            for id,display in parser.automatic:
                if id not in registry:errors.append('unregistered: '+id);continue
                r=registry[id];v=resolve(r['source'],r['key']);expected=f"{v*r['scale']:,.{r['digits']}f}"
                ok=v==r['stored'] and display==expected==r['display']
                row={'location':item['file'],'id':id,**r,'actual':v,'pass':ok}
                automatic.append(row)
                if not ok:errors.append(item['file']+': '+id)
            for text in parser.manual:
                # 장·쪽·Issue·모델명도 누락 없이 기록하되 물리값과 구분한다.
                structural=bool(re.fullmatch(r'[\d\s–·~]+',text)) or bool(re.fullmatch(r'(?:S\d|#\d|PG\d|STM32H743).*',text))
                manual.append({'location':item['file'],'numbers':NUM.findall(text),'context':text,'source':item['sources'],'kind':'식별자·편집 번호' if structural else '문서·도면 수동 대조','status':'수동 확인 필요'})
    # 그림의 모든 데이터값은 sidecar와 원본 파일 해시로 연결한다.
    figure=[]
    for f in ['fig/figure_sources.json','fig/extra_sources.json']:
        path=HERE/f
        if not path.exists():errors.append('missing '+f);continue
        x=json.loads(path.read_text());source='sim/test/stage4_results.json'
        ok=hashlib.sha256((REPO/source).read_bytes()).hexdigest()==x['sha256']
        figure.append({'sidecar':f,'source':source,'source_hash_pass':ok})
        if not ok:errors.append('stale '+f)
    # 별도 저장 결과의 모든 24개 접합 온도를 실제 대조한다.
    stage=json.loads((REPO/'sim/test/stage4_results.json').read_text())['representative'][0]['results']
    bond=json.loads((REPO/'sim/test/bond_temp_results.json').read_text())['S1']
    cross=[a['bond_peak_C']==b['bond_peak_C'] for i in [0,1] for a,b in zip(stage[i]['thermal_layers'],bond[i]['thermal_layers'])]
    if len(cross)!=24 or not all(cross):errors.append('S1 cross-check')
    lines=['# 수치대조표','',f'JSON 표시 대조 {len(automatic)}회 / 고유 키 {len(set(r["id"] for r in automatic))}개. S1 별도 결과 24개 대조: '+('통과' if all(cross) else '실패')+'.', '', '자동 대조 통과는 아래 span·저장 JSON·그림 출처 해시에 한정한다. 수동 목록·이미지 내부 도면 치수·축 눈금은 PDF 검토 시 별도 확인한다. 새 원고의 숫자는 매 실행마다 다시 추출하므로 목록 누락 없이 표시된다.', '', '## JSON 자동 대조','', '| 위치·ID | 출처 파일·키 | 저장값 | 표시·반올림 | 범주 | 결과 |','|---|---|---|---|---|---|']
    for r in automatic:
        lines.append('| '+' | '.join(map(cell,[r['location']+' / '+r['id'],r['source']+' → '+'.'.join(map(str,r['key'])),repr(r['actual']),r['display']+f' (소수 {r["digits"]}자리, 배율 {r["scale"]})',r['kind'],'통과' if r['pass'] else '실패']))+' |')
    lines+=['','## 문서·도면 수동 대조와 편집 번호','', '저장값·표시값 열의 문자열은 원고에 적힌 그대로다. JSON key가 없는 문서·도면·번호는 source의 해당 문맥과 대조해야 한다. 이 표의 “수동 확인 필요”는 자동 검증 통과로 집계하지 않는다. 범주는 각 원고의 해당 문장·표를 따른다.','', '| 위치 | 원고 저장·표시 수치 | 문맥 | 출처 파일·절 | 범주·검사 |','|---|---|---|---|---|']
    for r in manual:
        lines.append('| '+' | '.join(map(cell,[r['location'],' / '.join(r['numbers']),r['context'],' · '.join(r['source']),r['kind']+' / '+r['status']]))+' |')
    lines+=['','## 그림 내부의 수치','', '| 그림 | 원본·키 | 저장값·반올림·범주 | 검사 |','|---|---|---|---|']
    for r in figure:
        lines.append('| '+r['sidecar']+' | sim/test/stage4_results.json | sidecar의 배열 정밀값 전체; 데이터=계산 결과, 입력은 params kind. 눈금은 표시 척도·참고값 | 원본 SHA256 '+('일치' if r['source_hash_pass'] else '불일치')+' |')
    lines+=['| 재사용 CAD·도면·화면 | archive_v1/fig/ch11_* · ch16_* · media/stills | 원본 이미지 바이트 유지. 치수·전원은 설계값, 질량·높이는 참고값. 원본 dimensions.json·summary.json·pinmap.csv 대조 | 수동 확인 필요 |','', '각 그래프의 정밀 데이터 전체는 [대표 쪽 그림 전표](fig/figure_sources.json)와 [S1~S4 그림 전표](fig/extra_sources.json)에 수록했다. 파라미터 입력 전표는 [부록 B](appendix/B_파라미터.md)에 모든 kind/source와 함께 기록했다.']
    (HERE/'수치대조표.md').write_text('\n'.join(lines)+'\n')
    result={'automatic_occurrences':len(automatic),'unique_ids':len(set(r['id'] for r in automatic)),'automatic_pass':not errors,'manual_contexts':len(manual),'manual_status':'별도 검토 필요','S1_cross_check_count':len(cross),'figures':figure,'errors':errors}
    (HERE/'number_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return int(bool(errors))
if __name__=='__main__':sys.exit(main())
