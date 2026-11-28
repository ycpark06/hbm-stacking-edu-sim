# 기말 발표 자료

8장 PowerPoint 공개판과 슬라이드 노트 대본, 6분 데모 체크리스트입니다. 내용은 `deck.json`, 배치는 `build.js`에서 관리합니다. 중간 발표 `소스/build.js`를 복사해 pptxgenjs 방식·글꼴·팔레트·도형 이름·노트 처리를 확장했고, 중간 `slides.json`·`deck.json`은 형식만 참조했습니다. HTML 추출 경로는 사용하지 않습니다. 원본은 수정하지 않았습니다.

## 빌드

이미 설치된 pptxgenjs 3.12.0을 사용하며 추가 설치는 필요하지 않습니다.

```sh
cd docs/presentation
node build.js
# MSE489_기말발표.pptx — 이름 없는 공개판
```

제출용은 Claude가 로컬에서만 만듭니다. 실제 개인정보 JSON과 제출용 PPTX는 저장소 밖에 둡니다. `--cover-local`은 `members[].name`, `members[].id`만 표지 텍스트에 사용하며 입력값을 로그·내용 JSON·메타데이터에 쓰지 않습니다. 저장소 안 출력과 `--out` 없는 제출용 빌드는 거부합니다. 공개판은 로컬 개인정보 파일을 자동으로 찾거나 읽지 않습니다.

JSON 형식 설명(실제 파일을 저장소에 만들지 않음): `{"members":[{"id":"학번 문자열","name":"이름 문자열"}]}`

```sh
node build.js --cover-local /저장소밖/표지정보.json --out /저장소밖/제출용.pptx
```

16:9 13.333×7.5 in, 맑은 고딕, 남색 중심 중간 팔레트를 사용합니다. 표지 44 pt, 제목 32 pt, 본문·표 18 pt 이상입니다. 장 번호 13 pt와 쪽 번호 12 pt는 공통 틀의 예외입니다. 도형 이름은 `슬라이드ID_종류번호`입니다. 모든 설명은 노트의 ~습니다체 대본으로 이어집니다. 공개판에 개인정보가 들어가지 않도록 작성자 메타데이터도 과목 코드로 고정했습니다.

## 슬라이드 구성과 시간

| # | ID | 메시지·구성 | 지정 시간 | 10분 운영 |
|---|---|---|---|---|
| 1 | cover | 장비 렌더와 제목 | 별도 시간 없음 | 즉시 전환 |
| 2 | scope | 두 공정 좌우 비교표 | 30 s | 30 s |
| 3 | system | 3D 장비 + 편집 가능한 구조도 | 40 s | 40 s |
| 4 | results | S1~S5 핵심 수치·해석 표 | 60 s | 55 s |
| 5 | trouble | 증상·원인·수정·결과 3×4 표 | 60 s | 55 s |
| 6 | improve | 중간 대비 7개 항목 비교표 | 30 s | 25 s |
| 7 | demo | 번호를 붙인 가로 흐름, 웹 URL | 6 min | 6 min |
| 8 | wrap | 남은 한계와 제작 후 시험, 결론 | 40 s | 35 s |

HANDOFF 지정 장별 합은 **4분 20초 + 데모 6분 = 10분 20초**입니다. 지정 시간은 `deck.json.seconds`에 보존했습니다. 10분 운영은 4·5·6·8장의 노트에서 각 5초 축약 안내를 따라 **슬라이드 4분 + 데모 6분**으로 진행합니다. 실제 발화 속도는 리허설에서 확인해야 합니다.

## 그림 출처

| 복사본 | 원본 | 사용 |
|---|---|---|
| `fig/view_iso.png` | `cad/stacker/out/view_iso.png` | 표지·시스템의 동일 장비 확인용 렌더 |
| `fig/ch17_head_comp.png` | `docs/report/final/fig/ch17_head_comp.png` | 기존 보조 그림 복사본 보존 (P8에서 슬라이드 사용 제외) |

그림은 비율을 유지하며 원본을 수정하지 않았습니다. P8에서 5장의 작은 보조 그림을 편집 가능한 32 pt 수치 강조 “208.5 → 약 231 ℃”로 교체했습니다. 1층 자기 접합 최고의 기본 조건과 헤드 보정 시 계산 결과이며, 핵심 해석은 18 pt 표에 유지했습니다. 시스템 구조도는 README 2절과 보고서 16.1절을 단순화한 PowerPoint 도형입니다. 스택 열 모델의 이상 경계와 독립 SIL의 구분을 유지했습니다.

## 수치 출처 대조표

경로는 저장소 루트 기준입니다. JSON 배열 인덱스는 0부터 시작합니다. `representative[id=Sx]`는 해당 id의 항목을 선택한다는 표기입니다. 모든 반올림은 표시용이며 원래 정밀값·판정을 바꾸지 않습니다.

| 슬라이드 | 표시 수치·구분 | 출처 파일·키 또는 절 |
|---|---|---|
| 3 | STM32H743, .bin / .wasm (대상·산출물) | `firmware/README.md`; `docs/report/final/16_디지털트윈.md` 16.1~16.2절 |
| 4·5·7 | S1 기본 208.5 / 215.8 ℃ (계산 결과) | `sim/test/bond_temp_results.json:S1[0].thermal_layers[0,1].bond_peak_C` |
| 4·5·7 | 액상선 221 ℃ (문헌값) | `sim/params.json:solder.liquidus_snag.value`; `bond_temp_results.json:S1[0].alarms[].liquidus_C` |
| 4·5·7 | 보정 시 전 층 약 231 ℃ (계산 결과), 목표 231 ℃ (설계값) | `sim/test/bond_temp_results.json:S1[1].thermal_layers[].bond_peak_C`, `S1[1].head_compensation.target_C` |
| 4·7 | 필요 헤드 최대 약 341 ℃, KPI까지 약 59 ℃ (계산 결과) | `sim/test/bond_temp_results.json:S1[1].head_compensation.layers[].required_head_C`, `.headroom_C`; `docs/report/final/15_적층공정모드.md` 15.2절, `17_트러블슈팅_개선성과.md` 17.2.1절의 반올림 값·여유 |
| 4·7 | 400 ℃ (원문 KPI) | `docs/requirements.md` 1절; `sim/test/bond_temp_results.json:S1[1].head_compensation.limit_C` |
| 4·7 | S2 TC (0.24, −1.16), MR (0.04, 0.01) μm (단일 표본 관찰값) | `sim/test/stage4_results.json:representative[id=S2].results[0,1].alignment.cumulative_um` |
| 4·7 | S3 100→50 μm, TC / MR 4.1배, 50 μm 둘 다 불량 (계산 결과·설계 목표 판정) | `sim/test/stage4_results.json:representative[id=S3].results[].recipe.thickness_um`, `.warpage.thickness_half_ratio`, `.warpage.judgement`; 보고서 15.3절 |
| 4·7 | S4 본더 240 / 41 s, MR 배치 14,826 s (계산 결과) | `sim/test/stage4_results.json:representative[id=S4].results[0,1].cycle.bonder_s`, `results[1].cycle.batch_post_s` |
| 4·7 | 후경화 4 h (문헌값), 라인 UPH 미산출 | `sim/test/stage4_results.json:representative[id=S4].results[1].cycle.breakdown.once.postcure_s` = 14,400 s; 보고서 15.7절 |
| 4·5·7 | S5 15 μm, 압력 0에서 893 s·미충전 89 %, 1 MPa에서 3.3 s (계산 결과) | `sim/test/stage4_results.json:representative[id=S5].results[recipe.gap_um=15,recipe.inlet_pressure_MPa=0 또는 1].muf.fill_time_s`, `.muf.unfilled_fraction` (비율×100, 정수 반올림) |
| 4·5·7 | 입구 1 MPa (가정값), 간격 15 / 7 μm (문헌값 조건), 7 μm 필러 불량 | `sim/params.json:muf.applied_pressure`; `geometry.interlayer_gap`; `sim/test/stage4_results.json:representative[id=S5].results[].recipe`, `.muf.filler_blocked`, `.defect_judgement`; 보고서 15.5절 |
| 5 | 접촉 열저항 estimate (역산 추정값) | `sim/params.json:thermal_stack.tool_contact_R_area`, `thermal_stack.chuck_contact_R_area`; 보고서 17.2.1절 |
| 5 | anti-windup 고착 초과량 3.58→0.057 N (동일 시험 조건 계산 결과) | `firmware/README.md` Validation 3/검증 결과; `docs/report/final/17_트러블슈팅_개선성과.md` 17.2.3절 |
| 6 | 중간 대비 7개 항목 (정성 비교) | `docs/report/final/17_트러블슈팅_개선성과.md` 17.3절 |
| 7 노트 | MR 약 250 ℃ (계산 결과), 기본 8단 / S1 12단 (입력 조건) | `sim/test/bond_temp_results.json:S1[2].thermal_layers[].bond_peak_C`; `sim/params.json:recipe.layers`; `stage4_results.json:representative[id=S1].recipes` |
| 7 노트 | 과하중 래치 55 N (안전 설계값) | `sim/params.json:equipment_limits.force_latch_N`; `web/js/hmi.js` 알람 버튼; `firmware/README.md` |
| 8 | 냉각 피크→180 ℃, 전 구간 4 K/s 설계 목표 FAIL/REVIEW | `calc/hardware/reflow_heater.json:results.forced_cooling_design_segment.end_C`, `.required_min_K_s`, `.maintains_required_rate`; `verdict.status`; 보고서 15.9절 |

원문 KPI 충족을 새로 선언하지 않습니다. 원문 KPI는 ±1 μm, 400 ℃, 50 N, 가로·세로 ≤600 mm이며 피드백 10 ms는 원문 요구입니다. 질량·높이는 참고값입니다. 업체 주장은 관찰 항목(판정 없음)이며 계산 입력과 분리합니다. S3 업체 주장 불일치, 냉각 FAIL/REVIEW, NCF 정량 모델 없음, TC 하부층 미달을 보존했습니다.

## 검증·후속 확인

`node build.js`로 공개판을 생성합니다. PPTX ZIP/XML의 8장·도형 이름·노트·글꼴 크기·외곽 범위를 검사하는 `python3 verify_pptx.py`를 함께 제공합니다. P8에서는 수정 대상(4장 모든 표 셀, 5장 강조 수치, 6장 제목, 8장 결론)에 한글/전각 1 em·영숫자 0.55 em·공백 0.3 em 추정 폭의 15% 여유와 줄 높이를 검사합니다. 4장 표·주석·쪽 번호 사이와 8장 목록·결론 사이 간격도 검사합니다. 실제 대체 글꼴 측정값이 아니며 PowerPoint 줄바꿈·렌더링 확인을 대체하지 않습니다. PDF 변환·슬라이드 이미지 확인·제출용 빌드는 Claude 담당이며 여기서는 실행하지 않습니다. 브라우저·PowerPoint를 실행하거나 우회하지 않았습니다. 커밋·push·PR·Issue·태그 변경도 하지 않습니다.

검사 기록(2026-11-28): 공개판 `node build.js` 성공, 8장·89개 도형 이름·4개 native 표·전체 노트·폰트 크기·표 행 높이·외곽 범위 검사 통과. 두 그림 복사본은 원본과 바이트 일치합니다. `git diff --check` 통과. 전체 tracked 파일의 `git grep -I -l -E`와 새 발표 소스의 `git grep --no-index --exclude-standard -I -l -E`에서 이메일 및 실제 학번 형태의 `name/id` 값 패턴은 모두 출력 없음(exit 1)이었습니다. PPTX XML에서도 이메일·학번 패턴이 없고 공개 표지 문구를 확인했습니다. 일반 문서에 나오는 ‘이름·학번’이라는 필드 설명은 개인정보 값이 아닙니다. 패턴 검색은 임의의 실명을 완전하게 판별하지 못하므로 새 파일의 표지·대본·메타데이터도 직접 대조했습니다.

커밋 단위 제안(커밋하지 않음): `docs: 기말 발표 빌드 스크립트와 슬라이드 내용`, `docs: 발표 그림과 데모 체크리스트`, `docs: README 발표 자료 위치`. 공개 PPTX와 빌드 검증 스크립트·수치 대조표는 첫 단위에 포함합니다. 기존에 준비된 package 파일은 그대로 유지했습니다.

P8 배치 수정(2026-11-28): 4장 첫 열을 0.9 in으로 넓히고 S1·S5 행을 0.9 in, S2·S3 행을 0.8 in, S4 행을 0.82 in으로 늘렸습니다. 주석은 y=6.65 in, 쪽 번호는 y=7.05 in으로 내려 분리했습니다. S1은 “보정 시 전 층”으로 명확히 했습니다. 6장 제목을 줄이고, 8장 한계 목록 간격을 0.55 in으로 줄인 뒤 결론을 y=5.95 in으로 내려 마지막 목록 상자와 0.62 in 간격을 확보했습니다. 공개판 재빌드 및 27개 텍스트·표 셀의 폭 여유/높이 검사 통과. Mac PowerPoint PDF 재렌더링은 Claude 확인 사항입니다.

P8 커밋 단위 제안(커밋하지 않음): `fix: 발표 슬라이드 배치와 대체 글꼴 여유 검사` — build.js, deck.json, verify_pptx.py, 공개 PPTX, 이 README의 P8 기록.
