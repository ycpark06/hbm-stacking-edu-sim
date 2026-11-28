"""Python 3.12, no CAD runtime. All dimensions from spec; inputs audited in JSON."""
from pathlib import Path
import importlib.util
import json, math
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('stacker',ROOT/'cad/stacker/spec_stacker.py'); G=importlib.util.module_from_spec(s); s.loader.exec_module(G)
H=json.loads((HERE/'hw_params.json').read_text()); SIM=G.SIM
h=lambda k:H[k]['value']
def save(name,results,checks,limitations,post_tests=None,reviews=None):
    post_tests=post_tests or []; reviews=reviews or []
    remaining=[k for k,v in checks.items() if not v]
    payload=dict(model=name,inputs=dict(hardware=H,dimensions=G.VALUES,parts=G.PART_SOURCES,materials=SIM['materials'],reflow=SIM['reflow'],geometry=SIM['geometry']),results=results,
                 verdict=dict(original_KPI={'force_max_N':G.LIMITS['force'],'head_max_C':G.LIMITS['head_temp'],'footprint_max_mm':G.LIMITS['footprint'],'note':'400 C는 헤드 KPI; 리플로우 척 목표는 별도'},design_checks=checks,status='FAIL/REVIEW' if remaining or reviews else 'PASS',remaining_FAIL_REVIEW=remaining+reviews,post_fabrication_tests=post_tests),limitations=limitations)
    (HERE/(name+'.json')).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    print(f"{name:22} {payload['verdict']['status']:12} "+' | '.join(f'{k}={v}' for k,v in checks.items()))
    print("  FAIL/REVIEW: "+("; ".join(remaining+reviews) or "없음")+" | 제작 후 시험: "+("; ".join(post_tests) or "없음"))
    return payload

def reflow():
    r=G.REFLOW; w,d,t=[r[k]*1e-3 for k in ('w','d','t')]
    C=w*d*t*h('al_rho')*h('al_cp')+(r['heater_w']*1e-3)**2*r['heater_t']*1e-3*h('aln_rho')*h('aln_cp')
    A=w*d+2*(w+d)*t; amb=h('ambient'); peak=SIM['reflow']['peak_temp']['value']
    assert h('heater_power')==r['power_W']
    flow_capacity=h('coolant_flow')*1e-3/60*h('coolant_rho')*h('coolant_cp')
    # hA in series with finite coolant heat capacity: well-mixed gas control-volume assumption.
    forced_G=1/(1/(h('h_forced')*A)+1/flow_capacity)
    def loss(T,forced=False):
        # Stefan-Boltzmann constant, Kelvin offset are physical/unit constants.
        return (forced_G if forced else h('h_natural')*A)*(T-amb)+h('emissivity')*5.670374419e-8*A*((T+273.15)**4-(amb+273.15)**4)+h('calsil_k')*w*d/(r['ins_t']*1e-3)*(T-amb)
    ramps=[dict(ramp_K_s=x,required_W=C*x+loss(peak),feasible=C*x+loss(peak)<=h('heater_power')) for x in SIM['reflow']['ramp_up']['range']+[SIM['reflow']['ramp_up']['value']]]
    def cool(forced,dt,target=None,controlled=False):
        target=h('cool_to') if target is None else target
        T=peak; elapsed=0
        while T>target and elapsed<h('max_cool_time'):
            rate=loss(T,forced)/C
            if controlled: rate=min(rate,SIM['reflow']['ramp_down']['value'])
            step=min(dt,(T-target)/rate)
            T-=rate*step; elapsed+=step
        return elapsed
    natural=cool(False,h('dt')); forced=cool(True,h('dt')); fine=cool(True,h('dt')/2)
    controlled=cool(True,h('dt'),controlled=True)
    controlled_tl=cool(True,h('dt'),h('liquidus'),True)
    end_rate=loss(h('cool_to'),True)/C
    # Program peak plateau plus shoulder at TL+5 C ensures nominal TAL including ramps.
    ramp=SIM['reflow']['ramp_up']['value']; down=SIM['reflow']['ramp_down']['value']; tl=h('liquidus')
    near=SIM['reflow']['time_near_peak']['value']; tal=SIM['reflow']['time_above_liquidus']['value']
    shoulder=tal-near-(peak-tl)/ramp-(peak-tl)/down
    heat_time=(peak-amb)/ramp+SIM['reflow']['soak_time']['value']+max(0,shoulder)
    simultaneous=h('head_power')+h('heater_power')+h('aux_48'); sequenced=h('heater_power')+h('aux_48')
    return save('reflow_heater',dict(thermal_capacity_J_K=C,peak_C=peak,hold_W=loss(peak),ramps=ramps,heater_W=h('heater_power'),heater_ohm=h('voltage_48')**2/h('heater_power'),heater_A=h('heater_power')/h('voltage_48'),
      natural_cool_to_100_s=natural,forced_cool_to_100_s=forced,cooling_dt_half_difference_s=abs(fine-forced),natural_initial_cool_K_s=loss(peak)/C,forced_initial_cool_K_s=loss(peak,True)/C,
      forced_control_cool_W=C*down,forced_end_cool_K_s=end_rate,forced_cool_to_liquidus_s=cool(True,h('dt'),tl),controlled_cool_to_100_s=controlled,ideal_4K_s_cool_to_100_s=(peak-h('cool_to'))/down,coolant_flow_L_min=h('coolant_flow'),coolant_capacity_W_K=flow_capacity,forced_effective_conductance_W_K=forced_G,heater_margin_3K_s_W=h('heater_power')-max(x['required_W'] for x in ramps),heater_margin_3K_s_percent=(h('heater_power')/max(x['required_W'] for x in ramps)-1)*100,peak_hold_s=near,shoulder_hold_s=shoulder,TAL_target_s=tal,TAL_estimated_controlled_s=near+max(0,shoulder)+(peak-tl)/ramp+controlled_tl,heat_time_s=heat_time,Biot_upper=h('h_forced')*t/h('al_k'),power_48_simultaneous_W=simultaneous,power_48_sequenced_W=sequenced,power_48_head_phase_W=h('head_power')+h('aux_48'),power_48_max_sequenced_W=max(sequenced,h('head_power')+h('aux_48')),power_24_W=h('aux_24'),
      power_action='순차 운전 채택: 헤드400 W와 척150 W 두 히터 동시 통전 금지(SW 인터락, 펌웨어 PR #30에서 구현·시험). 동시650 W는 금지 상태 참고값.'),
      dict(default_2K_s=next(x['feasible'] for x in ramps if x['ramp_K_s']==ramp),all_1_to_3K_s=all(x['feasible'] for x in ramps),peak_hold=loss(peak)<h('heater_power'),power48_head_phase=h('head_power')+h('aux_48')<=h('power_48'),power48_sequenced=sequenced<=h('power_48'),power24=h('aux_24')<=h('power_24'),profile_heat_time=heat_time<=SIM['reflow']['total_time_25_to_peak_max']['value'],forced_cooling_tracks_default_4K_s=end_rate>=down,controlled_cooling_under_profile_max=min(loss(peak,True)/C,down)<=max(SIM['reflow']['ramp_down']['range'])),
      ['Al plate + heater only; fixture/payload heat capacity and bolt thermal bridges omitted.','공기/N₂ 유량100 L/min 및 h=400은 독립 가정. 유한 유량 열저항 포함; 기본4 K/s는 전 구간 추종 불가, 최대6 K/s와 기본4 K/s를 구분.','집중정수는 면내 온도 균일성, 실제 프로파일 제어와 재료 인증을 검증하지 않음.'],post_tests=['노즐 유량/h 및 탑재 상태 열프로파일 실측'],reviews=[])

def mold():
    m=G.MOLD; p=h('mold_pressure'); selected=m['bore']; area=math.pi*selected**2/4
    rows=[dict(d_mm=d,p40_MPa=h('force')/(math.pi*d*d/4),p50_MPa=G.LIMITS['force']/(math.pi*d*d/4),required_N=p*math.pi*d*d/4) for d in h('diameters')]
    need=p*area; force=need+h('friction_reserve'); cavity=m['cavity_w']**2*m['cavity_d']; stack=G.STACK['die']**2*G.STACK['layers']*G.STACK['thickness']
    gate=m['gate_l']*m['gate_w']*m['gate_d']; resin=(cavity-stack+gate)*h('resin_overfill'); shot=area*m['stroke']; clamp=p*m['cavity_w']**2
    f=G.FIT; cold=[f['hole_min']-f['shaft_max'],f['hole_max']-f['shaft_min']]; hot=[c*(1+h('steel_cte')*1e-6*(SIM['reflow']['peak_temp']['value']-h('ambient'))) for c in cold]
    return save('mold_jig',dict(diameter_sweep=rows,selected_d_mm=selected,force_ideal_N=need,force_with_friction_N=force,margin_KPI_N=G.LIMITS['force']-force,margin_warning52_N=G.LIMITS['warn_force']-force,max_d_50N_mm=math.sqrt(4*G.LIMITS['force']/(math.pi*p)),cavity_mm3=cavity,solid_die_mm3=stack,resin_with_overfill_mm3=resin,shot_mm3=shot,required_stroke_mm=resin/area,fit='Ø4 H7/g6, bore 4.000..4.012, shaft 3.988..3.996 mm',cold_clearance_mm=cold,hot_isothermal_clearance_mm=hot,closure_force_N=clamp,clamp_preload_required_N=clamp*h('clamp_safety'),clamp_preload_design_N=m['clamp_preload_N'],clamp_count=m['clamp_count'],clamp_thread=m['clamp_thread'],
       action='3 MPa×6×6 mm 캐비티 개방력 108 N: Z축 50 N만으로 금형 체결 불가. M3 나사 4개 독립 체결, 합계 예압 ≥216 N 채택. 기밀 판정: 제작 후 시험.'),
       dict(pressure_under50=force<=G.LIMITS['force'],warning_margin=force<G.LIMITS['warn_force'],shot_volume=shot>=resin,independent_clamp_preload=m['clamp_preload_N']>=clamp*h('clamp_safety')),
       ['p=F/A is ideal static pressure, not gap inlet pressure; leakage, viscosity and friction unvalidated.','H7/g6 clearance is not a resin seal. 3 MPa leak test / replaceable sealed sleeve required.','금형은 조립 설명용 대기 위치에 배치한다. Z축 아래에서 교환 장착하고 독립 클램프로 체결한다. 유리 내압/벤트 수지 포집기는 제작 후 시험한다.'],post_tests=['기밀: 3 MPa 수지 누설 시험','M3 4개 합계 예압 ≥216 N 확인 및 유리/나사 내압·벤트 트랩 시험'])

def load_path():
    F=h('force'); c=G.CHUCK; E=h('al_E')*1e3; span=h('support_span'); I=c['d']*c['t']**3/12
    delta=F*span**3/(48*E*I); sigma=(F*span/4)*(c['t']/2)/I
    parts={p[1]:p for p in G.P}; rows=[]
    for n in ('Collet_Tool','AlN_Heater','MACOR_Insulator','Z_Carriage','Bridge_Beam','Bridge_Column_L'):
        q=parts[n]; a,b,L=q[4][3:]; em=E if q[3]=='al' else (h('steel_E')*1e3 if q[3]=='steel' else SIM['materials']['si_E']['value']*1e3)
        rows.append(dict(part=n,stress_MPa=F/(a*b),axial_shortening_um=F*L/(a*b*em)*1000,model='전체 40 N이 통과하는 축 압축 상한; AlN/MACOR 탄성계수는 Si 대용 가정'))
    die_area=G.STACK['die']**2
    pitch=SIM['geometry']['bump_pitch']['value']*1e-3; diameter=SIM['geometry']['bump_diameter']['value']*1e-3
    count=die_area/pitch**2; single_area=math.pi*diameter**2/4; contact_area=count*single_area
    contacts=[dict(force_N=f,die_average_pressure_MPa=f/die_area,bump_contact_stress_MPa=f/contact_area,reference_strength_ratio=h('die_strength_reference')/(f/contact_area)) for f in (F,G.LIMITS['force'])]
    die_pressure=F/die_area; local=F/contact_area; quartz=F*c['window']**3/(48*h('quartz_E')*1e3*(c['window']*c['t']**3/12))*1000
    # Die spanning unsupported window: strip upper-bound using bare 50um die, not quartz-backed operating configuration.
    thin=h('die_thin'); unsupported_sigma=3*F/(2*thin**2); beam=parts['Bridge_Beam'][4]; beam_delta=F*510**3/(48*E*(beam[4]*beam[5]**3/12))*1000
    return save('load_path',dict(load_path='head → die stack → full-depth quartz insert → chuck → MACOR supports → XY stages → granite → columns/beam',force_N=F,die_average_pressure_MPa=die_pressure,local_contact_pressure_MPa=local,bump_pitch_um=pitch*1000,bump_diameter_um=diameter*1000,bump_count_area_estimate=count,single_bump_area_mm2=single_area,total_bump_contact_area_mm2=contact_area,force_cases=contacts,Si_reference_strength_MPa=h('die_strength_reference'),comparison='문헌 굽힘 파괴강도와 접촉 압축응력 크기 비교; 균일하중·전면 석영 지지 조건부 손계산 PASS, 최소강도/수명 보증 아님',chuck_bending_um=delta*1000,chuck_bending_stress_MPa=sigma,quartz_window_bending_um=quartz,frame_beam_deflection_um=beam_delta,axial_members=rows,unsupported_50um_die_stress_MPa=unsupported_sigma,margin_warning52_N=G.LIMITS['warn_force']-F),
       dict(chuck_flatness=delta<=c['flat'],chuck_stress=sigma<h('al_yield'),bump_contact_handcalc=all(x['bump_contact_stress_MPa']<h('die_strength_reference') for x in contacts)),
       ['FEA 대신 범프 원형면적 손계산. 모든 범프가 균일 접촉하고 전면 석영 지지되는 조건. 문헌 굽힘 인장강도는 압축 접촉 허용응력과 다르며 파손확률/실물 안전 인증이 아님.','50 um die must never bridge Ø15 opening without full quartz backing; interface bonding/contact stiffness unresolved.','Beam supports simple, omitted joint/stage compliance. Flatness is manufactured geometry; load bending is separate.'],post_tests=['실제 다이 표면결함·범프 불균일 접촉 및 전면 지지 확인'])

def expansion():
    dt=SIM['reflow']['peak_temp']['value']-h('ambient'); r=G.REFLOW
    al=h('al_cte')*1e-6; steel=h('steel_cte')*1e-6; si=SIM['materials']['si_cte']['value']*1e-6
    shift=al*h('datum_offset')*dt*1000; mismatch=abs(al-si)*h('datum_offset')*dt*1000
    baseline=json.loads((ROOT/'calc/midterm/error_budget.json').read_text())['rss_3s']
    # Systematic thermal offsets are not random RSS terms. Budget consumes bounded drift.
    max_dt=h('drift_budget')/(al*h('datum_offset')*1000)
    return save('thermal_expansion',dict(delta_T_K=dt,reflow_width_growth_um=al*r['w']*dt*1000,reflow_z_growth_um=al*r['t']*dt*1000,stack_chuck_width_growth_um=al*G.CHUCK['w']*dt*1000,mount_growth_um=steel*h('mount_length')*dt*1000,datum_shift_um=shift,relative_Si_datum_shift_um=mismatch,stack_Si_growth_um=si*G.STACK['layers']*G.STACK['thickness']*dt*1000,baseline_RSS3sigma_um=baseline,baseline_remaining_linear_margin_um=h('alignment_limit')-baseline,thermal_drift_budget_um=h('drift_budget'),max_temperature_change_after_alignment_K=max_dt,uncorrected_total_bound_um=baseline+mismatch,
       action='층간 정렬은 적층 중 상온 또는 고정 정렬 온도에서 완료. 리플로우 시 스택 전체가 척과 함께 이동하므로 기준점108.56 μm 이동은 층간 정합 ±1 μm KPI에 영향 없음. 적층 척=리플로우 척 구성은 정렬 온도 고정 + 온도 도달 후90 s 안정화 대기(중간 보고서7장).',alignment_wait_s=r['alignment_wait_s'],interlayer_KPI_effect='영향 없음: 완성 스택 강체 동반 이동 해석; 열 휨/미끄러짐 별도',uncorrected_total_bound_note='기존 수치 보존용 냉간→고온 좌표 오용 상한; 층간 정합 판정에 사용하지 않음'),
       dict(interlayer_alignment_rigid_stack=True,baseline_alignment=baseline<=h('alignment_limit')),
       ['Uniform 20→250 C worst-case; fixed mount at same temperature is upper-bound assumption.','Systematic shift is not independent Gaussian noise: do not add to RSS in quadrature.','고온 평면도·층간 CTE차·열 휨·미끄러짐을 강체 이동과 구분; 본 판정은 기준점 이동의 KPI 해석에 한정.'],post_tests=['정렬 온도 고정/90 s 대기 후 실제 열안정·고온 평면도 확인'])
if __name__=='__main__':
    print('계산 | 판정 (원문 KPI와 설계 목표 분리; FAIL/REVIEW는 자동 설계 변경 없음)')
    for fn in (reflow,mold,load_path,expansion): fn()
