"""Chromium 없이 원고 링크·장수·원본 보존·공개판 옵션을 검사한다."""
import ast,hashlib,json,re
from pathlib import Path
from build_v2 import HERE,REPO,document

def main():
    manifest=json.loads((HERE/'pages.json').read_text())
    assert len(manifest['report'])==35 and len(manifest['summary'])==9
    failures=[]
    for kind,items in manifest.items():
        for x in items:
            text=(HERE/x['file']).read_text()
            for url in re.findall(r'(?:src|href)="([^"]+)"',text):
                if '://' not in url and not (HERE/url).exists():failures.append(x['file']+': '+url)
    hashes=json.loads((HERE/'archive_manifest.json').read_text())
    archive=HERE.parent/'archive_v1'
    for path,digest in hashes.items():
        if hashlib.sha256((archive/path).read_bytes()).hexdigest()!=digest:failures.append('archive modified '+path)
    namespace={}
    tree=ast.parse((archive/'build_final.py').read_text())
    # 실행하지 않고 CH·ROOT·fig 상대 경로를 확인한다.
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id=='CH':namespace['CH']=ast.literal_eval(node.value)
    for chapter in namespace['CH']:
        f=archive/chapter
        if not f.exists():failures.append('archive chapter missing '+chapter)
        for url in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',f.read_text()):
            if '://' not in url and not (archive/url).exists():failures.append('archive figure missing '+url)
    assert 'Path(__file__).resolve().parent' in (archive/'build_final.py').read_text()
    for kind in ['report','summary']:
        public=document(kind)
        assert '공개판' in public and len(re.findall(r'<main class="sheet',public))==len(manifest[kind])+1
    result={'report_pages_with_cover':36,'summary_pages_with_cover':10,'appendix_pages':len(manifest['appendix']),'archive_files_unchanged':len(hashes),'failures':failures,'PDF_render':'미실행: Claude 담당'}
    (HERE/'static_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if failures:raise SystemExit(1)
if __name__=='__main__':main()
