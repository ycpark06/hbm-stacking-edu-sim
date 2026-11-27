"""Single geometry source, mm, absolute assembly coordinates, z up.
Inherited envelope/parts: midterm chapters 3/7/11, cad/midterm/spec.py.
All additions below are 설계값; calculated adequacy: calc/hardware/*.json.
No Fusion imports; consumers load this file by absolute __file__-relative path.
"""
from pathlib import Path
import importlib.util
import json
ROOT = Path(__file__).resolve().parents[2]
def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
MID = load_module(ROOT/'cad/midterm/spec.py', 'midterm_geometry')
SIM = json.loads((ROOT/'sim/params.json').read_text())
# Metadata accompanies every new scalar; SI conversion only happens in calculations.
VALUES = {}
def v(key, value, unit='mm', source='설계값; 06 HANDOFF §3; 검산 calc/hardware/*.json'):
    VALUES[key] = dict(value=value, unit=unit, kind='설계값', source=source)
    return value
D = dict(MID.D)
NAMES = ('frame','head','z_carriage','stack_chuck','reflow_chuck','mold_jig','plunger','dispenser','ncf_tray','camera_bottom')
# Manufacturing geometry shared by drawings and actual CAD cuts.
CHUCK = dict(w=v('stack.width',100,source='중간 11장 ST-004'),d=v('stack.depth',100,source='중간 11장 ST-004'),t=v('stack.thickness',18,source='중간 11장 ST-004'),
             window=v('stack.window_d',15,source='중간 11장 ST-004; H7/g6'),pitch=v('stack.bolt_pitch',80),bolt=v('stack.bolt_d',4.5),
             pin=v('stack.dowel_d',3),pin_pitch=v('stack.dowel_pitch',60),pilot=v('stack.pilot_d',6),flat=v('stack.flatness',.002,source='중간 11장 ST-004; 설계 목표'),
             groove_w=v('stack.groove_width',1),groove_depth=v('stack.groove_depth',.5),groove_span=v('stack.groove_span',40))
REFLOW = dict(w=v('reflow.width',40),d=v('reflow.depth',40),t=v('reflow.thickness',8),pitch=v('reflow.bolt_pitch',30),bolt=v('reflow.bolt_d',4.5),
              heater_w=v('reflow.heater_width',30),heater_t=v('reflow.heater_thickness',2),ins_t=v('reflow.insulation_thickness',10,source='중간 7.5절 규산칼슘 방식'),
              tc_d=v('reflow.tc_d',1.6),tc_depth=v('reflow.tc_depth',4),flat=CHUCK['flat'])
MOLD = dict(w=v('mold.width',30),d=v('mold.depth',30),t=v('mold.thickness',10),cavity_w=v('mold.cavity_width',6),cavity_d=v('mold.cavity_depth',2),
            bore=v('mold.plunger_d',4),plunger_l=v('mold.plunger_length',20),stroke=v('mold.stroke',8),gate_w=v('mold.gate_width',1),gate_d=v('mold.gate_depth',.5),
            gate_l=v('mold.gate_length',6),vent_w=v('mold.vent_width',.5),vent_d=v('mold.vent_depth',.02),pitch=v('mold.clamp_pitch',22),bolt=v('mold.clamp_d',3.4))
# ISO 286 diameter >3..6 mm, secondary machining dimensions are also in source.
FIT = dict(hole_min=v('fit.H7_min',0),hole_max=v('fit.H7_max',.012),shaft_min=v('fit.g6_min',-.012),shaft_max=v('fit.g6_max',-.004))
STACK = dict(layers=v('stack.layers',12,'count', '설계값; requirements §3 / recipe.layers.range'),die=SIM['geometry']['die_size']['value'],
             thickness=SIM['geometry']['die_thickness']['value']/1000,gap=SIM['geometry']['interlayer_gap']['value']/1000)
POSITIONS = dict(stack=v('position.stack',[0,0,165]),reflow=v('position.reflow',[140,-100,165]),mold=v('position.mold',[-140,100,179]),
                 dispenser=v('position.dispenser',[-140,100,240]),ncf=v('position.ncf',[85,0,171]),camera=v('position.camera',[40,0,70]))
MATERIALS = dict(stack_chuck='A6061-T6', reflow_chuck='A6061-T6',mold_jig='SUS304',plunger='SUS304',window='fused silica')
# Manufacturing requirements: midterm 11.3/11.4 or explicit new design value.
TOL = dict(outline=v('tol.outline',.05),thickness=v('tol.thickness',.01),parallel=v('tol.parallel',.005),perpendicular=v('tol.perpendicular',.01),
           ra_top=v('finish.top',.4,'um'),ra_slide=v('finish.plunger',.2,'um'),ra_other=v('finish.other',1.6,'um'))
def group(n,g):
    if n=='Z_Carriage': return 'z_carriage'
    if n=='Vacuum_Chuck_200C' or n=='Quartz_Window': return 'stack_chuck'
    if n=='Bottom_Camera': return 'camera_bottom'
    if n=='GelPak_Tray': return 'ncf_tray'
    if n.startswith('Dispenser_'): return 'dispenser'
    return 'head' if g=='Head' else 'frame'
P=[]
for typ,n,g,m,p in MID.P:
    if n.startswith('Dispenser_'):
        p=tuple(a+b if i<2 else a for i,(a,b) in enumerate(zip(p,(-60,100)+(0,)*(len(p)-2))))
    P.append((typ,n,group(n,g),m,p))
CUTS=[(n,'box',p) for n,p in MID.CUTS if n!='Vacuum_Chuck_200C']
def box(n,g,m,xyz,dims): P.append(('box',n,g,m,tuple(xyz)+tuple(dims)))
def zhole(n,x,y,z,t,d): CUTS.append((n,'cyl',(x,y,z-t/2-1,z+t/2+1,d/2)))
def plate_holes(n,x,y,z,t,pitch,diam):
    for dx in (-pitch/2,pitch/2):
        for dy in (-pitch/2,pitch/2): zhole(n,x+dx,y+dy,z,t,diam)
x,y,z=POSITIONS['stack']; zhole('Vacuum_Chuck_200C',x,y,z,CHUCK['t'],CHUCK['window'])
plate_holes('Vacuum_Chuck_200C',x,y,z,CHUCK['t'],CHUCK['pitch'],CHUCK['bolt'])
for dx in (-CHUCK['pin_pitch']/2,CHUCK['pin_pitch']/2): zhole('Vacuum_Chuck_200C',dx,0,z,CHUCK['t'],CHUCK['pin'])
zhole('Vacuum_Chuck_200C',0,30,z,CHUCK['t'],CHUCK['pilot'])
# Surface vacuum ring, open to a top-side hose adapter (not a blind decorative groove).
s=CHUCK['groove_span']; w=CHUCK['groove_w']; h=CHUCK['groove_depth']; top=z+CHUCK['t']/2
for dx,dy,lx,ly in ((0,-s/2,s,w),(0,s/2,s,w),(-s/2,0,w,s),(s/2,0,w,s),(0,35,w,30)):
    CUTS.append(('Vacuum_Chuck_200C','box',(dx,dy,top-h/2,lx,ly,h)))
x,y,z=POSITIONS['reflow']; box('Reflow_Plate','reflow_chuck','al',(x,y,z),(REFLOW['w'],REFLOW['d'],REFLOW['t']))
plate_holes('Reflow_Plate',x,y,z,REFLOW['t'],REFLOW['pitch'],REFLOW['bolt'])
CUTS.append(('Reflow_Plate','cyl',(x,y,z+REFLOW['t']/2-REFLOW['tc_depth'],z+REFLOW['t']/2+1,REFLOW['tc_d']/2)))
box('Reflow_Heater','reflow_chuck','aln',(x,y,z-REFLOW['t']/2-REFLOW['heater_t']/2),(REFLOW['heater_w'],REFLOW['heater_w'],REFLOW['heater_t']))
box('Reflow_Insulator','reflow_chuck','calsil',(x,y,z-REFLOW['t']/2-REFLOW['heater_t']-REFLOW['ins_t']/2),(40,40,REFLOW['ins_t']))
# Parked service stations: interchangeable tooling, not simultaneous bonding sites.
box('Reflow_Pedestal','frame','al',(x,y,99.5),(50,50,99)) # base top50 -> insulation bottom149
x,y,z=POSITIONS['mold']; box('Mold_Block','mold_jig','steel',(x,y,z),(MOLD['w'],MOLD['d'],MOLD['t']))
bottom=z-MOLD['t']/2
CUTS.append(('Mold_Block','box',(x,y,bottom+MOLD['cavity_d']/2,MOLD['cavity_w'],MOLD['cavity_w'],MOLD['cavity_d'])))
bore_x=x+MOLD['cavity_w']/2+MOLD['gate_l']
zhole('Mold_Block',bore_x,y,z,MOLD['t'],MOLD['bore'])
CUTS.append(('Mold_Block','box',(x+MOLD['cavity_w']/2+MOLD['gate_l']/2,y,bottom+MOLD['gate_d']/2,MOLD['gate_l'],MOLD['gate_w'],MOLD['gate_d'])))
vent_l=(MOLD['w']-MOLD['cavity_w'])/2
CUTS.append(('Mold_Block','box',(x-MOLD['cavity_w']/2-vent_l/2,y,bottom+MOLD['vent_d']/2,vent_l,MOLD['vent_w'],MOLD['vent_d'])))
plate_holes('Mold_Block',x,y,z,MOLD['t'],MOLD['pitch'],MOLD['bolt'])
# Exploded parked plunger; working stroke and engagement are annotated in drawing.
P.append(('cyl','Plunger','plunger','steel',(bore_x,y,z+MOLD['t']/2+2,z+MOLD['t']/2+2+MOLD['plunger_l'],MOLD['bore']/2)))
box('Mold_Pedestal','frame','al',(x,y,107),(40,40,114)) # top164
box('Mold_Glass_Substrate','mold_jig','quartz',(x,y,169),(30,30,10))
# Plate glass is fully backed except a small observation aperture; cover needs independent screw clamping.
# Drawing features for the NCF tray: midterm 3장 GelPak nominal dimensions reused.
# Per-part provenance also records derived coordinates and every inherited tuple.
PART_SOURCES={n:dict(kind='중간값' if n in {r[1] for r in MID.P} else '설계값',
 source='중간 3·7·11장, cad/midterm/spec.py; 신규 치수 spec_stacker.py; calc/hardware 결과로 검산',dimensions_mm=list(p),material=m,group=g) for _,n,g,m,p in P}
LIMITS=dict(force=v('limit.force',50,'N','원문 KPI PBL p7'),footprint=v('limit.footprint',600,'mm','원문 KPI PBL p7'),
 head_temp=v('limit.head_temp',400,'C','원문 KPI PBL p7'),warn_force=v('limit.warn_force',52,'N','중간 10장 소프트웨어 경고'),latch_force=v('limit.latch_force',55,'N','중간 10장 래치'),
 warn_temp=v('limit.warn_temp',410,'C','중간 10장 경고'),latch_temp=v('limit.latch_temp',420,'C','중간 10장 래치'))
def bounds(part):
    t,n,g,m,p=part
    if t=='box':
        x,y,z,a,b,c=p; return [x-a/2,y-b/2,z-c/2],[x+a/2,y+b/2,z+c/2]
    x,y,z0,z1,r,*_=p; return [x-r,y-r,z0],[x+r,y+r,z1]
def bbox():
    bb=[bounds(p) for p in P]
    return [max(b[1][i] for b in bb)-min(b[0][i] for b in bb) for i in range(3)]
