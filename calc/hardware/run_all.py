"""Python 3.12, no CAD runtime. All dimensions from spec; inputs audited in JSON."""
from pathlib import Path
import importlib.util
import json, math
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('stacker',ROOT/'cad/stacker/spec_stacker.py'); G=importlib.util.module_from_spec(s); s.loader.exec_module(G)
H=json.loads((HERE/'hw_params.json').read_text()); SIM=G.SIM
h=lambda k:H[k]['value']
def save(name,results,checks,limitations):
    payload=dict(model=name,inputs=dict(hardware=H,dimensions=G.VALUES,parts=G.PART_SOURCES,materials=SIM['materials'],reflow=SIM['reflow'],geometry=SIM['geometry']),results=results,
                 verdict=dict(original_KPI={'force_max_N':G.LIMITS['force'],'head_max_C':G.LIMITS['head_temp'],'footprint_max_mm':G.LIMITS['footprint'],'note':'400 C는 헤드 KPI; 리플로우 척 목표는 별도'},design_checks=checks,status='PASS' if all(checks.values()) else 'FAIL/REVIEW'),limitations=limitations)
    (HERE/(name+'.json')).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    print(f"{name:22} {payload['verdict']['status']:12} "+' | '.join(f'{k}={v}' for k,v in checks.items()))
    return payload

def reflow():
    r=G.REFLOW; w,d,t=[r[k]*1e-3 for k in ('w','d','t')]
    C=w*d*t*h('al_rho')*h('al_cp')+(r['heater_w']*1e-3)**2*r['heater_t']*1e-3*h('aln_rho')*h('aln_cp')
    A=w*d+2*(w+d)*t; amb=h('ambient'); peak=SIM['reflow']['peak_temp']['value']
    def loss(T,forced=False):
        # Stefan-Boltzmann constant, Kelvin offset are physical/unit constants.
        return (h('h_forced') if forced else h('h_natural'))*A*(T-amb)+h('emissivity')*5.670374419e-8*A*((T+273.15)**4-(amb+273.15)**4)+h('calsil_k')*w*d/(r['ins_t']*1e-3)*(T-amb)
    ramps=[dict(ramp_K_s=x,required_W=C*x+loss(peak),feasible=C*x+loss(peak)<=h('heater_power')) for x in SIM['reflow']['ramp_up']['range']+[SIM['reflow']['ramp_up']['value']]]
    def cool(forced,dt):
        T=peak; elapsed=0
        while T>h('cool_to') and elapsed<h('max_cool_time'):
            T-=loss(T,forced)*dt/C; elapsed+=dt
        return elapsed
    natural=cool(False,h('dt')); forced=cool(True,h('dt')); fine=cool(True,h('dt')/2)
    # Program peak plateau plus shoulder at TL+5 C ensures nominal TAL including ramps.
    ramp=SIM['reflow']['ramp_up']['value']; down=SIM['reflow']['ramp_down']['value']; tl=h('liquidus')
    near=SIM['reflow']['time_near_peak']['value']; tal=SIM['reflow']['time_above_liquidus']['value']
    shoulder=tal-near-(peak-tl)/ramp-(peak-tl)/down
    heat_time=(peak-amb)/ramp+SIM['reflow']['soak_time']['value']+max(0,shoulder)
    simultaneous=h('head_power')+h('heater_power')+h('aux_48'); sequenced=h('heater_power')+h('aux_48')
    return save('reflow_heater',dict(thermal_capacity_J_K=C,peak_C=peak,hold_W=loss(peak),ramps=ramps,heater_W=h('heater_power'),heater_ohm=h('voltage_48')**2/h('heater_power'),heater_A=h('heater_power')/h('voltage_48'),
      natural_cool_to_100_s=natural,forced_cool_to_100_s=forced,cooling_dt_half_difference_s=abs(fine-forced),natural_initial_cool_K_s=loss(peak)/C,forced_initial_cool_K_s=loss(peak,True)/C,
      forced_control_cool_W=C*down,peak_hold_s=near,shoulder_hold_s=shoulder,TAL_s=tal,heat_time_s=heat_time,Biot_upper=h('h_forced')*t/h('al_k'),power_48_simultaneous_W=simultaneous,power_48_sequenced_W=sequenced,power_24_W=h('aux_24'),
      power_action='동시 정격 620 W: 600 W 초과. 리플로우 시 헤드 출력 금지 시퀀스 필요; 동시 사용 시 48 V 750 W 이상 전원 변경안(정격 검토 필요).'),
      dict(default_2K_s=next(x['feasible'] for x in ramps if x['ramp_K_s']==ramp),all_1_to_3K_s=all(x['feasible'] for x in ramps),peak_hold=loss(peak)<h('heater_power'),power48_simultaneous=simultaneous<=h('power_48'),power48_sequenced=sequenced<=h('power_48'),power24=h('aux_24')<=h('power_24'),profile_heat_time=heat_time<=SIM['reflow']['total_time_25_to_peak_max']['value'],natural_cooling_tracks_4K_s=loss(peak)/C>=down),
      ['Al plate + heater only; fixture/payload heat capacity and bolt thermal bridges omitted.','4 K/s 냉각은 자연냉각 불가: 제트 유량 피드백/스로틀 필요. 강제 h=400도 실측 전 추정.','집중정수는 면내 온도 균일성, 실제 프로파일 제어와 재료 인증을 검증하지 않음.'])

def mold():
    m=G.MOLD; p=h('mold_pressure'); selected=m['bore']; area=math.pi*selected**2/4
    rows=[dict(d_mm=d,p40_MPa=h('force')/(math.pi*d*d/4),p50_MPa=G.LIMITS['force']/(math.pi*d*d/4),required_N=p*math.pi*d*d/4) for d in h('diameters')]
    need=p*area; force=need+h('friction_reserve'); cavity=m['cavity_w']**2*m['cavity_d']; stack=G.STACK['die']**2*G.STACK['layers']*G.STACK['thickness']
    gate=m['gate_l']*m['gate_w']*m['gate_d']; resin=(cavity-stack+gate)*h('resin_overfill'); shot=area*m['stroke']; clamp=p*m['cavity_w']**2
    f=G.FIT; cold=[f['hole_min']-f['shaft_max'],f['hole_max']-f['shaft_min']]; hot=[c*(1+h('steel_cte')*1e-6*(SIM['reflow']['peak_temp']['value']-h('ambient'))) for c in cold]
    return save('mold_jig',dict(diameter_sweep=rows,selected_d_mm=selected,force_ideal_N=need,force_with_friction_N=force,margin_KPI_N=G.LIMITS['force']-force,margin_warning52_N=G.LIMITS['warn_force']-force,max_d_50N_mm=math.sqrt(4*G.LIMITS['force']/(math.pi*p)),cavity_mm3=cavity,solid_die_mm3=stack,resin_with_overfill_mm3=resin,shot_mm3=shot,required_stroke_mm=resin/area,fit='Ø4 H7/g6, bore 4.000..4.012, shaft 3.988..3.996 mm',cold_clearance_mm=cold,hot_isothermal_clearance_mm=hot,closure_force_N=clamp,clamp_preload_design_N=clamp*h('clamp_safety'),
       action='3 MPa×6×6 mm 캐비티 개방력 108 N: Z축 50 N만으로 금형 체결 불가. M3 나사 4개 독립 체결, 합계 예압 216 N 이상 설계 제안. 유리/나사 내압은 실증 대기.'),
       dict(pressure_under50=force<=G.LIMITS['force'],warning_margin=force<G.LIMITS['warn_force'],shot_volume=shot>=resin,closure_by_Z_alone=clamp<=G.LIMITS['force']),
       ['p=F/A is ideal static pressure, not gap inlet pressure; leakage, viscosity and friction unvalidated.','H7/g6 clearance is not a resin seal. 3 MPa leak test / replaceable sealed sleeve required.','금형은 조립 설명용 대기 위치에 배치한다. Z축 아래에서 교환 장착하고 독립 클램프로 체결한다. 유리 내압/벤트 수지 포집기는 별도 검증한다.'])

def load_path():
    F=h('force'); c=G.CHUCK; E=h('al_E')*1e3; span=h('support_span'); I=c['d']*c['t']**3/12
    delta=F*span**3/(48*E*I); sigma=(F*span/4)*(c['t']/2)/I
    parts={p[1]:p for p in G.P}; rows=[]
    for n in ('Collet_Tool','AlN_Heater','MACOR_Insulator','Z_Carriage','Bridge_Beam','Bridge_Column_L'):
        q=parts[n]; a,b,L=q[4][3:]; em=E if q[3]=='al' else (h('steel_E')*1e3 if q[3]=='steel' else SIM['materials']['si_E']['value']*1e3)
        rows.append(dict(part=n,stress_MPa=F/(a*b),axial_shortening_um=F*L/(a*b*em)*1000,model='전체 40 N이 통과하는 축 압축 상한; AlN/MACOR 탄성계수는 Si 대용 가정'))
    die_pressure=F/G.STACK['die']**2; local=die_pressure/h('bump_contact_fraction'); quartz=F*c['window']**3/(48*h('quartz_E')*1e3*(c['window']*c['t']**3/12))*1000
    # Die spanning unsupported window: strip upper-bound using bare 50um die, not quartz-backed operating configuration.
    thin=h('die_thin'); unsupported_sigma=3*F/(2*thin**2); beam=parts['Bridge_Beam'][4]; beam_delta=F*510**3/(48*E*(beam[4]*beam[5]**3/12))*1000
    return save('load_path',dict(load_path='head → die stack → full-depth quartz insert → chuck → MACOR supports → XY stages → granite → columns/beam',force_N=F,die_average_pressure_MPa=die_pressure,local_contact_pressure_MPa=local,chuck_bending_um=delta*1000,chuck_bending_stress_MPa=sigma,quartz_window_bending_um=quartz,frame_beam_deflection_um=beam_delta,axial_members=rows,unsupported_50um_die_stress_MPa=unsupported_sigma,margin_warning52_N=G.LIMITS['warn_force']-F),
       dict(chuck_flatness=delta<=c['flat'],chuck_stress=sigma<h('al_yield'),average_die_stress=local<h('die_strength'),die_fracture_proven=False),
       ['Fracture not certified by average compression: edge flaws, bumps, bending and point loads require coupon test/FEA.','50 um die must never bridge Ø15 opening without full quartz backing; interface bonding/contact stiffness unresolved.','Beam supports simple, omitted joint/stage compliance. Flatness is manufactured geometry; load bending is separate.'])

def expansion():
    dt=SIM['reflow']['peak_temp']['value']-h('ambient'); r=G.REFLOW
    al=h('al_cte')*1e-6; steel=h('steel_cte')*1e-6; si=SIM['materials']['si_cte']['value']*1e-6
    shift=al*h('datum_offset')*dt*1000; mismatch=abs(al-si)*h('datum_offset')*dt*1000
    baseline=json.loads((ROOT/'calc/midterm/error_budget.json').read_text())['rss_3s']
    # Systematic thermal offsets are not random RSS terms. Budget consumes bounded drift.
    max_dt=h('drift_budget')/(al*h('datum_offset')*1000)
    return save('thermal_expansion',dict(delta_T_K=dt,reflow_width_growth_um=al*r['w']*dt*1000,reflow_z_growth_um=al*r['t']*dt*1000,stack_chuck_width_growth_um=al*G.CHUCK['w']*dt*1000,mount_growth_um=steel*h('mount_length')*dt*1000,datum_shift_um=shift,relative_Si_datum_shift_um=mismatch,stack_Si_growth_um=si*G.STACK['layers']*G.STACK['thickness']*dt*1000,baseline_RSS3sigma_um=baseline,baseline_remaining_linear_margin_um=h('alignment_limit')-baseline,thermal_drift_budget_um=h('drift_budget'),max_temperature_change_after_alignment_K=max_dt,uncorrected_total_bound_um=baseline+mismatch,
       action='고온 현위치 비전 재정렬 + 대칭/미끄럼 장착 필요. 상온 정렬좌표를 250 C까지 그대로 적용 불가. 온도 도달 후 대기는 척 실측 안정화로 별도 결정(헤드90s 전용 규칙 재사용 불가).'),
       dict(uncompensated_alignment=mismatch<=h('drift_budget')),
       ['Uniform 20→250 C worst-case; fixed mount at same temperature is upper-bound assumption.','Systematic shift is not independent Gaussian noise: do not add to RSS in quadrature.','No claim that 2 um hot flatness is achieved; thermoelastic 3D FEA/measurement pending.'])
if __name__=='__main__':
    print('계산 | 판정 (원문 KPI와 설계 목표 분리; FAIL/REVIEW는 자동 설계 변경 없음)')
    for fn in (reflow,mold,load_path,expansion): fn()
