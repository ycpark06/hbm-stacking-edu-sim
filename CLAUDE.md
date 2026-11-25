# CLAUDE.md — 작업 규칙

이 저장소에서 작업하는 Claude Code가 매 세션 시작 시 읽는 문서다.

## 1. 프로젝트 요약

UNIST MSE489 첨단패키징기술 기말 대체 PBL 과제. 중간 과제의 **교육용 데스크톱 다이본더**를 **다단 적층(HBM 방식) 본더**로 고도화하고, 한 장비에서 **TC-NCF 모드와 MR-MUF 모드**를 비교한다. 실물 없이 **시뮬레이션(디지털 트윈)** 으로 구동하며 GitHub Pages 웹 페이지로 시연한다.

- 전체 계획: [`docs/PLAN.md`](docs/PLAN.md) — 작업 전에 해당 단계 내용을 확인한다.
- 계획과 다르게 진행해야 하면 먼저 사용자에게 묻고, 승인되면 `docs/PLAN.md`를 고친 뒤 작업한다.

## 2. 반드시 지킬 원칙

1. **원문 KPI와 설계 목표를 구분한다.**
   - 원문 KPI (PBL 7쪽): 정합 반복정밀도 ±1 μm, 펄스 히터 최고 400 ℃, 최대 본딩 하중 50 N, 풋프린트 가로·세로 ≤ 600 mm
   - 원문 요구 (PBL 9쪽): 피드백 주기 10 ms
   - 원문에 없는 수치는 KPI라고 쓰지 않는다. "설계 목표" 또는 "파생 요구"로 표기하고 근거를 적는다.
2. **질량과 높이는 판정 대상이 아닌 참고값이다.**
3. **공정 조건은 가정값이라고 표기한다.** SK하이닉스와 삼성전자는 세부 공정 조건을 공개하지 않았다. 강의 수치를 우선 쓰고, 나머지는 문헌값이나 가정값으로 두고 출처를 적는다. 가정값은 `sim/params.json` 한 곳에 모은다.
4. **계산 모델은 중간 보고서 모델을 기준으로 한다.** `calc/`의 Python 원본과 `sim/`의 JS 이식본은 같은 입력에서 같은 결과를 내야 한다. 이를 확인하는 테스트를 둔다.
5. **사용 도구:** Autodesk Fusion(Mac), Python, JS, C. COMSOL은 쓰지 않는다.
6. **결과를 보고할 때** 원문 KPI, 설계 목표, 참고값, 가정값을 구분해서 쓴다.

## 3. 폴더별 역할

| 폴더 | 내용 |
|---|---|
| `docs/` | 계획서, 요구사항, 보고서 원고(`report/`), 실습 매뉴얼(`manual/`), 발표 자료(`presentation/`) |
| `calc/` | Python 계산 모델과 결과 JSON |
| `firmware/src/` | 제어 로직 C 코드 (하중 PI 1 ms, 온도 PI 10 ms, 인터락) |
| `firmware/hal/` | 하드웨어 추상 계층. MCU용과 웹용을 바꿔 끼운다 |
| `firmware/build/` | `controller.bin` (MCU), `controller.wasm` (웹) |
| `sim/` | 시뮬레이션 엔진 (JS), `params.json`, 테스트 |
| `web/` | `index.html`, 3D 뷰어, HMI. GitHub Pages 배포 대상 |
| `cad/` | Fusion 스크립트, STEP, GLB, `drawings/` (2D 제작 도면) |
| `wiring/` | 배선도 |
| `media/` | 영상 링크, 캡처 |

**파일 저장 규칙**
- 웹이 읽는 파일(GLB, JSON, wasm)은 **일반 커밋**으로 올린다. GitHub Pages는 LFS 파일을 제대로 서비스하지 못한다.
- 일반 커밋 파일은 100 MB를 넘기지 않는다. 큰 원본(STEP 등)은 LFS를 쓰고, 영상은 Releases나 외부 링크로 둔다.
- 학번 등 개인정보를 저장소에 넣지 않는다 (공개 저장소).

## 4. Git 규칙

1. **작업 전에 브랜치를 만든다.** `main`에 직접 커밋하지 않는다. 브랜치 이름은 `docs/PLAN.md` 11.2절을 따른다.
2. **작게 커밋한다.** 기능 단위로 나눈다. 접두어: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `cad:`, `chore:`, `build:`
3. **PR로 병합한다.** `.github/pull_request_template.md`의 리뷰 체크리스트를 채우고, 리뷰 의견과 반영 내용을 기록한 뒤 병합한다.
4. **문제가 생기면 Issue에 기록한다.** 순서: 증상 → 원인 분석 → 해결 → 결과. 라벨: `bug`, `model`, `firmware`, `ui`, `cad`, `docs`
5. **해결한 Issue는 README 트러블슈팅 로그에 한 줄로 반영한다.**
6. **태그:** 중간 자산 이관 직후 `v1.0-midterm`, 최종 제출 시 `v2.0-final`
7. **작업 분담:** 코드·문서 작성은 Codex가, 검증은 Claude가 맡는다.
   - Claude는 작업을 나누고 브랜치를 만든 뒤 `codex exec`로 Codex에게 작업을 지시한다. 지시에는 목표, 파일 위치, 완료 기준, 지켜야 할 원칙(CLAUDE.md 2절)을 포함한다.
   - Codex가 끝내면 Claude가 검증한다: (1) PLAN 10절 폴더 구조, (2) 테스트 통과 (모델은 golden vector 일치), (3) 원문 KPI·설계 목표·가정값 구분 표기, (4) HANDOFF 또는 PLAN의 완료 기준.
   - 실패하면 Claude가 원인을 Issue로 남기고 Codex에게 수정을 다시 지시한다.
   - 통과하면 Claude가 PR을 만들고, 체크리스트의 '리뷰 의견과 반영 내용'에 검증 결과와 수정 이력을 적는다. PR 설명에 작성자(Codex)·리뷰어(Claude)를 밝힌다.

## 5. 펌웨어 빌드

제어 로직 C 코드 한 벌을 두 가지로 빌드한다 (SIL 검증).

```bash
# PC golden·성능·anti-windup·인터락 검증
make -C firmware test
# STM32H743 → controller.elf/.bin, size 출력
make -C firmware mcu
# Emscripten ES module → controller.js/.wasm
make -C firmware wasm
# Node 고정 입력 PC ↔ wasm 검증 (별도 타깃)
make -C firmware test-wasm
```

필요한 도구: `make`, C99 `cc`, `python3`, `arm-none-eabi-gcc`·`objcopy`·`size`, `emcc`, `node`.
하중 1 ms·온도 10 ms의 공통 float 제어기를 PC/MCU/wasm HAL과 연결한다.
실물 bring-up은 범위 밖이며 자세한 인터페이스와 검증은 `firmware/README.md`를 따른다.

## 6. 웹 실행과 배포

```bash
# 로컬 실행 (단계 4에서 확정)
# 예: python3 -m http.server -d web 8000

# 배포: GitHub Pages (단계 4에서 설정 방법을 채운다)
```

## 7. Chat 작업물 받기 (inbox)

코드·문서 초안 일부는 Claude 앱(Chat)에서 만들어 `~/Desktop/MSE489/기말보고서/inbox/<번호_작업명>/`에 넣는다. 저장소(`repo/`)에는 Chat이 직접 쓰지 않는다.

- 사용자가 "inbox/<폴더> 가져와"라고 하면: 해당 폴더의 `HANDOFF.md`를 먼저 읽고 → 지정된 브랜치를 만들고 → 지정 위치로 복사 → 테스트 실행 → 기능 단위 커밋 → PR 생성
- 테스트가 실패하거나 내용이 계획과 다르면 커밋하지 말고 Issue로 기록한 뒤 사용자에게 보고한다.
- 가져온 뒤 inbox 폴더는 지우지 않고 그대로 둔다.

## 8. 보고 규칙

- `docs/PLAN.md` 12절의 각 단계가 끝나면 사용자에게 보고하고, 확인을 받은 뒤 다음 단계로 넘어간다.
- 보고 내용: 완료한 것, 완료 기준 충족 여부, 생긴 문제와 Issue 번호, 다음 단계에서 정할 것

## 9. 중간 과제 자산 위치 (사용자 Mac)

폴더 구성: `~/Desktop/MSE489/` 아래 `강의자료/`(공통), `중간보고서/`, `기말보고서/`(이 저장소는 `기말보고서/repo/`)

| 자산 | 위치 (`~/Desktop/MSE489/` 기준) |
|---|---|
| 강의 PDF / 강의 정리 md | `강의자료/`, `강의자료/상세정리/` |
| 중간 최종 제출본 (보고서·발표) | `중간보고서/01_최종제출/` — 학번·이름이 들어 있으므로 저장소에 복사하지 않는다 |
| 보고서 원고 (장별 md) | `중간보고서/02_설계보고서_작업/01_문제정의.md` ~ `14_결론.md` |
| 그림 / 계산 스크립트·결과 | `중간보고서/02_설계보고서_작업/fig/`, `calc/` |
| 보고서 PDF | `중간보고서/02_설계보고서_작업/MSE489_교육용다이본더_설계보고서.pdf` (60쪽) |
| PDF 빌드 | 위 폴더에서 `python3 build_final.py` (Playwright Chromium, Noto Sans CJK 필요) |
| 도면 스크립트 | `중간보고서/02_설계보고서_작업/fig/dwg/` |
| Fusion 모델링 스크립트 | `중간보고서/03_CAD/DieBonderModel/DieBonderModel.py` |
| Fusion 실행 결과 | `중간보고서/03_CAD/DieBonderModel/out/` (이미지, STEP, summary.json) |
| 중간 발표 자료 소스 | `중간보고서/04_발표/발표자료_소스/` |
| 기말 과제 안내 | `기말보고서/00_과제안내/` |

**Fusion 스크립트 실행:** Fusion에서 뷰 메뉴 → 텍스트 명령 표시 → Py 모드를 고르고 아래 한 줄을 입력한다. 파일 선택 창은 macOS 보안 때문에 자동 조작이 안 되므로 이 방식을 쓴다.

```python
g={'__file__':__import__('os').path.expanduser('~/Desktop/MSE489/중간보고서/03_CAD/DieBonderModel/DieBonderModel.py')};exec(open(g['__file__'],encoding='utf-8').read(),g);g['run'](None)
```

## 10. 중간 보고서 핵심 결과 (모델 재사용 기준)

| 장 | 핵심 |
|---|---|
| 3 시스템 | 고정 헤드 + 이동 기판, 조동+미동 2단 스테이지, 빔스플리터 듀얼 비전, 운전 모드 4개 |
| 4 공정 물리 | 스퀴즈 유동(BLT ∝ 하중×시간), 체적 보존(필렛), 경화 아레니우스, 휨 티모셴코 식, TCB는 자기정렬 없음 |
| 5 오차 예산 | RSS 3σ 0.88 μm (≤ 1 μm), 열드리프트가 가장 큼 |
| 7 열 | 히터 AlN 20×20×5 mm, 400 W, 22 K/s, 정렬은 설정 온도 도달 90 s 후 |
| 9 비전 | NCC + 가우시안 서브픽셀 + 평탄화 보정, 폐루프 정렬 3σ 0.09 μm |
| 10 제어 | 하중 1 ms PI (초과량 ≤ 0.035 N), 온도 10 ms PI (±0.42 ℃), 안전 계층 52 N/410 ℃ 경고, 55 N/420 ℃ 차단 |
| 11 CAD | Fusion 43부품, 590×480 mm, 간섭 0 |
| 13 교육 | 언더필 충전 Washburn 식, DoE 2⁴⁻¹ |
