"""최종 보고서 PDF: 표지 + 요약 + 목차(쪽수 자동) + 본문 + 쪽 번호. 도면은 가로 페이지."""
import markdown, re, pathlib, subprocess, sys
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).parent
CH=["01_문제정의.md","02_요구사항_KPI.md","03_시스템구성.md","04_공정물리.md","05_정합오차예산.md","06_구동부설계.md",
    "07_열설계.md","08_구조진동해석.md","09_비전정렬.md","10_제어회로.md","11_CAD도면.md","12_통합검증.md","13_교육안전.md","14_결론.md"]
OUT=ROOT/(sys.argv[1] if len(sys.argv)>1 else "MSE489_교육용다이본더_설계보고서.pdf")
css="""@page{size:A4;margin:18mm 16mm 20mm}@page land{size:A4 landscape;margin:10mm 12mm 14mm}@page cover{margin:0}
body{font-family:'Noto Sans CJK KR',sans-serif;font-size:10pt;line-height:1.55;color:#111}
h1{font-size:17pt;border-bottom:2px solid #2b5c8a;padding-bottom:4px}h2{font-size:13pt;color:#2b5c8a;margin-top:18px}
table{border-collapse:collapse;width:100%;font-size:8.6pt;margin:8px 0}th,td{border:1px solid #999;padding:3px 5px;vertical-align:top}
th{background:#e8eef5}img{max-width:100%;display:block;margin:8px auto}p em{display:block;text-align:center;font-size:8.5pt;color:#444}
td:first-child{white-space:nowrap}tr,img{page-break-inside:avoid}section{break-before:page}
.dwg{page:land;break-before:page;break-after:page}.dwg img{max-height:170mm;width:auto;max-width:100%}
.cover{page:cover;height:285mm;overflow:hidden;position:relative;background:linear-gradient(160deg,#f4f7fb 0%,#ffffff 60%)}
.cover .band{background:#2b5c8a;height:16mm}.cover .t{padding:30mm 22mm 0}.cover h1{border:0;font-size:28pt;margin:0 0 6mm;color:#14365a}
.cover .sub{font-size:13pt;color:#2b5c8a;margin-bottom:14mm}.cover img{width:150mm;margin:0 auto}
.cover .meta{position:absolute;bottom:28mm;left:22mm;font-size:11pt;line-height:2}
.toc{list-style:none;padding:0;font-size:10.5pt}.toc li{display:flex;border-bottom:1px dotted #bbb;padding:2px 0}.toc li span:first-child{flex:1}
.toc li.h2{padding-left:6mm;font-size:9.4pt;color:#333}.toc li.h1{font-weight:bold;margin-top:4px}ul li{list-style:none}"""
def body_html():
    secs=[]
    for f in CH:
        h=markdown.markdown((ROOT/f).read_text(),extensions=["tables","sane_lists"])
        # drawings -> landscape block (image + caption)
        h=re.sub(r'(<p><img alt="[^"]*" src="fig/dwg/[^"]+" /></p>\s*<p><em>.*?</em></p>)',r'<div class="dwg">\1</div>',h,flags=re.S)
        secs.append("<section>"+h+"</section>")
    return "".join(secs)
def heads(html):
    return re.findall(r"<h([12])>(.*?)</h\1>",html)
def toc_html(hs,pages):
    li=[]
    for (lv,t),pg in zip(hs,pages):
        t=re.sub("<.*?>","",t)
        if lv=="2" and not re.match(r"\d+\.\d",t): continue
        li.append(f'<li class="h{lv}"><span>{t}</span><span>{pg}</span></li>')
    return '<section><h1>목차</h1><ul class="toc">'+"".join(li)+"</ul></section>"
cover="""<div class="cover"><div class="band"></div><div class="t">
<h1>교육용 데스크톱 다이본더<br>설계 보고서</h1>
<div class="sub">UNIST MSE489 첨단패키징기술 PBL — 교육용 반도체 장비 설계 및 제어</div>
<img src="fig/view_iso.png"></div>
<div class="meta">제출일: 2026년 11월<br>학번 / 이름: ____________________</div></div>"""
summary=markdown.markdown((ROOT/"00_요약.md").read_text(),extensions=["tables","sane_lists"])
def build(toc,path):
    html=f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>{cover}<section>{summary}</section>{toc}{body_html()}</body></html>"
    h=path.with_suffix(".html"); h.write_text(html)
    with sync_playwright() as p:
        b=p.chromium.launch(); pg=b.new_page(); pg.goto(h.resolve().as_uri())
        pg.pdf(path=str(path),prefer_css_page_size=True,print_background=True,display_header_footer=True,
               header_template="<span></span>",
               footer_template="<div style='font-size:8px;width:100%;text-align:center;color:#666'><span class='pageNumber'></span></div>")
        b.close()
hs=heads(body_html())
# pass 1 with placeholder toc (same length) to find pages
build(toc_html(hs,["00"]*len(hs)),OUT)
txt=[subprocess.run(["pdftotext","-f",str(i),"-l",str(i),str(OUT),"-"],capture_output=True,text=True).stdout
     for i in range(1,int(re.search(r"Pages:\s+(\d+)",subprocess.run(["pdfinfo",str(OUT)],capture_output=True,text=True).stdout).group(1))+1)]
import html as _h
def norm(s): return re.sub(r"\s+","",_h.unescape(re.sub("<.*?>","",s)))
start=next(i for i,t in enumerate(txt) if '첨단패키징에서는' in norm(t)); pages=[]
for lv,t in hs:
    key=norm(t)[:18]; pg="–"
    for i in range(start,len(txt)):
        if key in norm(txt[i]): pg=str(i+1); start=i; break
    pages.append(pg)
build(toc_html(hs,pages),OUT)
print(OUT, subprocess.run(["pdfinfo",str(OUT)],capture_output=True,text=True).stdout.split("Pages:")[1].split()[0],"pages")
