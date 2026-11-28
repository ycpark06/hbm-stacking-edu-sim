"""Chromium 없이 목차·본문·요약본 연결 및 생성 HTML의 쪽 번호를 대조한다."""
import json,re,sys
from html.parser import HTMLParser
from build_v2 import HERE,document

class Text(HTMLParser):
    def __init__(self):
        super().__init__();self.parts=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('style','script'):self.skip+=1
        elif tag=='br':self.parts.append(' ')
    def handle_endtag(self,tag):
        if tag in ('style','script'):self.skip-=1
        elif tag in ('p','h1','h2','header','footer','td','th'):self.parts.append('\n')
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)

def text(source):
    p=Text();p.feed(source);return ''.join(p.parts)

def norm(value):return ' '.join(text(value).split())

def main():
    m=json.loads((HERE/'pages.json').read_text());errors=[]
    toc=(HERE/'chapters/02.html').read_text()
    entries=re.findall(r'<p data-toc-section="([^"]+)" data-toc-page="(\d+)"><span>(.*?)</span><b>(\d+)</b></p>',toc,re.S)
    actual=[];chapters=[];sections={}
    for expected,x in enumerate(m['report'],1):
        if x['page']!=expected:errors.append('page sequence '+x['file'])
        source=(HERE/x['file']).read_text();heading=re.search(r'<h1>(.*?)</h1>',source,re.S)
        if not heading:errors.append('missing h1 '+x['file']);continue
        if x['chapter']=='목차':continue
        sec=x.get('section','');a,b=map(int,sec.split('.'))
        if not chapters or chapters[-1]!=a:chapters.append(a)
        sections.setdefault(a,[]).append(b)
        expected_title=sec+' '+norm(x['title'])
        if norm(heading[1])!=expected_title:errors.append('body title '+x['file'])
        if not x['chapter'].startswith(str(a)+' ') or x['label']!=x['chapter']:errors.append('chapter header '+x['file'])
        actual.append((sec,str(x['page']),expected_title,str(x['page'])))
    if chapters!=list(range(1,len(chapters)+1)):errors.append('chapter sequence')
    for a,seq in sections.items():
        if seq!=list(range(1,len(seq)+1)):errors.append('section sequence '+str(a))
    if [(s,p,norm(t),b) for s,p,t,b in entries]!=actual:errors.append('TOC title/number/page/order')
    toc_chapters=re.findall(r'data-toc-chapter="(\d+)">(.*?) <span>(.*?)</span>',toc)
    expected_chapters=[]
    for a in chapters:
        rows=[x for x in m['report'] if x.get('section','').startswith(f'{a}.')]
        ps=[x['page'] for x in rows];label=str(ps[0]) if len(ps)==1 else f'{ps[0]}–{ps[-1]}'
        expected_chapters.append((str(a),rows[0]['chapter'],label))
    if [(a,norm(t),p) for a,t,p in toc_chapters]!=expected_chapters:errors.append('TOC chapter title/range')
    for x in m['summary']:
        source=text((HERE/x['file']).read_text())
        label=x.get('report_page_label','')
        if not label or label+'쪽' not in source:errors.append('summary page label '+x['file'])
        parsed=[]
        for g in label.split('・'):
            ends=list(map(int,g.split('–')));parsed.extend(range(ends[0],ends[-1]+1))
        if parsed!=x['report_pages'] or any(p<1 or p>len(m['report']) for p in parsed):errors.append('summary range '+x['file'])
    versions=[]
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--text-dir',type=__import__('pathlib').Path);args=p.parse_args()
    for kind in ['report','summary','appendix']:
        rendered=document(kind)
        pages=re.findall(r'<main class="sheet" data-page="(\d+)">',rendered)
        if pages!=[str(x['page']) for x in m[kind]]:errors.append('rendered pages '+kind)
        for sheet,x in zip(re.split(r'<main class="sheet" data-page="\d+">',rendered)[1:],m[kind]):
            if f'<span class="page">{x["page"]}</span>' not in sheet:errors.append('footer '+kind)
        visible=text(rendered)
        # Explicit exception: filenames and repository paths retain their version components.
        visible=re.sub(r'\S*(?:/|\.(?:png|pdf|html|py|md|json))\S*','',visible)
        versions.extend(kind+': '+line for line in visible.splitlines() if re.search(r'\bv2\b',line,re.I))
        if args.text_dir:
            args.text_dir.mkdir(parents=True,exist_ok=True);(args.text_dir/(kind+'.txt')).write_text(visible)
    if versions:errors.extend(versions)
    result={'report_body_pages':len(m['report']),'report_with_cover':len(m['report'])+1,'summary_with_cover':len(m['summary'])+1,'chapters':len(chapters),'sections':len(actual),'toc_pass':not errors,'visible_version_mentions':len(versions),'path_filename_exception':'파일명·저장소 경로 유지','errors':errors,'render_status':'HTML 정적 대조; PDF·넘침·폰트 시각 확인은 Claude 담당'}
    (HERE/'toc_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2));return bool(errors)
if __name__=='__main__':sys.exit(main())
