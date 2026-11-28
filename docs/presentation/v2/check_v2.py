"""Public-deck structural and source checks. PDF layout review remains Claude's step."""
import json,re,zipfile,hashlib,sys
from pathlib import Path
from xml.etree import ElementTree as ET
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
D=json.loads((HERE/'deck_v2.json').read_text()); records=json.loads((HERE/'numeric_manifest.json').read_text())
errors=[]
def check(ok,msg):
 if not ok:errors.append(msg)
def read(p):return json.loads(p.read_text())
slides=D['slides'];check(len(slides)==21,'장 수');check(sum(s['seconds'] for s in slides)==210,'시간 합계')
for s in slides:
 words=len(s['body'].split());check(words<=20,f"{s['id']} 본문 {words}");check('\n' not in s['title'],f"{s['id']} 제목 줄")
for r in records:
 p=ROOT/r['file']
 if isinstance(r['key'],list):
  actual=read(p)
  for k in r['key']:actual=actual[k]
  check(actual==r['raw'],f"원값 불일치 {r['slide']} {r['key']}")
 else:check(r['raw'] in p.read_text(),f"보고서 근거 불일치 {r['slide']}")
S=read(ROOT/'sim/test/stage4_results.json');sc={x['id']:x['results'] for x in S['representative']};base,comp,_=sc['S1']
check(sum(l['peak_C']<221 for l in base['thermal_layers'])==2,'미달 층 수')
check(all(round(l['peak_C'])==231 for l in comp['thermal_layers']),'231 반올림')
check(round(max(comp['head_setpoints_C']))==341,'헤드 최대 반올림')
check(all(l['peak_C']==l['bond_peak_C'] for r in [base,comp] for l in r['thermal_layers']),'자기 접합 최고 정의')
check([round(sc['S3'][b]['warpage']['max_um']/sc['S3'][a]['warpage']['max_um'],1) for a,b in [(0,1),(2,3)]]==[4.1,4.1],'휨 배율')
check([round(sc['S4'][i]['cycle']['bonder_s']) for i in [0,1]]==[240,41],'점유 반올림')
check(round(sc['S5'][4]['muf']['fill_time_s'])==893 and round(sc['S5'][5]['muf']['fill_time_s'],1)==3.3,'충전 반올림')
check(sc['S5'][3]['muf']['unfilled_fraction']==0 and sc['S5'][3]['muf']['filler_blocked'],'필러 판정')
ban=re.compile(r'혁신적|획기적|효율적인|핵심적인|TTS|ffmpeg|영상\s*제작|자막\s*제작|\d{4}[-./]\d{1,2}[-./]\d{1,2}|\d{1,2}월\s*\d{1,2}일|(?:월|화|수|목|금|토|일)요일|(?:이름|성명|학번)\s*[:：]|(?<!\d)20\d{6,8}(?!\d)|(?:발표자|작성자)\s*[:：]\s*[가-힣]{2,4}',re.I)
A='{http://schemas.openxmlformats.org/drawingml/2006/main}';P='{http://schemas.openxmlformats.org/presentationml/2006/main}'
ppt=HERE/'MSE489_기말발표_v2.pptx';visible=[];durations=[]
with zipfile.ZipFile(ppt) as z:
 files=z.namelist();names=sorted([n for n in files if re.fullmatch(r'ppt/slides/slide\d+.xml',n)],key=lambda n:int(re.search(r'(\d+)\.xml',n).group(1)))
 check(len(names)==21,'PPTX 장 수')
 embedded={hashlib.sha256(z.read(n)).hexdigest() for n in files if n.startswith('ppt/media/')}
 for name,digest in read(HERE/'chart_hashes.json').items():
  check(hashlib.sha256((HERE/'assets'/f'{name}.png').read_bytes()).hexdigest()==digest,f'{name} 그래프 변경')
  check(digest in embedded,f'{name} PPTX 그래프 동일성')
 for i,name in enumerate(names):
  tree=ET.fromstring(z.read(name));texts=[n.text or '' for n in tree.iter(A+'t')];joined='\n'.join(texts);visible.append(joined)
  check(slides[i]['title'] in texts,f'{i+1} PPTX 제목');check(sum(len(t.split()) for t in texts if t!=slides[i]['title'])<=20,f'{i+1} PPTX 전체 본문 어절');check(not ban.search(joined),f'{i+1} 금지/날짜/개인정보 패턴')
  check(not list(tree.iter(A+'tbl')),f'{i+1} 표 금지')
  for off,ext in [(x.find(A+'off'),x.find(A+'ext')) for x in tree.iter(A+'xfrm')]:
   if off is not None and ext is not None:
    check(all(int(off.get(k,'0'))>=0 for k in ['x','y']) and int(off.get('x'))+int(ext.get('cx'))<=12192000+1000 and int(off.get('y'))+int(ext.get('cy'))<=6858000+1000,f'{i+1} 개체 경계')
  note=ET.fromstring(z.read(f'ppt/notesSlides/notesSlide{i+1}.xml'));nt='\n'.join(n.text or '' for n in note.iter(A+'t'))
  match=re.search(r'말할 시간: (\d+)초',nt);check(bool(match),f'{i+1} 노트 시간');durations.append(int(match.group(1)) if match else 0)
  check('말할 문장과 범위:' in nt,f'{i+1} 말할 문장')
 check(sum(durations)==210,'PPTX 노트 시간 합계')
 for name in [n for n in files if n.endswith('.xml')]:ET.fromstring(z.read(name))
 theme=z.read('ppt/theme/theme1.xml').decode();check('a:ea typeface="Pretendard"' in theme,'동아시아 글꼴')
 core=ET.fromstring(z.read('docProps/core.xml'));creator=core.find('{http://purl.org/dc/elements/1.1/}creator');check(creator is None or not creator.text,'작성자 개인정보')
# Optional real font metrics; title must fit on one line, body within its assigned box.
metrics='skipped (Pillow not installed)'
try:
 from PIL import ImageFont
 fonts=Path.home()/'Library/Fonts'
 for b in read(HERE/'layout_manifest.json'):
  if not isinstance(b['text'],str):continue # hyperlink runs checked separately below
  font=ImageFont.truetype(str(fonts/('Pretendard-Bold.otf' if b['bold'] else 'Pretendard-Regular.otf')),size=round(b['size']*4))
  width=max(font.getlength(line)/4 for line in b['text'].split('\n'))
  check(width<=b['w']*72,f"{b['slide']} 텍스트 폭 {width:.1f}>{b['w']*72:.1f}")
 metrics='Pretendard actual glyph widths checked'
except ImportError:pass
report={'slides':len(slides),'seconds':sum(durations),'body_words':[len(s['body'].split()) for s in slides],'numeric_records':len(records),'font_metrics':metrics,'errors':errors,'pdf_review':'Pending Claude PowerPoint conversion and visual review'}
(HERE/'check_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(bool(errors))
