"""Final concept wiring; exact implemented HAL pin and explicit proposed pin mapping."""
from pathlib import Path
import csv, importlib.util, re, json
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
s=importlib.util.spec_from_file_location('stacker',ROOT/'cad/stacker/spec_stacker.py'); G=importlib.util.module_from_spec(s); s.loader.exec_module(G)
from matplotlib import font_manager as fm
font='Noto Sans CJK JP' if any(f.name=='Noto Sans CJK JP' for f in fm.fontManager.ttflist) else 'Apple SD Gothic Neo'
plt.rcParams.update({'font.family':font,'pdf.fonttype':42,'svg.fonttype':'none'})
# Proposal pins do not assert alternate-function compatibility or board connectivity.
PROPOSAL='배선 설계값 (HAL 미구현)'
ROWS=[('hal_hw_fault','PG0','입력 active-high pull-down','외부 고장 래치','HAL 구현 (임시 보드 핀)', 'firmware/hal/hal_stm32h7.c GPIOG_IDR bit0'),
('ADS1256_SCK','PA5','SPI1 SCK','로드셀 ADS1256',PROPOSAL,'보드 AF/전압 확인 필요'),('ADS1256_MISO','PA6','SPI1 MISO','로드셀 ADS1256',PROPOSAL,'보드 AF 확인 필요'),('ADS1256_MOSI','PA7','SPI1 MOSI','로드셀 ADS1256',PROPOSAL,'보드 AF 확인 필요'),('ADS1256_CS','PB0','출력 CS','로드셀 ADS1256',PROPOSAL,'독립 GPIO'),('ADS1256_DRDY','PB1','입력 DRDY','로드셀 ADS1256',PROPOSAL,'독립 GPIO'),
('hal_read_temp_C','PA0','ADC 입력','헤드 AD8495',PROPOSAL,'3.3 V ADC 범위 검토'),('reflow_temp','PA1','ADC 입력','리플로우 AD8495',PROPOSAL,'별도 온도 PI/HAL 필요'),('jig_pressure','PA2','ADC 입력','지그 압력 센서',PROPOSAL,'선택 입력; 0-3.3 V 조정'),('jig_position','PG1','입력','플런저 원점 스위치',PROPOSAL,'24 V 절연 입력'),
('hal_write_heater_W','PE9','TIM1 CH1 PWM','헤드 게이트 드라이버',PROPOSAL,'20 kHz 설계값; PE9/PE11 두 히터 동시 통전 금지(SW 인터락), 펌웨어 구현 PR #30'),('reflow_heater_pwm','PE11','TIM1 CH2 PWM','리플로우 게이트 드라이버',PROPOSAL,'150 W 설계값; PE9/PE11 두 히터 동시 통전 금지(SW 인터락), 펌웨어 PR #30·HMI 표시 W5'),('hal_write_z_velocity_mm_s','PD8/PD9','USART3 TX/RX','서보 속도 명령',PROPOSAL,'드라이버 프로토콜 미확정'),('hal_write_safety.brake','PG2','출력','브레이크 상태 요청',PROPOSAL,'독립 HW 차단과 별개'),('hal_write_safety.sto','PG3','출력','STO 상태 요청',PROPOSAL,'독립 HW 차단과 별개'),('fw_reset_latch','PC13','입력','수동 SW 리셋 요청',PROPOSAL,'HW 래치 수동 리셋 별도')]
def validate():
    hal=(ROOT/'firmware/hal/hal_stm32h7.c').read_text()
    assert re.search(r'int hal_hw_fault\(void\).*GPIOG_IDR & 1u',hal)
    assert 'GPIOG_MODER &= ~3u' in hal
    pins=[pin for row in ROWS for pin in row[1].split('/')]; assert len(pins)==len(set(pins))
    for row in ROWS:
        if row[4].startswith('HAL 구현'): assert row[0]=='hal_hw_fault' and row[1]=='PG0'
    print('PASS: HAL hal_hw_fault=PG0; 15 proposed mappings labeled HAL 미구현; no duplicate pins')
def generate():
    validate()
    H=json.loads((ROOT/'calc/hardware/hw_params.json').read_text())
    R=json.loads((ROOT/'calc/hardware/reflow_heater.json').read_text())['results']
    with (HERE/'pinmap.csv').open('w') as f:
        w=csv.writer(f,lineterminator='\n'); w.writerow(['signal','pin','direction_interface','destination','status','source_note']); w.writerows(ROWS)
    fig,ax=plt.subplots(figsize=(16.54,11.69)); ax.set(xlim=(0,420),ylim=(0,297),aspect='equal'); ax.axis('off')
    ax.add_patch(Rectangle((7,7),406,283,fill=False,lw=1.3))
    ax.text(13,281,'HBM 적층 본더 - 전원·제어 배선 / STM32H743 핀 배정',fontsize=14,weight='bold')
    ax.text(13,274,f'설계 검토용 | {font} | HW 차단=굵은 적색, SW 래치=굵은 자색 | A3 / W4-WR-001',fontsize=8)
    def block(x,y,w,h,text,color='#eff3f5'):
        ax.add_patch(Rectangle((x,y),w,h,fc=color,ec='#34495e',lw=.8)); ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=8)
    def link(a,b,label='',safety=False,soft=False,label_at=None):
        col='#b32624' if safety else '#773399' if soft else '#36536b'
        ax.add_patch(FancyArrowPatch(a,b,arrowstyle='->',mutation_scale=10,lw=2.5 if safety or soft else .8,color=col))
        if label:
            lx,ly=label_at or ((a[0]+b[0])/2,(a[1]+b[1])/2+2)
            ax.text(lx,ly,label,fontsize=7,ha='center',color=col,bbox=dict(facecolor='white',edgecolor='none',pad=.4))
    block(13,238,62,27,'① AC 220 V → 퓨즈/PE\n48 V 600 W / 24 V 150 W')
    block(92,238,89,27,'비상정지 + 도어 + 냉각 유량\n이중 채널 안전 릴레이 → K1', '#fdecec')
    link((75,252),(92,252),safety=True)
    block(199,238,94,27,'독립 HW 고장 래치 / 수동 복귀\n55 N 비교기 OR 420 ℃ 중복TC\n안전 체인 개방 OR 전력단 고장','#fdecec')
    link((181,251),(199,251),safety=True)
    block(312,238,91,27,'K1 OFF / 두 게이트 EN OFF\n서보 STO / Z 무여자 브레이크\n24 V 기록 전원 유지','#fdecec'); link((293,251),(312,251),safety=True)
    block(13,191,85,30,'② 헤드 히터 48 V / 400 W\n15 A 퓨즈 → 히터 → 100 V MOSFET\n게이트 드라이버 + 션트 감시')
    block(112,191,85,30,f"⑤ 리플로우 48 V / {G.REFLOW['power_W']} W\n분기 퓨즈(선정대기) → 히터 → MOSFET\n독립 게이트 EN / 중복 과온 감시")
    link((43,238),(43,221),safety=True); ax.text(49,228,'K1 후 48 V',fontsize=7,color='#b32624')
    link((155,238),(155,221),safety=True)
    block(211,191,94,30,'③ 로드셀 INA826 → ADS1256\n헤드TC / 척TC → AD8495\nPT100/MAX31865·엔코더 별도설계')
    block(320,191,83,30,'⑥ 지그 입력\n압력 센서 → 절연/ADC\n플런저 원점 → 절연 GPIO')
    block(91,137,147,36,'④ STM32H743 / 3.3 V 로직\n하중 PI 1 ms · 온도 PI 10 ms (설계 목표)\nSW 경고52 N/410 ℃ → 래치55 N/420 ℃\n두 히터 동시 통전 금지(SW 인터락)','#f1e9f8')
    link((253,191),(227,173),'SPI / ADC'); link((349,191),(238,169),'ADC / GPIO',label_at=(291,185))
    link((105,173),(55,191),'인터락 → PWM PE9',soft=True,label_at=(71,180))
    link((156,173),(156,191),'PWM PE11',soft=True,label_at=(176,180))
    block(266,141,137,32,'서보 드라이버 / Z축 브레이크\nSW 상태요청 PG2/PG3는 HAL 미구현\n독립 HW 차단은 MCU 출력과 무관')
    link((238,156),(266,156),'PD8/9 설계값')
    # Dedicated left SW corridor and narrow PG0 corridor keep lines outside boxes.
    link((246,238),(246,229),safety=True)
    link((246,229),(204,229),safety=True)
    link((204,229),(204,178),safety=True)
    link((204,178),(218,173),safety=True)
    ax.text(207,219,'PG0 HW fault',fontsize=7,color='#b32624',rotation=90,va='top')
    link((91,148),(9,148),soft=True)
    link((9,148),(9,232),soft=True)
    link((9,232),(220,232),soft=True)
    link((220,232),(220,238),soft=True)
    ax.text(16,166,'SW 래치 → 차단 요청\n(출력 미구현)',fontsize=7,color='#773399',ha='left',va='center')
    link((403,251),(409,251),safety=True)
    link((409,251),(409,157),safety=True)
    link((409,157),(403,157),safety=True)
    ax.text(407,221,'HW STO / BRAKE',fontsize=7,color='#b32624',rotation=90,ha='right',va='top')
    ax.text(13,132,f"순차 전력: 척{R['power_48_sequenced_W']} W / 헤드{R['power_48_head_phase_W']} W ≤{H['power_48']['value']} W. 24 V측{R['power_24_W']}≤{H['power_24']['value']} W (보조는 가정값).",fontsize=8,color='#a22')
    ax.text(13,126,'두 히터 동시 통전 금지(SW 인터락): 펌웨어 PR #30에서 구현·시험, HMI 표시는 W5. 동시650 W 금지. 지그 기밀·내압: 제작 후 시험.',fontsize=8)
    # Tabulated mapping on the same sheet; exact implemented pin separated by status.
    columns=['신호명 (함수명은 HAL 그대로)','핀','인터페이스','연결 / 구현 상태']
    cells=[[r[0],r[1],r[2],r[3]+(' · 두 히터 동시 통전 금지(SW 인터락)' if r[1] in ('PE9','PE11') else '')+' / '+('HAL 구현' if r[4].startswith('HAL 구현') else '배선 설계값 · HAL 미구현')] for r in ROWS]
    table=ax.table(cellText=cells,colLabels=columns,cellLoc='left',colLoc='left',bbox=[.03,.065,.94,.34],colWidths=[.30,.10,.18,.42]); table.auto_set_font_size(False); table.set_fontsize(6.7)
    for (r,c),cell in table.get_celld().items():
        cell.set_linewidth(.35)
        if r==0: cell.set_facecolor('#dde5ec'); cell.set_text_props(weight='bold')
        elif r==1: cell.set_facecolor('#fce7e6')
    ax.text(13,14,'출처: 중간 10.4절 · firmware/hal/hal_stm32h7.c · calc/hardware/reflow_heater.json. 핀 AF/회로 BOM/절연·배선 굵기 상세 검증 대기.',fontsize=7)
    fig.savefig(HERE/'hbm_wiring.svg');
    svg=HERE/'hbm_wiring.svg'; svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    fig.savefig(HERE/'hbm_wiring.pdf'); fig.savefig(HERE/'hbm_wiring.png',dpi=150); plt.close(fig)
    print('PASS: SVG + PDF + PNG, pinmap.csv')
if __name__=='__main__': generate()
