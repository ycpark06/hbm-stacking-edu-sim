"""공개 PPTX 구조 검사. 렌더링 검사는 별도로 수행한다."""
import json
import re
import zipfile
import unicodedata
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
NS = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'}
EMU = 914400

# 실제 Mac 대체 글꼴을 측정한 값이 아닌 사전 검사 추정치다.
# 한글/전각 1 em, 영숫자 .55 em, 공백 .3 em에 폭 여유 15%를 더한다.
# 명시적 줄바꿈을 유지해야 하는 수정 대상만 검사하며 실제 렌더링을 대신하지 않는다.
FONT_WIDTH_FACTOR = 1.15

def estimated_width(text, size):
    units = sum(1 if unicodedata.east_asian_width(c) in ('W', 'F')
                else .3 if c == ' ' else .55 for c in text)
    return units * size / 72 * FONT_WIDTH_FACTOR

def check_text_fit(body, width, height, label, margins=(0, 0, 0, 0)):
    left, right, top, bottom = margins
    paragraphs = body.findall('a:p', NS)
    line_heights = []
    for paragraph in paragraphs:
        runs = paragraph.findall('a:r', NS)
        required = sum(estimated_width(run.findtext('a:t', '', NS),
                                      int(run.find('a:rPr', NS).get('sz')) / 100)
                       for run in runs)
        assert required <= width - left - right, (label, '15% font width', round(required, 3), round(width-left-right, 3))
        size = max((int(run.find('a:rPr', NS).get('sz')) / 100 for run in runs), default=18)
        line_heights.append(size / 72 * 1.25)
    assert sum(line_heights) <= height - top - bottom, (label, 'line height', sum(line_heights), height-top-bottom)

def check():
    deck = json.loads((HERE / 'deck.json').read_text())
    with zipfile.ZipFile(HERE / 'MSE489_기말발표.pptx') as z:
        slides = [p for p in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', p)]
        assert len(slides) == len(deck['slides']) == 8
        presentation = ET.fromstring(z.read('ppt/presentation.xml'))
        dim = presentation.find('p:sldSz', NS)
        assert abs(int(dim.get('cx')) / EMU - 13.333) < .001
        assert abs(int(dim.get('cy')) / EMU - 7.5) < .001
        objects = tables = fit_checks = 0
        for i, d in enumerate(deck['slides'], 1):
            root = ET.fromstring(z.read(f'ppt/slides/slide{i}.xml'))
            seen = set()
            text_bounds = {}
            table_bottom = None
            for tag in ('sp', 'pic', 'graphicFrame'):
                for obj in root.findall(f'.//p:spTree/p:{tag}', NS):
                    nv = obj.find('.//p:cNvPr', NS)
                    name = nv.get('name')
                    assert re.fullmatch(re.escape(d['id']) + r'_(title|text|table|img|box)\d+', name), name
                    assert name not in seen
                    seen.add(name)
                    objects += 1
                    xfrm = obj.find('.//a:xfrm', NS) if tag != 'graphicFrame' else obj.find('p:xfrm', NS)
                    if xfrm is not None:
                        off, ext = xfrm.find('a:off', NS), xfrm.find('a:ext', NS)
                        x, y = int(off.get('x')) / EMU, int(off.get('y')) / EMU
                        w, h = int(ext.get('cx')) / EMU, int(ext.get('cy')) / EMU
                        assert min(x, y, w, h) >= 0, (name, x, y, w, h)
                        assert x + w <= 13.334 and y + h <= 7.501, (name, x, y, w, h)
                    if tag == 'sp':
                        body = obj.find('p:txBody', NS)
                        if body is not None:
                            content = ''.join(body.itertext())
                            # 실제 PPTX 텍스트와 좌표로 수정 대상을 찾는다.
                            text_bounds[content] = (x, y, w, h)
                            targets = ([d['title']] if d['id'] == 'improve' else
                                       [d['metric']] if d['id'] == 'trouble' else
                                       [d['conclusion']] if d['id'] == 'wrap' else [])
                            if content in targets:
                                check_text_fit(body, w, h, name)
                                fit_checks += 1
                    for run in obj.findall('.//a:r', NS):
                        props = run.find('a:rPr', NS)
                        assert props is not None and props.get('sz'), name
                        size = int(props.get('sz')) / 100
                        # 공통 틀의 장 번호/출처 13 pt, 쪽 번호 12 pt만 예외.
                        assert size >= 18 or (name.endswith('title1') and size == 13) or (re.fullmatch(d['id'] + r'_text[23]', name) and size == 12), (name, size)
                    for latin in obj.findall('.//a:latin', NS):
                        assert latin.get('typeface') == 'Malgun Gothic'
                    for tbl in obj.findall('.//a:tbl', NS):
                        total_h = sum(int(r.get('h')) for r in tbl.findall('a:tr', NS)) / EMU
                        assert y + total_h < 6.8, (name, 'table rows', y + total_h)
                        if d['id'] == 'results':
                            table_bottom = y + total_h
                            widths = [int(c.get('w')) / EMU for c in tbl.findall('a:tblGrid/a:gridCol', NS)]
                            for row_index, row in enumerate(tbl.findall('a:tr', NS)):
                                row_height = int(row.get('h')) / EMU
                                for col_index, cell in enumerate(row.findall('a:tc', NS)):
                                    props = cell.find('a:tcPr', NS)
                                    margins = tuple(int(props.get(k, '0')) / EMU for k in ('marL', 'marR', 'marT', 'marB'))
                                    check_text_fit(cell.find('a:txBody', NS), widths[col_index], row_height,
                                                   (name, row_index, col_index), margins)
                                    fit_checks += 1
                        tables += 1
            if d['id'] == 'results':
                legend = text_bounds[d['legend']]
                footer = text_bounds[f"{i} / 8 · {d['footer']}"]
                assert table_bottom + .1 <= legend[1]
                assert legend[1] + legend[3] + .05 <= footer[1]
            if d['id'] == 'wrap':
                last = text_bounds[d['limits'][-1]]
                conclusion = text_bounds[d['conclusion']]
                assert last[1] + last[3] + .3 <= conclusion[1]
            notes = ET.fromstring(z.read(f'ppt/notesSlides/notesSlide{i}.xml'))
            note_text = ''.join(n.text or '' for n in notes.findall('.//a:t', NS))
            assert d['notes'] in note_text, d['id']
            assert root.find('.//a:buChar', NS) is None, d['id']
        alltext = '\n'.join(z.read(p).decode() for p in z.namelist() if p.endswith('.xml'))
        assert 'MSE489 첨단패키징기술 기말 PBL' in alltext
        assert not re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', alltext)
        assert not re.search(r'\b(?:19|20)\d{6}\b', alltext)
        print(f'PASS: {len(slides)} slides, {objects} named objects, {tables} native tables, notes/font/bounds/no-bullets')
        print(f'PASS: {fit_checks} text/cell fits with 15% estimated font width, line heights, results/wrap gaps')
        print('PASS: 공개판 과목 표지, 이메일·학번 패턴 없음 (XML 구조 확인)')

if __name__ == '__main__':
    check()
