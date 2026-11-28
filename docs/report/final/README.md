# 기말 설계 보고서

교육용 HBM 다단 적층 본더의 TC-NCF / MR-MUF 비교 디지털 트윈 설계 보고서다. 표지는 제목·과목명·날짜만 포함하며 개인정보를 넣지 않는다. 중간 원고는 수정하지 않는다.

| 원고 | 내용 |
|---|---|
| `00_요약.md` | 목표·장비 구성·원문 KPI·S1~S5·한계 |
| `01_문제정의.md`~`14_결론.md` | 중간 설계를 적층 장비로 개정하는 담당 원고 |
| `15_적층공정모드.md` | 열·휨·NCF·MUF·정렬·사이클·민감도 |
| `16_디지털트윈.md` | 공통 C·SIL·웹 HMI·3D·배포 |
| `17_트러블슈팅_개선성과.md` | 전체 로그·대표 Issue·중간 대비 개선 성과 |
| `fig/` | 중간 그림·도면·스크립트 복사본과 장별 신규 그림 |
| `build_final.py` | Markdown→Chromium PDF, 장별 목차 쪽수 자동 계산 |

## 그림 생성

저장소 루트에서 다음 명령을 실행한다. 단계4 결과 JSON을 읽으며 원본 결과를 수정하지 않는다. `ch15_figs.py`는 온도–시간·휨–층수·S5 열지도·사이클 분해 그림을 생성한다. `ch16_architecture.py`는 README 2절의 관계를 그린다.

```bash
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 docs/report/final/fig/ch15_figs.py
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 docs/report/final/fig/ch16_architecture.py
```

`fig/ch16_hmi.png`는 최종 브라우저 검증 시 Claude가 넣는 화면 캡처다. 현재 파일이 없으면 PDF에는 삽입 대기 상자가 표시되고 경고한다. 다른 담당자의 그림도 같은 방식으로 경고한다.

## PDF 빌드

Python의 `markdown`, `playwright`와 Playwright Chromium이 필요하다. 그림 재생성에는 `numpy`, `matplotlib`이 필요하다. 글꼴은 CSS에서 `Noto Sans CJK KR`, `Apple SD Gothic Neo`, sans-serif 순서다.

```bash
cd docs/report/final
python3 build_final.py
```

지정 Python 환경을 직접 선택하려면 다음과 같이 실행한다.

```bash
cd docs/report/final
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 build_final.py
```

출력은 `MSE489_HBM적층본더_기말보고서.pdf`다. 00~17장 목록에서 없는 파일은 건너뛰고 경고한다. 표지→요약→장별 목차→본문 순서이며, `fig/dwg/` 이미지·캡션은 가로 페이지, 나머지는 A4 세로 페이지다. 쪽번호는 전체 PDF 기준이다.

Poppler의 `pdfinfo`·`pdftotext`를 호출하지 않는다. 실제 Chromium PDF의 `/Type /Page` 사전 수를 세고, 각 장 시작까지의 동일한 문서를 인쇄하여 시작 쪽수를 계산한다. 목차 쪽수 갱신이 수렴한 후 전체 PDF를 인쇄한다. 장내 절은 각 장 원고에서 찾으며 자동 목차는 장 단위다.

샌드박스에서 Chromium 실행이 차단되면 우회하지 않고 오류를 보고한다. 다른 장과 화면 캡처가 모두 들어온 뒤 최종 빌드하고 요약 1쪽·목차 쪽수·긴 표의 머리행·가로 도면·한글 글꼴을 시각 검토해야 한다. 태그 발행은 최종 제출 시 사용자 결정이다.

## 이 작업 환경의 빌드 시도 (2026-11-28)

지정 Python 3.12로 실행하여 누락된 01~14장과 예정 HMI 그림 경고를 확인했다. 이후 Chromium 시작에서 `TargetClosedError`, `MachPortRendezvousServer: Permission denied (1100)`로 중단되었다. 샌드박스를 우회하지 않았으며 PDF는 생성하지 못했다. 따라서 자동 목차 실제 쪽수, 요약 1쪽 여부와 PDF 레이아웃은 검증 대기다. 그림 5개는 생성 후 시각 확인했고 중간 그림·도면·스크립트 32개 복사본은 원본과 바이트 일치를 확인했다.
