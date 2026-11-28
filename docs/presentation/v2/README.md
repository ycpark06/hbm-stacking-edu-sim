# 발표 v2

공개판 21장, 노트 합계 210초(3분 30초), 평균 10초. 승인 개요 22장의 5·6번을 GitHub·Pages 한 장으로 합쳤고 두 장의 12초를 유지했다. 나머지 순서·말할 문장·시간은 유지했다. 부록은 추가하지 않았다.

발표 흐름: 1~5번 50초 → 6번 영상 전환 5초 → 7번 데모 전환 5초 → 8~21번 150초. 영상 약 210초와 실제 데모 약 180초는 슬라이드 설명 시간에서 제외한다. 기존 demo_checklist.md는 수정하지 않았다. 해당 파일의 데모 내용은 v2 7번에서 연결한다.

## 빌드

작업 트리 루트에서 실행한다. Node 의존성은 기존 package-lock.json을 사용한다.

```sh
npm ci --prefix docs/presentation
python3 -m pip install matplotlib pillow
python3 docs/presentation/v2/make_charts.py
node docs/presentation/v2/build_v2.js
python3 docs/presentation/v2/check_v2.py
```

이 환경에서는 설치된 패키지가 있는 `~/.venv/bin/python`으로 Python 단계를 실행했다. 그래프는 Agg, Pretendard, 저장 JSON의 원값을 사용하며 시뮬레이션을 다시 실행하지 않는다. 숫자를 반올림할 때 원값은 numeric_manifest.json에 남긴다. 데이터 변경은 make_charts.py → build_v2.js → check_v2.py 순서로 재생성한다.

기본 출력은 `MSE489_기말발표_v2.pptx`, 이름·학번 없는 공개판이다. 제출용 표지 입력은 선택 사항이며 이 작업에서는 읽거나 실행하지 않았다.

```sh
node docs/presentation/v2/build_v2.js --cover-json <경로> --out <경로>
```

입력 형식은 `{"members":[{"name":"이름","id":"학번"}]}`. 개인정보 출력은 저장소 밖 PPTX 경로만 허용하고, 표지 이름·학번 칸에만 넣는다. 개인정보를 로그·JSON 진단 파일에 저장하지 않는다. 기본 공개판 경로를 덮어쓰지 않는다.

## 글꼴과 화면

Pretendard → 맑은 고딕 → Apple SD Gothic Neo 순서로 수동 대체한다. PPTX는 대체 목록을 보관하지 않으므로 발표 PC에 Pretendard Regular/Bold를 설치하는 방법을 권장한다. 폰트 파일은 임베드하지 않았다. 테마 latin·ea·Hang과 모든 편집 텍스트는 Pretendard, 강조는 bold다. 그래프는 Pretendard로 래스터 출력한다.

흰 바탕, 남색 #14365A, 본문 #44505F, 주황 #C2622A, 보조선 #E6ECF3의 5색을 사용한다. 실제 캡처·CAD 재질의 원래 색은 유지했다. 제목 32pt, 본문 22pt 이상, 주소 17pt. 편집 가능한 C/HAL 구조도를 제외한 증거 이미지는 원본 비율을 유지한다. 그래프 원값과 소스는 JSON·Python으로 수정한다.

`assets/`에 공개 증거 영역을 함께 제공해 빌드가 작업 트리 밖 자료에 의존하지 않는다. `asset_sources.json`에 캡처 출처·크롭 좌표를 기록했다. GitHub는 날짜·상대 시간·기여자 영역을 제외한 실제 폴더 영역, PR은 제목만 사용한다. 캡처 속 글자는 본문 어절 검사에서 제외하며 읽기 자료로 확대하지 않는다.

`cad_light_all.png`는 제작 당시 없으므로 3번은 기존 `media/stills/cad_overview.png`의 3D 영역을 사용했다. light 전체 캡처가 도착하면 아래 명령으로 캡처를 갱신한 뒤 PPT를 재빌드한다. 그 밖의 light 캡처는 제공된 원본을 사용했다. 원리·공장 순서는 슬라이드에서 다시 설명하지 않는다.

```sh
python3 docs/presentation/v2/prepare_assets.py --design-dir <승인된_design_review_경로>
node docs/presentation/v2/build_v2.js
python3 docs/presentation/v2/check_v2.py
```

## 장별 제목과 시간

| v2 | 승인 개요 | 제목 | 초 |
|---:|---:|---|---:|
| 1 | 1 | 단일 다이 설계를 두 적층 공정 비교로 넓혔다 | 8 |
| 2 | 2 | 같은 조건에서 두 공정을 비교할 도구가 필요했다 | 10 |
| 3 | 3 | 장비 설계를 웹에서 살펴볼 수 있다 | 10 |
| 4 | 4 | 같은 C 제어기를 MCU와 웹으로 빌드했다 | 10 |
| 5 | 5·6 | 영상에서 본 저장소에 계산과 변경 근거를 남겼다 | 12 |
| 6 | 7 | 두 공정의 원리와 장비 동작은 영상으로 본다 | 5 |
| 7 | 8 | 계산 결과와 고장 복구를 직접 확인하겠다 | 5 |
| 8 | 9 | 결과를 맞추기보다 미달 원인을 남겼다 | 10 |
| 9 | 10 | 기본 레시피에서는 아래 두 층이 액상선에 못 미쳤다 | 12 |
| 10 | 11 | 열저항을 되돌리면 온도 미달의 원인이 가려진다 | 12 |
| 11 | 12 | 선택 보정으로 전 층이 계산상 목표 온도에 도달했다 | 12 |
| 12 | 13 | 얇은 칩에서는 두 모드 모두 휨 불량이 남았다 | 10 |
| 13 | 14 | 본더 점유가 짧아도 라인 생산성은 아직 모른다 | 10 |
| 14 | 15 | 가정한 입구 압력에서는 충전 시간이 줄었다 | 10 |
| 15 | 16 | 충전이 끝나도 좁은 간격의 필러 불량은 남는다 | 10 |
| 16 | 17 | 적분 누적을 막자 고착 뒤 하중 초과가 줄었다 | 10 |
| 17 | 18 | 불가능한 램프는 실행 전에 거부한다 | 10 |
| 18 | 19 | PC와 웹 제어기의 출력 일치를 확인했다 | 10 |
| 19 | 20 | 중간의 설계 계산을 조작 가능한 실습으로 바꿨다 | 12 |
| 20 | 21 | 냉각 계산은 아직 설계 목표에 못 미쳤다 | 12 |
| 21 | 22 | 다음은 추정 입력과 보정 조건을 실물로 확인할 차례다 | 10 |

## 수치 대조표

아래 표는 작업 문서이며 슬라이드에는 표를 넣지 않았다. 경로는 작업 트리 루트 기준이다. 승인 개요의 `docs/report/final/`은 현재 트리에 없어서 동일한 보존 자료 `docs/report/archive_v1/`을 실제 근거로 사용했다. `numeric_manifest.json`은 원값 전체와 배열 인덱스를 보관하고 check_v2.py가 소스 파일의 키를 다시 읽어 정확히 비교한다.

| 슬라이드 | 수치 또는 결과 | 출처 파일 | 키 | 범주 |
|---:|---|---|---|---|
| 9 | 12층 peak_C 208.539525693~253.079147276 ℃ | `sim/test/stage4_results.json` | `representative.0.results.0.thermal_layers` | 계산 결과 |
| 11 | 12층 peak_C 208.539525693~253.079147276 ℃ | `sim/test/stage4_results.json` | `representative.0.results.0.thermal_layers` | 계산 결과 |
| 11 | 12층 peak_C 230.992603718~231.011188698 ℃ | `sim/test/stage4_results.json` | `representative.0.results.1.thermal_layers` | 계산 결과 |
| 12 | 7.413174969357404 | `sim/test/stage4_results.json` | `representative.2.results.0.warpage.max_um` | 계산 결과 |
| 12 | 30.715646567469317 | `sim/test/stage4_results.json` | `representative.2.results.1.warpage.max_um` | 계산 결과 |
| 12 | 5.406727729136941 | `sim/test/stage4_results.json` | `representative.2.results.2.warpage.max_um` | 계산 결과 |
| 12 | 22.1990976477645 | `sim/test/stage4_results.json` | `representative.2.results.3.warpage.max_um` | 계산 결과 |
| 13 | 239.88600000000002 | `sim/test/stage4_results.json` | `representative.3.results.0.cycle.bonder_s` | 계산 결과 |
| 13 | 40.68600000000001 | `sim/test/stage4_results.json` | `representative.3.results.1.cycle.bonder_s` | 계산 결과 |
| 14 | 892.7665876475774 | `sim/test/stage4_results.json` | `representative.4.results.4.muf.fill_time_s` | 계산 결과 |
| 14 | 3.320933922451846 | `sim/test/stage4_results.json` | `representative.4.results.5.muf.fill_time_s` | 계산 결과 |
| 16 | 하중 응답 전체 rows, 초과량 3.57892777614 N, 0.057444963807 N | `docs/report/archive_v1/fig/ch17_force_data.json` | `runs` | 노이즈 없는 계산 시험 |
| 9 | {"layers": 12, "thickness_um": 100, "gap_um": 15, "inlet_pressure_MPa": 1, "bond_force_N": 40, "head_temp_compensation": false} | `sim/test/stage4_results.json` | `representative.0.results.0.recipe` | 계산 결과 |
| 9 | 12층 peak_C 208.539525693~253.079147276 ℃ | `sim/test/stage4_results.json` | `representative.0.results.0.thermal_layers` | 계산 결과 |
| 11 | 271.185302734~341.387939453 | `sim/test/stage4_results.json` | `representative.0.results.1.head_setpoints_C` | 계산 결과 |
| 13 | 14825.75 | `sim/test/stage4_results.json` | `representative.3.results.1.cycle.batch_post_s` | 계산 결과 |
| 15 | {"layers": 12, "thickness_um": 100, "gap_um": 7, "inlet_pressure_MPa": 3, "bond_force_N": 40, "head_temp_compensation": false} | `sim/test/stage4_results.json` | `representative.4.results.3.recipe` | 계산 결과 |
| 15 | 5.088470186138616 | `sim/test/stage4_results.json` | `representative.4.results.3.muf.fill_time_s` | 계산 결과 |
| 15 | 0 | `sim/test/stage4_results.json` | `representative.4.results.3.muf.unfilled_fraction` | 계산 결과 |
| 15 | True | `sim/test/stage4_results.json` | `representative.4.results.3.muf.filler_blocked` | 계산 결과 |
| 15 | 불량(필러 막힘) | `sim/test/stage4_results.json` | `representative.4.results.3.defect_judgement` | 계산 결과 |
| 11 | 221 C | `sim/params.json` | `solder.liquidus_snag` | 문헌값 |
| 11 | 10 degC | `sim/params.json` | `judgement.bond_temp_margin_C` | 설계값 |
| 11 | 400 degC | `sim/params.json` | `equipment_limits.head_max_temp_C` | 원문 KPI |
| 11 | 0.0002 m2K/W | `sim/params.json` | `thermal_stack.tool_contact_R_area` | 역산 추정값 |
| 11 | 0.0002 m2K/W | `sim/params.json` | `thermal_stack.chuck_contact_R_area` | 역산 추정값 |
| 14 | 1 MPa | `sim/params.json` | `muf.applied_pressure` | 가정값 |
| 14 | 5 Pa.s | `sim/params.json` | `muf.viscosity_at_fill` | 가정값 |
| 20 | {"kind": "design", "start_C": 250, "end_C": 180, "time_s": 17.07233588031998, "min_cool_K_s": 3.3931509463912066, "max_cool_K_s": 4.901870524272919, "average_cool_K_s": 4.1002004934012595, "required_min_K_s": 4, "rate_source": "sim/params.json reflow.ramp_down.value", "maintains_required_rate": false} | `calc/hardware/reflow_heater.json` | `results.forced_cooling_design_segment` | 설계 목표 / 계산 결과 |
| 20 | FAIL/REVIEW | `calc/hardware/reflow_heater.json` | `verdict.status` | 설계 목표 / 계산 결과 |
| 17 | 저레인지 기본을 1 N/s | `docs/report/archive_v1/17_트러블슈팅_개선성과.md` | `저레인지 기본을 1 N/s` | 설계 선택 |
| 18 | 14,400 출력값 | `docs/report/archive_v1/17_트러블슈팅_개선성과.md` | `14,400 출력값` | 저장된 독립 SIL 검증 결과 |
| 18 | 8.1e-6 | `docs/report/archive_v1/17_트러블슈팅_개선성과.md` | `8.1e-6` | 저장된 독립 SIL 검증 결과 |

표시 반올림과 해석:

- 9번: 기본 아래 두 층 208.5395/215.8478 ℃ < 문헌 액상선 221 ℃. 자기 접합 구간의 다이 중심 계산값이며 실제 솔더 접점 실측값이 아니다.
- 10번: 역산 추정 열저항과 기본 레시피를 보존했다. 보정 실행은 열저항·승온 속도·유지 시간을 유지하고 층별 헤드 설정만 바꾼다.
- 11번: 약 231 ℃는 결과 범위 230.992603718~231.011188698 ℃의 반올림. 설계 목표 231 ℃=문헌 액상선 221 ℃+설계 마진 10 ℃와 구분한다. 필요한 헤드 최대 341.387939453 ℃는 계산 결과이며 400 ℃는 원문 KPI다. 이상 헤드 경계 계산을 출력 제한 폐루프 성능·접합 품질 보증으로 확대하지 않는다.
- 12번: 두께 100/50 μm에서 휨 배율 TC 4.14338616, MR 4.10582866을 약 4.1배로 표현했다. 업체 우열이나 업체 박형 휨 주장 재현으로 설명하지 않는다.
- 13번: 본더 TC 239.886 s, MR 40.686 s를 240/41 s로 표시했다. MR 배치 후공정 14825.75 s는 별도이며 라인 UPH는 계산하지 않았다.
- 14번: 15 μm에서 0/1 MPa 결과 892.766587648/3.320933922 s를 893/3.3 s로 표시했다. 유효 입구 압력과 점도 5 Pa·s는 가정값이며 금형 압력과 구분한다.
- 15번: 7 μm·3 MPa에서 미충전 0 %여도 필러 불량을 유지한다. 미충전 면적률은 전체 보이드율과 다르다.
- 16번: 동일 고레인지 20 N·5 N/s, 속도 한계 ±0.5 mm/s, 고착 0.5 s의 저장 응답을 사용했다. 초과량 3.58/0.057 N은 노이즈 없는 시험 결과다.
- 17번: 1 N/s는 저레인지 기본 설계 선택이다. 정격 상한과 유효 강성 기준 약 0.999 N/s를 구분한다.
- 18번: 14,400 출력값, 최대 절대 차이 8.1e-6은 저장된 독립 PC/wasm 검증 결과다. 이번 빌드에서 SIL을 재실행하지 않았다.
- 20번: 피크~180 ℃ 최소 3.393150946/평균 4.100200493 K/s, 목표 4 K/s를 구분해 FAIL/REVIEW를 유지했다. 아래 온도 구간은 관찰 항목이다.

## 검사 결과와 Claude 인계

check_v2.py 통과: 21장, 노트 210초, 정의 본문 2~10어절. PPTX 실제 텍스트에서도 제목을 제외한 전체 어절 수 ≤20을 확인한다. 수치 원값 33건, 핵심 반올림·필러 판정, 그래프 파일 및 PPTX 삽입 해시, XML 구문, 개체 경계, 표 없음, 금지 수식어·날짜·학번/이름 라벨 패턴, 공개판 작성자 공란, 동아시아 폰트, 실제 Pretendard 글자 폭을 검사한다. 패턴 검사는 캡처 픽셀 안의 개인정보·날짜를 자동 판독하지 않으므로 증거 크롭을 별도로 육안 확인했다.

PowerPoint 실행과 PDF 변환은 사용자 지시에 따라 Claude가 한다. 현재 PowerPoint 렌더링 검수는 미완료다. PDF 전체 21장을 훑고, 특히 다음 장을 확대 확인한다.

- 3번: 기존 어두운 CAD 이미지의 배치와 light 전체 캡처 교체 여부.
- 4번: C/HAL 분기 선과 라벨, MCU/wasm의 관계.
- 5번: 저장소 폴더 캡처 크기, 저장소·Pages 주소 한 줄과 두 링크 작동.
- 7·19번: 가로로 긴 알람 캡처와 세로로 긴 결과 캡처의 가독성.
- 8번: PR 제목 한 줄이 날짜·개인정보 없이 보이는지.
- 9·10·11번: 승인 trouble_seq 3장과 제목·판단·전후 차트 구성 비교, 동일 0~300 ℃ 축, 12층 라벨과 221 ℃ 기준선, 231 ℃ 숫자 겹침.
- 12~14·16번: 축·범례·그래프 안 라벨 잘림, 본문과 겹침. 특히 가로 막대의 왼쪽 범주명과 오른쪽 숫자.
- 17·18·20번: 큰 숫자와 판정 문구가 한 메시지로 보이는지.

검사 보고는 check_results.json에 남겼다. 화면 이미지만 검수했으며 완성 슬라이드를 PowerPoint에서 확인했다고 주장하지 않는다. 기존 단계 8 build.js·deck.json·PPTX·demo_checklist.md와 승인 자료는 변경하지 않았다.

## 커밋 단위 제안

커밋과 push는 실행하지 않았다. 이후 승인된 경우의 경계만 제안한다.

1. `presentation v2 sources`: build_v2.js, deck_v2.json, make_charts.py, prepare_assets.py, check_v2.py, README.md.
2. `presentation v2 evidence`: assets/, asset_sources.json, numeric_manifest.json, chart_hashes.json.
3. `presentation v2 public build`: 공개 PPTX, layout_manifest.json, check_results.json. Claude PDF 검수 후 별도 기록을 더한다.

개인 표지 JSON·제출용 PPTX·node_modules는 위 단위에 포함하지 않는다. 현재 media/stills/light/는 작업 시작 전부터 있던 미추적 자료이며 이 작업에서 덮어쓰지 않았다.
