# 보고서 v2

승인된 시안의 본문 35쪽 + 표지 1쪽, 요약본 9쪽 + 표지 1쪽을 고정 A4 HTML로 구성했다. 본문 번호는 표지를 제외한다. 부록은 별도이며 기본 빌드에 합치지 않는다. PDF·페이지 PNG의 최종 조판 확인은 Claude가 수행한다.

## 파일

| 경로 | 내용 |
|---|---|
| `chapters/01.html` ~ `35.html` | 본보고서 원고. 장별 배치는 아래 표 |
| `summary/01.html` ~ `09.html` | 본보고서 장 번호로 연결하는 요약본 |
| `appendix/A_트러블슈팅.md` | 범위에 맞는 전체 15건, 작업 단계·증상·원인·선택 이유·결과 |
| `appendix/B_파라미터.md` | params의 전표 207개 전체, kind/source/note 포함 |
| `appendix/C_계산상세.md`, `D_이력.md` | 식·검증 경계·상세 계산 링크, 기존 판 이력 |
| `appendix/001.html` ~ `057.html` | 부록 인쇄용 전표·문제 로그·계산 설명. Markdown 원본도 함께 확인 |
| `pages.json`, `report.css` | 쪽 순서·제목·근거 및 승인 시안 스타일 |
| `make_figs.py`, `figures_extra.py`, `fig/` | 저장 JSON 재도식화·6개 그래프·정밀값/출처 해시 |
| `build_v2.py` | HTML→PDF·표지 옵션·쪽 이미지·넘침/이미지 로드 검사 |
| `check_numbers.py`, `numbers.json` | 숫자 span의 JSON 경로·범주·반올림과 대조 |
| `수치대조표.md`, `number_check.json` | 자동 결과·수동 확인 대상 전체 문맥 |
| `archive_manifest.json` | 기존 판 이동 직후 파일별 SHA256 |
| `검증인계.md` | 논리 검증 12건의 위치, 검사 결과, Claude 확인 목록 |

## 목차와 예상 본문 쪽

| 장 | 쪽 | 분량 |
|---|---|---:|
| 1 요약 / 목차 | 1 / 2 | 2 |
| 2 과제 목표와 요구사항 | 3–4 | 2 |
| 3 중간 설계 요약 | 5–7 | 3 |
| 4 왜 HBM 적층인가 | 8–9 | 2 |
| 5 장비 고도화 | 10–13 | 4 |
| 6 디지털 트윈 | 14–16 | 3 |
| 7 S1·S2·S3·S5·S4 | 17–21 | 5 |
| 8 트러블슈팅과 개선 성과 | 22–29 | 8 |
| 9 한계와 향후 시험 | 30–32 | 3 |
| 10 결론 / 참고문헌 | 33 / 34–35 | 3 |

중간 내용은 뒤 장에서 쓰는 요구·정합 결론을 표 A, 구조·구동·열 사양을 표 B로 남겼다. 상세 유도·에폭시 실습·프레임 반복·중간 도면 전문은 [중간 판](../midterm/)을 참조한다. 승인 계획의 생략/유지 판단을 따랐으며 기존 판의 기말 추가 내용은 4–9장에 재배치했다.

## 공개판 빌드

Python에 matplotlib·numpy·playwright가 필요하다. HTML→PDF는 기존 build_final.py와 같은 Playwright Chromium 인쇄 방식이다. 사용 가능한 Python 실행 파일을 선택한다. 이 작업 환경에서는 `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3`에 matplotlib가 설치되어 있다. 기본 `python3`에는 없었다.

```sh
python3 docs/report/v2/make_figs.py
python3 docs/report/v2/check_numbers.py
python3 docs/report/v2/build_v2.py --pages-png /tmp/report-v2-pages --check-overflow
```

기본 출력은 이 폴더의 `MSE489_HBM적층본더_보고서_v2.pdf`, `MSE489_HBM적층본더_요약본.pdf`다. 표지에는 이름·학번을 넣지 않으며 로컬 개인정보 파일을 탐색하거나 읽지 않는다. `--kind report` 또는 `summary`는 한 종류만 생성한다. `--kind appendix`는 별도 부록 PDF를 생성한다.

```sh
python3 docs/report/v2/build_v2.py --kind report --out /tmp/보고서.pdf
python3 docs/report/v2/build_v2.py --html-only
python3 docs/report/v2/build_v2.py --kind appendix --out /tmp/부록.pdf --pages-png /tmp/report-v2-appendix
```

쪽 PNG는 종류별 폴더에 저장한다. footer의 시작선 아래로 본문 요소가 내려가거나 페이지 좌우를 벗어나면 검사 실패다. 이미지 로드 실패와 예상 sheet 수/PDF 페이지 수도 검사한다. `--check-overflow`를 생략해도 넘침 검사는 수행한다. 실패하면 PDF 저장을 중단하며 `render_check.json`과 PNG를 보고 원고를 수정한다. 자동 높이 축소로 본문을 숨기지 않는다.

HTML만 볼 때도 이미지·링크의 기준은 v2 폴더다. 배포용 완성 PDF·PNG는 아직 생성하지 않았다.

## 제출판: 로컬 전용

`--cover-json`은 명시한 파일만 읽으며 `members[].name`, `members[].id` 문자열을 표지에만 넣는다. `--out`이 필수이고 입력·출력·PNG 모두 저장소 밖 경로여야 한다. 값은 로그나 JSON 전표에 쓰지 않는다. 입력 형식은 `{"members":[{"name":"이름 문자열","id":"학번 문자열"}]}`다. 실제 개인정보 예시는 저장소에 만들지 않는다.

```sh
python3 docs/report/v2/build_v2.py --cover-json /저장소밖/표지정보.json --out /저장소밖/보고서출력 --pages-png /저장소밖/검토PNG
```

`--kind all`의 `--out`은 폴더이며 두 PDF를 넣는다. 단일 kind의 `--out`은 PDF 파일이다. 제출판의 `--html-only`도 저장소 밖에만 출력한다.

## 글꼴

HTML·그래프 순서는 Pretendard → Malgun Gothic → Apple SD Gothic Neo다. Pretendard 정적 OTF/TTF를 OS 글꼴 관리자 또는 `~/Library/Fonts`에 설치한 뒤 새 프로세스로 빌드한다. 그래프는 설치된 Pretendard OTF를 등록하며 `fig/figure_sources.json`에 실제 선택 글꼴을 적는다. 지정 글꼴이 하나도 없으면 생성 실패로 처리하므로 먼저 설치한다. 다른 글꼴로 바뀌면 PDF 줄바꿈을 다시 확인한다.

## 숫자 검사 범위

원고의 `data-number` span은 source/key의 현재 저장값, 등록 정밀값, 표시 반올림을 실제 대조한다. 나머지 숫자 문맥도 모두 추출해 수동 목록에 낸다. 수동 목록은 JSON 대조 통과로 집계하지 않는다. 그림 데이터는 sidecar에 전체 정밀값과 JSON 해시를 남긴다. 재사용한 도면·화면 내부 치수·눈금은 원본 및 최종 PNG에서 따로 확인한다.

기존 판을 [archive_v1](../archive_v1/)로 mv해 보존했다. 원본 내부의 과거 경로 문자열은 바이트 보존 때문에 그대로다. 실제 사용 경로는 갱신했으며 예외와 검사 명령은 검증인계에 적었다. 커밋·push·PR은 수행하지 않았다.
