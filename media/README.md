# 시연 영상 자동 녹화

배포 HMI를 Playwright로 조작하여 **무음 화면 영상 8개, 계획 총 360초(6분)**를 만든다. 실제 녹화는 Claude가 Chromium 실행이 가능한 환경에서 수행한다. 이번 작업에서는 Chromium을 실행하지 않고 Python 문법과 로컬 선택자 계약만 정적으로 검사한다. MachPortRendezvousServer 등 브라우저 실행 오류가 나면 중단하며 실행 옵션 변경이나 다른 브라우저로 우회하지 않는다.

## 녹화 방법

저장소 루트에서 Python 3.12와 설치된 `playwright.sync_api`, Chromium을 사용한다. `ffmpeg`는 선택 사항이며 스크립트가 설치하지 않는다.

```bash
PYTHON=/Library/Frameworks/Python.framework/Versions/3.12/bin/python3
"$PYTHON" -m py_compile media/tools/record_demo.py media/tools/check_selectors.py
"$PYTHON" media/tools/check_selectors.py
"$PYTHON" media/tools/record_demo.py --plan

# 실제 녹화 담당 환경에서 실행: 하단 장면 제목과 선택적 MP4 연결
"$PYTHON" media/tools/record_demo.py --captions --concat

# 브라우저 창을 보면서 녹화할 때
"$PYTHON" media/tools/record_demo.py --captions --headed
```

기본 URL은 `https://ycpark06.github.io/hbm-stacking-edu-sim/web/`이다. `--url http://localhost:8000/web/`처럼 다른 배포본을 지정할 수 있다. 로컬 실행 시 저장소 루트를 서비스하여 `/sim/`, `/firmware/build/`, `/cad/web/` 상대 경로도 제공해야 한다. 녹화 전에 배포본이 로컬 UI 소스와 같은 버전이고 wasm·GLB가 준비되어 있는지 녹화 담당자가 확인한다.

1920×1080 뷰포트·동일 비디오 크기·장면별 새 컨텍스트를 사용한다. 마이크나 오디오 스트림을 만들지 않는다. 출력은 고정 경로 `media/out/`이다. 기존 산출물을 덮어쓰지 않도록 폴더가 비어 있지 않으면 시작을 거부한다. 재녹화할 때는 기존 폴더를 보관 위치로 옮긴다. 실패 시 `scenes.json`에 실패 원인과 가능한 부분 영상을 남기고 중단한다. 실패 영상을 정상 완료본으로 연결하지 않는다.

## 장면 계획

길이는 공정 입력이 아닌 영상 편집용 표시 설정이다. 각 장면 시간에는 페이지 로드·계산 대기·설명 읽기가 포함된다. 클릭 후 완료 조건과 버튼 활성 상태를 확인하고 남은 시간은 마지막 화면에서 채운다. 예산을 넘기거나 필수 읽기 시간이 부족하면 실패 처리한다. 3D 장면은 계산 후 단계 재생 중 느린 마우스 드래그로 OrbitControls를 조작한다.

| 번호 | 제목 | 계획 길이 | 화면 동작 | 보여 줄 값·구분 |
|---|---|---:|---|---|
| 1 | 장비 3D · 적층 진행 | 40 s | GLB 성공 문구 대기 → S2 실행 → 느린 회전 → 적층 재생 완료 | GLB 연결 상태, 층·단계·재생 시간(계산 후 교육용 재생) |
| 2 | S1 접합 온도 미달과 헤드 보정 | 60 s | S1 실행 → 기본/보정의 층별 표 열기 → 알람 패널 | 기본 1·2층 BOND_TEMP_LOW, 자기 접합 최고·헤드 설정·재가열·재용융(계산 결과) |
| 3 | S2 정렬과 비전 보정 반복 | 55 s | S2 누적 오차 → `vision.html` → 첫/마지막 층, 초기/최종 보정 단계, 모서리 전환 | 누적 X/Y, 검출 px·NCC, Δx/Δy/Δθ·참값 잔여·수렴(계산 결과); 비전 페이지는 층간 누적과 별개 |
| 4 | S3 박형 다이와 모델 한계 | 45 s | S3 네 결과 카드를 차례로 강조 | 각 휨·판정·두께 절반의 휨 증가 배율, 두 모드 박형 불량·모델 한계 |
| 5 | S5 가압 충전 | 45 s | 간격 × 입구 압력 표 → 대표 결과 카드 | 미충전률·판정, 충전 시간·필러·겔 경고; 금형 압력과 입구 유효 압력 구분 |
| 6 | S4 처리량 분해 | 40 s | 본더/배치 결과 → 두 모드 사이클 분해 표 열기 | 본더 점유·배치 후공정·후경화 등 시간(관찰 항목의 계산 결과); 라인 UPH 아님 |
| 7 | 고장 주입과 수동 복구 | 55 s | 하드웨어 고장 → 래치 → 원인 유지 중 리셋 거부 → 원인 해제 후 래치 유지 → 수동 리셋 → 헤드 통전 중 척 히터 요청 | 래치 코드, 헤드/척 W, 동시 통전 요청 차단(별도 wasm FIRMWARE 시연 결과) |
| 8 | 근거와 관찰 항목 | 20 s | assumption 검색 → 업체 주장·모델 한계 패널 | 가정값·출처, 업체 주장 관찰 항목·판정 없음 |
| 합계 | | **360 s** | **6분** | 내레이션 후첨부 |

공정·결과 수치는 스크립트가 새로 만들거나 화면에 덧씌우지 않는다. UI의 S1~S5와 기본 파라미터를 그대로 사용한다. 장면별 `samples`에 뷰포트 안에 그려진 DOM 텍스트를 읽어 저장하고, 그중 숫자가 있는 문자열을 `numeric_text`에 함께 담는다. 배지와 단위를 유지한 **화면 문자열**이며 고정 기준값으로 덮어쓰지 않는다. 숨긴 표·화면 밖 결과·모델 내부 값은 수집하지 않는다. Canvas 화소와 영상 십자선은 영상으로 관찰하며 그 수치는 인접 DOM 표시를 읽는다.

비교 근거는 [요구사항 7절](../docs/requirements.md#7-시연에서-보여-줄-대표-시나리오), [단계 4 보정 결과](../docs/stage4_model_update.md), [S1~S5 정의](../sim/scenarios.js), [파라미터](../sim/params.json)이다. 공정 조건은 가정값을 포함하며 업체 세부 조건은 비공개다. 원문 KPI와 설계 목표·설계값·문헌값·역산 추정값·가정값·관찰 항목·참고값·계산 결과를 화면 배지에 따라 구분한다. 업체 주장은 관찰 항목이며 판정에 쓰지 않는다. 질량·높이는 참고값이다.

S3의 선형 탄성·상온 물성·기판/점탄성/경화 수축 미포함 한계와 두 모드 박형 불량을 그대로 보여 준다. NCF 보이드 정량 모델은 없고, MUF 표는 미충전 면적률이다. [냉각 설계의 FAIL/REVIEW 및 제작 후 시험 과제](../docs/requirements.md#하드웨어-운전-조건-단계-5)는 이 영상으로 해결되거나 실물 검증된 것으로 해석하지 않는다.

## 출력·검증 범위

- `scene_01_3d.webm`부터 `scene_08_closing.webm`까지 장면별 영상.
- `scenes.json`: 계획, 실행 상태, 장면 번호·제목·요약, UTC 시작/끝, 실제 `start_s`/`end_s`/`duration_s`, 시점별 화면 문자열과 주요 수치.
- `--concat`: `ffmpeg`가 있으면 `concat.txt`와 무음 `demo_full.mp4` 생성. 없으면 건너뛰고 사유 기록. 연결 실패는 오류로 기록한다.

`start_s`와 `end_s`는 각 장면의 실제 단조 시계 경과 시간을 순서대로 누적한 **편집 타임라인**이다. 장면 간 컨텍스트 생성·인코더 종료 대기 시간은 제외한다. 각 장면은 페이지 생성 직전부터 마지막 화면 유지 종료까지 측정하며 탐색 시간도 포함한다. WebM의 첫 프레임과 인코더 종료 시점 때문에 파일의 실제 재생 길이는 이 경과 시간과 조금 다를 수 있다. 내레이션 최종 동기화는 생성된 영상의 재생 길이로 확인한다. UTC 시각은 실행 이력 확인용이다.

`check_selectors.py`는 브라우저를 열지 않는다. HTML id, JS가 생성하는 프리셋·인터락 버튼의 이름과 순서, 상태·제목 문자열, 비전 생성 코드와 5~7분 시간 계획을 검사한다. `--plan`도 브라우저 없이 실행된다. 이 검사는 배포본 일치·실제 CSS 배치·WebGL·계산 소요 시간·비디오 인코딩을 보증하지 않는다. 녹화 담당자는 완성본에서 표·배율·한계 문구·십자선의 가독성과 총 5~7분을 확인한다. 실패 시 배포 상태와 화면을 확인한 뒤 허용된 녹화 스크립트를 조정한다.

## 보관과 내레이션 연결

`media/out/` 전체는 gitignore 대상이다. **WebM·MP4 등 영상 파일을 커밋하지 않는다.** 완성본은 [CLAUDE.md 3절](../CLAUDE.md#3-폴더별-역할)에 따라 GitHub Releases 또는 외부 저장소에 보관한다. 업로드 위치와 공개 여부는 사용자가 결정한다. 이 스크립트는 업로드하지 않는다. 링크 확정 후 README의 영상 링크 반영은 별도 담당자가 수행한다.

내레이션 대본은 `scenes.json`의 장면 번호·제목과 연결한다. 각 장면의 `start_s`~`end_s`에 맞춰 대본을 나누고, `samples[].scene_s`를 알람·보정·리셋 설명의 기준점으로 사용한다. 계산 결과는 해당 녹화의 화면 문자열을 인용한다. `--captions`는 장면 제목만 표시하며 음성·대본 자막을 생성하지 않는다. 후편집에서 별도 녹음한 음성을 붙이고 화면 수치가 들리는 대본과 일치하는지 확인한다.

## 커밋 단위 제안

1. `feat: 배포 사이트 시연 장면 자동 녹화 스크립트` — `media/tools/`와 `.gitignore`.
2. `docs: 영상 녹화 방법과 장면 표` — `media/README.md`.

Codex는 커밋·push·PR·Issue 생성 없이 파일과 정적 검사 결과만 전달한다.

## 내레이션 큐 모드 (녹화 담당: Claude)

```bash
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m py_compile media/tools/record_demo.py media/tools/check_selectors.py
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 media/tools/check_selectors.py
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 media/tools/record_demo.py --cues media/tools/cues.json --plan
# 아래 녹화 명령은 Chromium 실행이 가능한 담당 환경에서만 실행한다.
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 media/tools/record_demo.py --cues media/tools/cues.json --captions --headed
```

`--cues`를 생략하면 기존 동작 순서와 고정 유지 시간 모드를 사용한다. 큐 모드는 각 장면의 페이지·GLB 로드, S1~S5 해당 계산 완료, 시작 스크롤을 **준비 구간**에서 처리한다. 고장 장면은 원인 해제·수동 리셋까지 준비한다. 준비 구간도 녹화되지만 본편 길이에는 포함하지 않는다. 준비 대기는 장면마다 별도 180초 상한이며 실패하면 오류를 기록하고 중단한다. 준비 완료 후 두 번의 화면 갱신을 기다리고 큐 시계 0을 잡는다. 모든 장면에서 GLB 성공 표시를 확인하므로 배포본에 GLB가 필요하다.

`cues.json`의 `targets`는 실제 HTML/JS 생성 근거, 선택자, 예상 요소 개수를 함께 보관한다. 런타임 개수가 다르면 다른 카드를 잘못 보여 주는 대신 중단한다. S1 카드 순서는 기본·헤드 보정·MR-MUF, S5 카드 순서는 간격별 모세관·기본·하한·상한이다. S5 표의 압력 열은 정렬된 0 / 0.1 / 1 / 3 MPa 순서를 따른다. 재용융은 기존 표의 통합 열(재가열 / 액상선 교차 / 후속 재용융)을 강조한다. S5의 15 μm × 0 MPa 충전 시간은 표와 카드가 멀리 떨어져 있어, 해당 카드의 **DOM 값과 구분 배지를 복제한 작은 표시창**을 표와 함께 보여 준다. 숫자를 별도로 입력하거나 모델 내부에서 읽지 않는다. 다음 강조에서 이 표시창과 이전 테두리를 해제한다. `--captions`는 여전히 장면 제목만 표시한다.

큐 시각은 읽기 전용 `영상/tts/timing.json`의 문장 시작값을 소수 셋째 자리까지 옮겼다. 시작 화면의 0초와 고장 복구 동작 13.5/15초는 지정된 편집 큐다. 장면 길이는 40/60/55/45/45/40/55/20초, 합계 360초다. `--plan` 표에 각 큐의 장면·시각·동작·대상이 출력된다. `goto` 로드 대기와 드래그도 동일한 절대 시계를 쓴다. 로드가 늦으면 다음 큐의 남은 대기가 줄고, 이미 지난 큐는 즉시 실행한다. 동시각 큐는 파일 순서대로 실행하며 실제 지연량을 기록한다. 장면 끝에서 진행 중인 동작은 남은 장면 시간으로 제한되며, 완료하지 못하면 실패로 기록한다.

큐 모드 `scenes.json` 필드:

- `clock0_video_s`: `page.video`를 받은 직후의 `time.monotonic()` 기준으로 측정한 준비 완료 시각. 반올림하지 않은 초 단위 값이다.
- `duration_s`: 잘라낼 본편의 계획 길이. `video_elapsed_s`는 준비를 포함한 실제 벽시계 경과 시간이다. `cue_elapsed_s`는 본편의 실제 경과 시간이다.
- `cues[]`: 계획 `t`/`action`/`args`, 실제 시작 `actual_s`(큐 시계), `video_s`(영상 기준), `late_s`(지연), `ended_s`(큐 시계 종료), `status`와 오류. 실패한 큐도 저장한다.
- `start_s`/`end_s`: 준비를 제외한 편집 타임라인. `actual_total_s`는 장면 본편 길이의 합계다. 기존 모드의 `samples`와 달리 큐 모드는 `cues`가 동기화 기준이다.

장면별 준비 구간을 먼저 잘라낸다. 예를 들어 `scenes.json`에서 해당 장면의 `clock0_video_s`와 `duration_s`를 가져와 다음과 같이 실행한다. 정확한 재인코딩을 위해 `-c copy`를 쓰지 않는다.

```bash
ffmpeg -ss <clock0_video_s> -i media/out/scene_02_s1.webm -t <duration_s> \
  -an -c:v libx264 -pix_fmt yuv420p scene_02_trimmed.mp4
```

이 처리를 8개 장면에 적용한 후 순서대로 연결하고, 큐 시계 0에 해당 장면의 TTS 시작을 맞춘다. 큐 모드는 준비 영상을 그대로 연결하지 않도록 `--concat` 조합을 거부한다. `clock0_video_s`는 지정한 단조 시계 기준의 준비 길이이며, 인코더 첫 프레임의 PTS를 실측한 값은 아니다. Claude는 완성 영상에서 프레임 경계·표 가독성·실제 선택자·WebGL·큐 지연을 확인해야 한다. Codex는 Chromium을 실행하지 않는다.

커밋 단위 제안: `feat: 내레이션 큐 기반 녹화 모드`. 커밋과 영상 파일 추가는 수행하지 않는다.

## 영상 v2 — 원리와 장비 동작 (6장면, 217초)

`record_demo.py`는 v1 그대로 유지한다. v2는 승인된 저장소 밖 대본과 `tts/timing.json`을 읽기만 하며, 문장 시작 시각에 맞춘 `tools/cues_v2.json`을 사용한다. 공정·결과 입력은 바꾸지 않는다. 장면 29의 필름 눌림과 31의 여러 층 반복은 문장 길이에 맞춘 진행률 편집 표시이며 실제 공정 시간이 아니다. 나머지 재생은 기존 지원 속도에서 종점을 지키고 정지한다. 35번은 `reflow-4` 승온부터 `reflow-5` 피크 진입까지 보인다.

```bash
python3 -m py_compile media/tools/record_v2.py
python3 media/tools/record_v2.py --plan \
  --timing "$HOME/Desktop/MSE489/기말보고서/영상/v2/tts/timing.json"
# Chromium 실행 가능 환경에서 Claude가 실행. 로컬 서버는 저장소 루트 자산 제공 필요.
python3 media/tools/record_v2.py --url http://localhost:8000/web/ \
  --card media/tools/compare_card.html \
  --timing "$HOME/Desktop/MSE489/기말보고서/영상/v2/tts/timing.json" \
  --cues media/tools/cues_v2.json --out media/out/v2 --captions
# 부분 재녹화: 새 출력 폴더에 --scene 4 --scene 5 (반복 지정 가능)
```

Playwright Chromium에 `--use-angle=swiftshader --enable-unsafe-swiftshader`를 전달하고, 장면마다 새 context에서 viewport·video 모두 1920×1080으로 녹화한다. 비교 카드는 `file://`로 연다. 로드·GLB 성공·factory ready·view-only·모드/초기 단계/카메라·CAD 비교 이미지·두 프레임 반영까지 **준비 구간**으로 분리한다. 이후 clock0부터 `timing.json`의 `video_s`만큼 유지한다. 출력 폴더는 비어 있어야 하며 실패 시 중단하고 부분 영상과 실패 매니페스트를 남긴다.

`scene01.webm`~`scene06.webm`은 준비 구간을 포함한다. `scenes.json`의 `clock0_video_s`는 비디오 핸들을 받은 직후 단조 시계 기준으로 추정한 준비 길이이고, `duration_s`는 원본 `video_s`다. 준비 끝에 순백 동기 플래시를 0.3 s 표시하고 제거 후 rAF 두 번을 거쳐 clock0을 잡는다. `sync_flash.shown_s`/`removed_s`는 started 기준이며, 트리밍은 영상에서 마지막 플래시 다음 프레임을 clock0으로 쓴다. `python3 media/tools/trim_v2.py media/out/v2`는 디코드 후 플래시 끝을 검출해 `duration_s` 길이의 `trim/sceneNN.mp4`(30 fps, H.264, yuv420p, 1920×1080, 무음)를 만들고, 마지막 한 프레임 부족은 복제로 채우며 검출 시각과 매니페스트 추정값 차이를 `trim/sync_report.json`에 저장한다. cue별 `t`/`actual_s`/`late_s`/`status`와 `ended_s`를 기록한다. `actual_s`는 clock0 기준 실행 시작이며 `late_s`는 계획보다 늦은 시간이다. 실패 cue는 `error`도 기록한다. 준비 시간이 본편 길이를 소모하지 않는다.

`--plan`은 브라우저 없이 6장면·42문장의 자막/시작 시각 대응, 시간 범위·순서, 실제 단계 ID/재생 길이, 대상의 파일·문자열 근거를 검사하고 표를 출력한다. DOM 생성 코드의 정적 계약 검사이며 실제 배포본·WebGL·레이아웃 검증은 Claude가 한다. 장면 제목(`--captions`)은 왼쪽 위(위 18px·왼쪽 24px, 24px 글꼴)에 둔다. 하단 중앙에 두면 공장 페이지 하단 고정 개념 애니메이션 문구를 가리기 때문이다. 별도 burn-in 자막은 바닥 110px 위에 둔다.

비교 카드 API: `window.card.showRow(1..3)`는 이전 행을 유지하며 페이드인, `focus(r, 0)`은 행 전체, `focus(r, 1)`은 TC-NCF, `focus(r, 2)`는 MR-MUF를 강조한다. `reset()`은 제목과 근거 문구만 남긴다. 카드의 색과 SVG는 단일 HTML 안에 있으며 외부 자원을 사용하지 않는다. CAD cue는 실제 목록 버튼 이름·`#explode` 입력 이벤트·`#comparison`/`#drawings` 스크롤·캔버스 드래그를 사용한다. targets에 근거 파일과 문자열을 함께 보관한다.
