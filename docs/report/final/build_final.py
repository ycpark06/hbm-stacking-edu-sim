"""기말 보고서: 표지·요약·장별 목차·본문·쪽번호. Poppler 불필요.

중간 build_final.py의 Markdown/Chromium 인쇄 방식을 확장한다.
각 장의 시작까지 동일한 문서를 인쇄하여 쪽수를 센다. DOM 높이 추정 대신
Chromium의 실제 페이지 나눔을 사용하므로 가로 도면 페이지도 포함한다.
"""
from __future__ import annotations
import html
import re
import sys
import tempfile
from pathlib import Path
import markdown
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
CH = [
    '00_요약.md', '01_문제정의.md', '02_요구사항_KPI.md', '03_시스템구성.md',
    '04_공정물리.md', '05_정합오차예산.md', '06_구동부설계.md', '07_열설계.md',
    '08_구조진동해석.md', '09_비전정렬.md', '10_제어회로.md', '11_CAD도면.md',
    '12_통합검증.md', '13_교육안전.md', '14_결론.md', '15_적층공정모드.md',
    '16_디지털트윈.md', '17_트러블슈팅_개선성과.md',
]
OUT = ROOT / 'MSE489_HBM적층본더_기말보고서.pdf'
CSS = """
@page{size:A4;margin:18mm 16mm 20mm}
@page land{size:A4 landscape;margin:10mm 12mm 14mm}
@page cover{size:A4;margin:0}
body{font-family:'Noto Sans CJK KR','Apple SD Gothic Neo',sans-serif;
 font-size:10pt;line-height:1.55;color:#111;margin:0;overflow-wrap:anywhere}
h1{font-size:17pt;border-bottom:2px solid #2b5c8a;padding-bottom:4px}
h2{font-size:13pt;color:#2b5c8a;margin-top:18px;break-after:avoid}
h3{break-after:avoid}table{border-collapse:collapse;width:100%;font-size:8.5pt;margin:8px 0}
th,td{border:1px solid #999;padding:3px 5px;vertical-align:top}th{background:#e8eef5}
thead{display:table-header-group}tr,img{break-inside:avoid}
img{max-width:100%;max-height:230mm;display:block;margin:8px auto;object-fit:contain}
p em{display:block;text-align:center;font-size:8.5pt;color:#444}
section{break-before:page}a{color:#235784;text-decoration:none}
pre{white-space:pre-wrap;font-size:8pt}code{font-size:.9em}
.dwg{page:land;break-before:page;break-after:page}
.dwg img{max-height:164mm;width:auto;max-width:100%}
.cover{page:cover;height:285mm;box-sizing:border-box;padding:45mm 22mm 20mm;
 background:linear-gradient(160deg,#f4f7fb,#fff)}
.cover h1{font-size:27pt;border:0;color:#14365a;line-height:1.5}
.cover .meta{margin-top:40mm;font-size:13pt;line-height:2}
.toc{list-style:none;padding:0;font-size:11pt}
.toc li{display:flex;border-bottom:1px dotted #bbb;padding:5px 0}
.toc .title{flex:1}.toc .num{width:14mm;text-align:right;font-variant-numeric:tabular-nums}
.missing-image{border:1px dashed #999;padding:8mm;color:#555;font-size:9pt}
"""
COVER = """<div class="cover"><h1>교육용 HBM 다단 적층 본더 — TC-NCF / MR-MUF 비교 디지털 트윈 설계 보고서</h1>
<div class="meta">UNIST MSE489 첨단패키징기술<br>2026년 11월 28일</div></div>"""
FOOTER = """<div style="font-size:8px;width:100%;text-align:center;color:#666"><span class="pageNumber"></span></div>"""

def page_count(pdf: bytes) -> int:
    """Chromium PDF의 비압축 페이지 사전 수. /Pages는 세지 않는다."""
    count = len(re.findall(rb'/Type\s*/Page\b', pdf))
    if not count:
        raise ValueError('PDF 페이지 사전을 찾지 못했습니다')
    return count

def load_chapters():
    chapters = []
    for name in CH:
        source = ROOT/name
        if not source.is_file():
            print(f'WARNING: 장 누락, 건너뜀: {name}', file=sys.stderr)
            continue
        source_text = source.read_text(encoding='utf-8')
        rendered = markdown.markdown(source_text, extensions=['tables', 'sane_lists', 'fenced_code'])
        # 중간 원고와 같은 fig/dwg 이미지+캡션 블록을 가로 페이지로 인쇄한다.
        rendered = re.sub(
            r'(<p><img\b[^>]*src="fig/dwg/[^"]+"[^>]*></p>\s*<p><em>.*?</em></p>)',
            r'<div class="dwg">\1</div>', rendered, flags=re.S)
        def check_image(match):
            src = html.unescape(match.group(1))
            if '://' not in src and not (ROOT/src).is_file():
                print(f'WARNING: 그림 누락: {name}: {src}', file=sys.stderr)
                return '<div class="missing-image">그림 삽입 대기: '+html.escape(src)+'</div>'
            return match.group(0)
        rendered = re.sub(r'<img\b[^>]*src="([^"]+)"[^>]*>', check_image, rendered)
        title = re.search(r'<h1>(.*?)</h1>', rendered, re.S)
        title = re.sub('<.*?>', '', title.group(1)) if title else source.stem
        chapters.append((name, title, '<section>'+rendered+'</section>'))
    if not chapters:
        raise ValueError('인쇄할 장이 없습니다')
    return chapters

def toc_html(chapters, pages):
    rows = ''.join('<li><span class="title">'+html.escape(title)+'</span><span class="num">'+str(pages[name])+'</span></li>' for name,title,_ in chapters)
    return '<section><h1>목차</h1><ul class="toc">'+rows+'</ul></section>'

def document(body):
    return '<!doctype html><html lang="ko"><head><meta charset="utf-8"><base href="'+ROOT.as_uri()+'/">'+'<style>'+CSS+'</style></head><body>'+body+'</body></html>'

def build():
    chapters = load_chapters()
    summary = next((ch for ch in chapters if ch[0].startswith('00_')), None)
    body_chapters = [ch for ch in chapters if ch is not summary]
    pages = {name:'000' for name,_,_ in chapters}
    with tempfile.TemporaryDirectory(prefix='mse489-final-') as tmp, sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            source = Path(tmp)/'report.html'
            def print_pdf(body):
                source.write_text(document(body), encoding='utf-8')
                page.goto(source.as_uri(), wait_until='networkidle')
                page.evaluate('document.fonts.ready')
                failed = page.locator('img').evaluate_all('(imgs)=>imgs.filter(i=>!i.complete || i.naturalWidth===0).map(i=>i.src)')
                if failed:
                    raise ValueError('이미지 로드 실패: '+', '.join(failed))
                return page.pdf(prefer_css_page_size=True, print_background=True,
                    display_header_footer=True, header_template='<span></span>', footer_template=FOOTER)
            # 목차 쪽수 자릿수는 고정 폭이다. 쪽수 갱신 뒤에도 수렴 여부를 확인한다.
            for _ in range(4):
                updated = {}
                if summary:
                    updated[summary[0]] = page_count(print_pdf(COVER+'<section><h1>'+html.escape(summary[1])+'</h1></section>'))
                prefix = COVER+(summary[2] if summary else '')+toc_html(chapters,pages)
                for name,title,content in body_chapters:
                    # 강제 새 장의 첫 제목까지 인쇄하면 마지막 쪽이 그 장 시작 쪽이다.
                    updated[name] = page_count(print_pdf(prefix+'<section><h1>'+html.escape(title)+'</h1></section>'))
                    prefix += content
                if updated == pages:
                    break
                pages = updated
            else:
                raise RuntimeError('목차 쪽수가 수렴하지 않았습니다')
            final = print_pdf(COVER+(summary[2] if summary else '')+toc_html(chapters,pages)+''.join(ch[2] for ch in body_chapters))
            OUT.write_bytes(final)
            print(f'{OUT}\n{page_count(final)} pages')
            for name,_,_ in chapters:
                print(f'{pages[name]:>3}  {name}')
        finally:
            browser.close()

if __name__ == '__main__':
    build()
