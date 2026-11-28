# HBM 적층 본더 CAD (Fusion 실행 전)

치수 단일 원본은 `spec_stacker.py`다. 중간 `cad/midterm/spec.py`를 읽어 43개 부품을 재사용하고 신규 8개를 추가한다. 신규 값은 설계값이며 출처는 `VALUES`, `PART_SOURCES`에 기록한다. 계산·도면·배선도도 같은 원본을 읽는다. 금형/리플로우 척은 교환 장착 설명용 대기 위치이며, 현재 모델은 제작 승인본이 아니다.

## 실행 방법

저장소 루트에서 Python 3.12로 사전 확인한다.

```sh
export PATH=/opt/homebrew/bin:$PATH
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 calc/hardware/run_all.py
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 cad/stacker/check_spec.py
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 cad/tools/test_to_glb.py
MPLCONFIGDIR=/tmp/w4-matplotlib /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 docs/drawings/generate.py
MPLCONFIGDIR=/tmp/w4-matplotlib /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 wiring/generate.py
```

`check_spec.py`는 `-I`도 지원한다. 51개 부품, 10개 그룹, 풋프린트 추정 590×480 mm를 확인한다. 높이 630 mm와 질량은 참고값이다. 사전검사는 간섭 검증을 대신하지 않는다.

Fusion은 사용자가 실행한다. 뷰 → 텍스트 명령 표시 → **Py**에 아래 한 줄을 입력한다 (CLAUDE.md 9절 형식).

```python
g={'__file__':__import__('os').path.expanduser('~/Desktop/MSE489/기말보고서/wt-hw/cad/stacker/HBMStackerModel.py')};exec(open(g['__file__'],encoding='utf-8').read(),g);g['run'](None)
```

스크립트는 `__file__` 기준으로 원본을 읽고 새 Fusion 문서를 만든다. 재실행 시 `out/mesh/*.stl`은 재생성한다.

## 이름 규칙

STL은 그룹별 통합 메시이며 파일명 = 컴포넌트 그룹명 = GLB 노드명이다. 개별 부품명은 Fusion 하위 컴포넌트와 summary의 parts에 유지한다.

| 그룹 / STL 이름 | 포함 부품 |
|---|---|
| `frame` | 중간 프레임·스테이지·기타 광학/전장 부품, 신규 받침대 |
| `head` | 중간 Head 그룹 중 Z_Carriage를 제외한 히터·콜릿 등 |
| `z_carriage` | Z_Carriage |
| `stack_chuck` | Vacuum_Chuck_200C, Quartz_Window |
| `reflow_chuck` | Reflow_Plate, Reflow_Heater, Reflow_Insulator |
| `mold_jig` | Mold_Block, Mold_Glass_Substrate |
| `plunger` | Plunger |
| `dispenser` | Dispenser_* (기존 위치에서 이동) |
| `ncf_tray` | GelPak_Tray |
| `camera_bottom` | Bottom_Camera |

## 산출물과 확인 항목

| 산출물 | 확인 |
|---|---|
| `out/HBMStacker.step` | 전체 형상, 천공·홈·캐비티·벤트, 단위 mm; 향후 Git LFS 대상 |
| `out/mesh/<위 10개 이름>.stl` | 10개 전부 존재, 기본 mm 기준 베이스 폭 590 mm 확인 |
| `out/summary.json` | bbox x/y ≤600 mm, footprint_KPI_pass=true, interference_count=0, interference_pass=true, 간섭 목록, 51개 부품·10개 그룹 |
| `out/view_iso.png`, `view_front.png`, `view_side.png`, `view_top.png` | 광로, 척 교환 위치, 지그·플런저, 조립 배치 시각 확인 |
| `../../docs/drawings/` | 적층 척·리플로우 척·지그 각 PNG/PDF, dimensions.json |
| `../../wiring/` | hbm_wiring.svg/pdf/png, pinmap.csv |
| `../../calc/hardware/` | 4개 계산 JSON 및 README의 판정·제작 후 시험 |

Fusion 실행 전에는 STEP/STL/summary/뷰와 실제 장비 GLB가 없다. 간섭 검사 실패 시 count=-1이므로 통과로 읽지 않는다. 도면은 A3·3각법·ISO 2768-mK이며 재질·열처리·조도·기하공차·끼워맞춤을 표시한다. Noto Sans CJK JP 미설치 환경에서는 Apple SD Gothic Neo로 대체한다.

Fusion 결과를 검토한 뒤 별도 지시에 따라 아래 변환을 수행한다. STL 입력 mm, GLB 출력 m, Z-up→Y-up 회전이며 extras에 단위를 기록한다. 일반 커밋 대상 GLB는 20 MiB 이하이고, 20 MB 이하 기준에도 실제 바이트 수를 확인한다. 합성 테스트는 임시 폴더만 사용한다.

```sh
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 cad/tools/to_glb.py
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 cad/tools/check_glb.py cad/web/hbm_stacker.glb
```

실제 GLB의 브라우저 표시, CAD 간섭 0, 고온 평면도 및 내압은 미검증이다. Fusion 실행 및 `out/` 결과 확인은 사용자 담당이며 이번 작업에서는 해당 폴더를 읽거나 쓰지 않는다.

## 사용자 확정 설계·리플로우 절차 (2026-11-28)

- 헤드400 W와 리플로우 척150 W(설계값)는 순차 사용한다. **두 히터 동시 통전 금지(SW 인터락)**를 펌웨어(PR #30, 구현·시험 완료)와 HMI에 둔다. 보조 포함 척 단계250 W, 헤드 단계500 W로48 V 600 W 이내다.
- 3 K/s 필요120.687 W 대비150 W의 여유는29.313 W(24.289%)다. 공기·N₂ 강제 냉각의 유량100 L/min·h400 W/m²K는 실측 전 가정이다. 설계 목표는 피크→180 ℃에서 기본4 K/s 이상 유지다. 현재250→180 ℃는17.072336 s, 최소3.393151 / 평균4.100200 K/s로 **FAIL/REVIEW**다. 180→100 ℃는32.764682 s, 1.689129~3.393151 K/s로 관찰 항목(판정 없음)이다. 상세 근거는 `../../calc/hardware/README.md`와 `hw_params.json`에 있다.
- Ø4 mm 플런저와 독립 M3 나사4개 합계 예압≥216 N을 채택한다. 기밀·예압·유리/나사 내압·벤트 트랩은 **제작 후 시험**이다. 나사 상세 형상은 기존 개념 CAD의4개 체결 구멍에 대응하는 조립품이며 이번에 형상을 바꾸지 않았다.
- 다이 파손은 FEA 대신 피치55 μm·지름25 μm 범프 면적 손계산을 사용한다.40/50 N에서 접촉응력9.860/12.325 MPa로 문헌 비교값261 MPa보다 낮다. 전면 석영 지지·균일 범프 하중 조건부 PASS이며, 문헌 두께·출처 및 모델 한계는 계산 README에 명시했다.

1. 적층 중 상온 또는 설정 정렬 온도에서 층간 정렬을 완료한다. **적층 척=리플로우 척이면 정렬 온도를 고정하고, 온도 도달 후90 s 안정화 대기(중간 보고서7장)**한 뒤 정렬한다.
2. 헤드 히터 출력을 OFF하고 SW 인터락으로 동시 통전이 금지된 상태에서 척 히터를 운전한다. 예열·승온·피크·TAL은 읽기 전용 `sim.reflow`를 따른다. 인터락은 펌웨어 PR #30에서 구현·시험했다 (실물 bring-up은 범위 밖).
3. 완성 스택 전체를 척과 함께 가열한다. 기준점108.56 μm(약109 μm) 이동은 층간 정합 ±1 μm KPI에 영향이 없다. 이 해석은 강체 동반 이동에 한정되며 열 휨·미끄러짐은 별도로 확인한다.
4. 척 히터를 OFF하고 공기·N₂ 강제 냉각을 수행한다. 설계 목표인 피크→180 ℃에서의 기본4 K/s 이상 유지와 문헌 프로파일 상한6 K/s를 구분한다. 현재 모델은 판정 구간 최소3.393151 K/s로 **FAIL/REVIEW**이며 실측 프로파일로 확인한다. 180 ℃ 아래 속도·시간은 관찰 항목(판정 없음)이다.

현재 모델은 적층/리플로우 척을 교환 장착 설명용 대기 위치에 둔다. 동일 척 구성의 위 절차는 사용자 확정 운영 조건이며 새로운 동일 척 형상을 만들지는 않았다. 원문 KPI·설계값·문헌값·가정값·제작 후 시험을 구분한다.
