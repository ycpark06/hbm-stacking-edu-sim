"""고정 A4 원고 → Playwright Chromium PDF. 기본은 이름 없는 공개판."""
from __future__ import annotations
import argparse
import html
import json
from pathlib import Path
import re
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
NAMES = {'report':'MSE489_HBM적층본더_보고서_v2.pdf', 'summary':'MSE489_HBM적층본더_요약본.pdf', 'appendix':'MSE489_HBM적층본더_보고서_v2_부록.pdf'}

def is_inside(path, root):
    return path.resolve().is_relative_to(root.resolve())

def document(kind, cover=None):
    manifest = json.loads((HERE/'pages.json').read_text(encoding='utf-8'))
    sheets=[]
    if kind != 'appendix':
        members=''
        if cover is not None:
            data=json.loads(cover.read_text(encoding='utf-8'))
            rows=data.get('members')
            if not isinstance(rows,list) or not rows or any(not isinstance(r,dict) or not isinstance(r.get('name'),str) or not isinstance(r.get('id'),str) for r in rows):
                raise ValueError('표지 JSON은 members[].name/id 문자열이 필요합니다')
            members='<p>'+ '<br>'.join(html.escape(r['name'])+'　'+html.escape(r['id']) for r in rows)+'</p>'
        title='본보고서 v2' if kind=='report' else '요약본'
        sheets.append('<main class="sheet cover"><header class="running"><b>MSE489</b><span>첨단패키징기술</span></header><div class="content"><h1>교육용 HBM<br>다단 적층 본더</h1><h2>TC-NCF / MR-MUF 비교 디지털 트윈</h2><div class="cover-meta"><p>'+title+'</p><p>설계·계산·모의 검증</p>'+members+'</div></div><footer><span>UNIST · MSE489</span><span>'+('제출판' if cover else '공개판')+'</span></footer></main>')
    for item in manifest[kind]:
        content=(HERE/item['file']).read_text(encoding='utf-8')
        sheets.append('<main class="sheet" data-page="'+str(item['page'])+'"><header class="running"><b>'+html.escape(item['chapter'])+'</b><span>교육용 HBM 적층 본더</span></header><div class="content">'+content+'</div><footer><span>'+html.escape(item['label'])+' · 계산·모의 검증</span><span class="page">'+str(item['page'])+'</span></footer></main>')
    return '<!doctype html><html lang="ko"><head><meta charset="utf-8"><base href="'+HERE.as_uri()+'/"><title>MSE489 '+kind+'</title><style>'+(HERE/'report.css').read_text(encoding='utf-8')+'</style></head><body>'+''.join(sheets)+'</body></html>'

QA = '''() => [...document.querySelectorAll('.sheet')].map((s,index)=>{
 const box=s.getBoundingClientRect(),f=s.querySelector('footer'),foot=f.getBoundingClientRect();
 const bad=[...s.querySelectorAll('.content *, .running')].filter(e=>{
   const b=e.getBoundingClientRect(); return b.width && b.height && (b.right>box.right+.5||b.left<box.left-.5||b.bottom>foot.top-.5);
 }).map(e=>({tag:e.tagName,text:e.textContent.slice(0,80)}));
 return {index:index+1,page:s.dataset.page||'cover',overflow:bad,
 failed_images:[...s.querySelectorAll('img')].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.getAttribute('src')),
 font:getComputedStyle(s).fontFamily};
})'''

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--kind',choices=['all',*NAMES],default='all')
    p.add_argument('--cover-json',type=Path)
    p.add_argument('--out',type=Path,help='all: 출력 폴더, 단일 kind: PDF 파일')
    p.add_argument('--pages-png',type=Path,help='쪽별 PNG와 render_check.json 저장 폴더')
    p.add_argument('--check-overflow',action='store_true',help='검사는 항상 수행하며 넘침 시 PDF 생성 중단')
    p.add_argument('--html-only',action='store_true',help='Chromium 없이 HTML만 생성')
    a=p.parse_args()
    if a.cover_json:
        if not a.out or is_inside(a.out,REPO) or is_inside(a.cover_json,REPO):
            p.error('제출판은 저장소 밖 --cover-json 및 --out이 필요합니다')
        if a.pages_png and is_inside(a.pages_png,REPO):
            p.error('제출판 페이지 PNG도 저장소 밖에 저장해야 합니다')
    kinds=list(NAMES)[:2] if a.kind=='all' else [a.kind]
    targets={k:((a.out/NAMES[k] if a.kind=='all' else a.out) if a.out else HERE/NAMES[k]) for k in kinds}
    for k,dest in targets.items():
        if a.cover_json and is_inside(dest,REPO): p.error('제출판 출력은 저장소 밖이어야 합니다')
        dest.parent.mkdir(parents=True,exist_ok=True)
    if a.html_only:
        for k,dest in targets.items():
            dest.with_suffix('.html').write_text(document(k,a.cover_json),encoding='utf-8')
        print('HTML 생성 완료')
        return
    from playwright.sync_api import sync_playwright
    with tempfile.TemporaryDirectory(prefix='mse489-v2-') as tmp, sync_playwright() as pw:
        browser=pw.chromium.launch()
        try:
            for k,dest in targets.items():
                f=Path(tmp)/(k+'.html');f.write_text(document(k,a.cover_json),encoding='utf-8')
                page=browser.new_page(viewport={'width':794,'height':1123},device_scale_factor=1.5)
                page.emulate_media(media='print')
                page.goto(f.as_uri(),wait_until='networkidle');page.evaluate('document.fonts.ready')
                results=page.evaluate(QA)
                folder=a.pages_png/k if a.pages_png else None
                if folder:
                    folder.mkdir(parents=True,exist_ok=True)
                    for i,sheet in enumerate(page.locator('.sheet').all()):
                        sheet.screenshot(path=str(folder/f'{i:03d}.png'))
                    (folder/'render_check.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
                if any(r['overflow'] or r['failed_images'] for r in results):
                    raise RuntimeError(k+': 본문 넘침/이미지 실패. render_check.json 또는 HTML을 확인하세요')
                pdf=page.pdf(prefer_css_page_size=True,print_background=True,display_header_footer=False)
                count=len(re.findall(rb'/Type\s*/Page\b',pdf))
                if count!=len(results): raise RuntimeError(f'{k}: 예상 {len(results)}쪽, PDF {count}쪽')
                dest.write_bytes(pdf)
                print(k+f': {count}쪽 완료')
                page.close()
        finally: browser.close()

if __name__=='__main__': main()
