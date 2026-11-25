# Fusion API script: MSE489 educational die bonder - concept assembly (auto-generated)
import adsk.core, adsk.fusion, traceback, os, json, math
# Geometry spec (mm). Origin: base top-center projected to floor (x right, y back, z up). Bonding site at x=y=0.
# type, name, group, material, params
D={"calsil":0.45,"granite":2.65,"al":2.70,"steel":7.85,"macor":2.52,"aln":3.26,"quartz":2.20,"elec":0.45,"cam":0.8,"plastic":1.2}
P=[
("box","Base_Granite","Frame","granite",(0,0,25, 590,480,50)),
("box","Bridge_Column_L","Frame","al",(-255,0,280, 80,160,460)),
("box","Bridge_Column_R","Frame","al",(255,0,280, 80,160,460)),
("box","Bridge_Beam","Frame","al",(0,0,540, 590,100,60)),
("box","Gusset_L","Frame","al",(-185,0,480, 60,100,60)),
("box","Gusset_R","Frame","al",(185,0,480, 60,100,60)),
("box","Z_Rail_L","Head","steel",(-45,0,400, 20,80,220)),
("box","Z_Rail_R","Head","steel",(45,0,400, 20,80,220)),
("box","Z_Motor_Brake","Head","al",(0,0,600, 60,60,60)),
("box","Z_Carriage","Head","al",(0,0,363, 70,40,74)),
("cyl","Theta_Stage","Head","steel",(0,0,310,326, 30)),
("box","Flexure_Leaf_Spring","Head","steel",(0,0,301, 50,50,18)),
("cyl","Load_Cell_100N","Head","steel",(0,0,276,292, 20)),
("cyl","Gimbal_Lockable","Head","steel",(0,0,260,276, 25)),
("box","Cooling_Jacket","Head","al",(0,0,250.5, 44,44,19)),
("box","MACOR_Insulator","Head","macor",(0,0,233, 40,40,16)),
("box","AlN_Heater","Head","aln",(0,0,222.5, 20,20,5)),
("box","Collet_Tool","Head","steel",(0,0,215, 10,10,10)),
("box","Coarse_X_Stage","Stage","al",(0,0,65, 220,200,30)),
("box","Coarse_Y_Stage","Stage","al",(0,0,95, 220,200,30)),
("box","Fine_XY_Piezo_Stage","Stage","al",(0,0,125, 120,120,30)),
("box","Cooling_Plate","Stage","al",(0,0,143, 110,110,6)),
("box","CalSil_Insulation","Stage","calsil",(0,0,151, 110,110,10)),
("box","Vacuum_Chuck_200C","Stage","al",(0,0,165, 100,100,18)),
("cyl","Quartz_Window","Stage","quartz",(0,0,156,174, 7.5)),
("tube","Quartz_Gas_Shield","Stage","quartz",(0,0,174,184, 54,50)),
("box","Bottom_Camera","Stage","cam",(40,0,70, 50,22,22)),
("box","GelPak_Riser","Stage","al",(85,0,139, 50,50,58)),
("box","GelPak_Tray","Stage","plastic",(85,0,171, 50,50,6)),
("box","RefDie_Riser","Stage","al",(-80,-80,142, 30,30,64)),
("box","Prism_BeamSplitter","Optics","quartz",(0,0,192, 30,30,14)),
("box","Prism_Slide_Rail","Optics","al",(0,-115,189, 20,150,10)),
("box","Dual_Camera_Telecentric","Optics","cam",(0,-215,187, 40,50,34)),
("box","Dual_Camera_Post","Optics","al",(20,-215,347, 20,20,286)),
("box","Dual_Camera_Bracket","Optics","al",(20,-132.5,500, 20,165,20)),
("box","Side_Camera","Optics","cam",(-185,0,190, 50,26,26)),
("box","Side_Camera_Arm","Optics","al",(-187.5,0,208, 55,10,10)),
("cyl","Dispenser_Barrel","Process","plastic",(-80,0,240,330, 8)),
("cyl","Dispenser_Needle","Process","steel",(-80,0,205,240, 0.6)),
("box","Dispenser_Post","Process","al",(-80,0,420, 12,12,180)),
("box","Laser_Displacement","Process","cam",(0,-55,260, 20,30,60)),
("box","Laser_Post","Process","al",(0,-55,400, 12,12,220)),
("box","Electrical_Box","Electrical","elec",(0,200,135, 300,80,170)),
]
CUTS=[("Coarse_X_Stage",(40,0,65,80,40,30)),("Coarse_Y_Stage",(40,0,95,80,40,30)),("Fine_XY_Piezo_Stage",(0,0,125,22,22,30)),
      ("Cooling_Plate",(0,0,143,22,22,6)),("CalSil_Insulation",(0,0,151,22,22,10)),("Vacuum_Chuck_200C",(0,0,165,15,15,18))]

COLORS={"Frame":(150,165,185),"Head":(170,130,200),"Stage":(225,190,120),"Optics":(90,190,150),"Process":(80,140,210),"Electrical":(120,120,120)}
MATCOL={"granite":(70,70,75),"macor":(245,245,240),"aln":(230,120,90),"quartz":(200,230,255)}
def run(context):
    ui=None
    try:
        app=adsk.core.Application.get(); ui=app.userInterface
        out=os.path.join(os.path.dirname(os.path.realpath(__file__)),"out"); os.makedirs(out,exist_ok=True)
        doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design=adsk.fusion.Design.cast(app.activeProduct)
        design.designType=adsk.fusion.DesignTypes.DirectDesignType
        root=design.rootComponent
        tb=adsk.fusion.TemporaryBRepManager.get()
        Pt=lambda x,y,z: adsk.core.Point3D.create(x/10,y/10,z/10)
        V=adsk.core.Vector3D.create
        def tbox(cx,cy,cz,lx,ly,lz):
            return tb.createBox(adsk.core.OrientedBoundingBox3D.create(Pt(cx,cy,cz),V(1,0,0),V(0,1,0),lx/10,ly/10,lz/10))
        def tcyl(cx,cy,z0,z1,r): return tb.createCylinderOrCone(Pt(cx,cy,z0),r/10,Pt(cx,cy,z1),r/10)
        # appearances
        alib=None
        for i in range(app.materialLibraries.count):
            L=app.materialLibraries.item(i)
            if L.appearances.count>50: alib=L; break
        base=None
        if alib:
            for i in range(alib.appearances.count):
                a=alib.appearances.item(i)
                if any(k in a.name for k in ("Paint","페인트","Plastic","플라스틱","Powder","분체")): base=a; break
        apcache={}
        def appearance(key,rgb):
            if key in apcache or base is None: return apcache.get(key)
            try:
                ap=design.appearances.addByCopy(base,"DB_"+key)
                for j in range(ap.appearanceProperties.count):
                    pr=ap.appearanceProperties.item(j)
                    cp=adsk.core.ColorProperty.cast(pr)
                    if cp and cp.value is not None: cp.value=adsk.core.Color.create(rgb[0],rgb[1],rgb[2],0); break
                apcache[key]=ap
            except: apcache[key]=None
            return apcache[key]
        MATID={"al":"PrismMaterial-231","steel":"PrismMaterial-018","granite":"Material-141","aln":"PrismMaterial-408","quartz":"PrismMaterial-086","macor":"PrismMaterial-287"}
        mlib=None
        for i in range(app.materialLibraries.count):
            L=app.materialLibraries.item(i)
            if L.materials.count>200: mlib=L; break
        def phys(m):
            try: return mlib.materials.itemById(MATID[m]) if (mlib and m in MATID) else None
            except: return None
        cut={n:c for n,c in CUTS}
        groups={}; mass=0.0; rows=[]
        for t,n,g,m,p in P:
            if g not in groups:
                go=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); go.component.name=g; groups[g]=go.component
            occ=groups[g].occurrences.addNewComponent(adsk.core.Matrix3D.create()); c=occ.component; c.name=n
            if t=="box": body=tbox(*p)
            elif t=="cyl": body=tcyl(*p)
            else:
                cx,cy,z0,z1,ro,ri=p; body=tcyl(cx,cy,z0,z1,ro); tb.booleanOperation(body,tcyl(cx,cy,z0-1,z1+1,ri),adsk.fusion.BooleanTypes.DifferenceBooleanType)
            if n in cut: tb.booleanOperation(body,tbox(*cut[n]),adsk.fusion.BooleanTypes.DifferenceBooleanType)
            b=c.bRepBodies.add(body); b.name=n
            kg=b.volume*D[m]/1000.0; mass+=kg; rows.append([g,n,m,round(kg,3)])
            ap=appearance(m if m in MATCOL else g, MATCOL.get(m,COLORS[g]))
            if ap: b.appearance=ap
            pm=phys(m)
            if pm:
                try: b.material=pm
                except: pass
        # bounding box
        bb=root.boundingBox
        size=[(bb.maxPoint.x-bb.minPoint.x)*10,(bb.maxPoint.y-bb.minPoint.y)*10,(bb.maxPoint.z-bb.minPoint.z)*10]
        # interference
        nint=-1; pairs=[]
        try:
            ents=adsk.core.ObjectCollection.create()
            for occ in root.allOccurrences:
                if occ.component.bRepBodies.count>0: ents.add(occ)
            ii=design.createInterferenceInput(ents); ii.areCoincidentFacesIncluded=False
            res=design.analyzeInterference(ii); nint=res.count
            for k in range(res.count):
                r=res.item(k); pairs.append([r.entityOne.name,r.entityTwo.name,round(r.interferenceBody.volume*1000,3)])
        except Exception as e: pairs.append(["interference check failed",str(e),0])
        # views
        vp=app.activeViewport
        views={"iso":(1,-1.2,0.9),"front":(0,-1,0),"side":(1,0,0),"top":(0,0,1)}
        for k,(ex,ey,ez) in views.items():
            cam=vp.camera; tgt=adsk.core.Point3D.create(0,0,28)
            cam.target=tgt; cam.eye=adsk.core.Point3D.create(ex*300,ey*300,28+ez*300)
            cam.upVector=V(0,1,0) if k=="top" else V(0,0,1)
            cam.isFitView=True; vp.camera=cam; vp.fit(); adsk.doEvents()
            vp.saveAsImageFile(os.path.join(out,"view_"+k+".png"),1600,1200)
        # STEP
        try:
            em=design.exportManager; em.execute(em.createSTEPExportOptions(os.path.join(out,"MSE489_DieBonder.step"),root))
        except Exception as e: pass
        try: fmass=sum(occ.component.bRepBodies.item(0).physicalProperties.mass for occ in root.allOccurrences if occ.component.bRepBodies.count>0)
        except: fmass=-1
        nap=sum(1 for v in apcache.values() if v)
        summary={"fusion_mass_kg":round(fmass,2),"appearances_created":nap,"mass_kg":round(mass,2),"bbox_mm":[round(s,1) for s in size],"interference_count":nint,"interference_pairs":pairs,"parts":rows}
        json.dump(summary,open(os.path.join(out,"summary.json"),"w"),ensure_ascii=False,indent=1)
        ui.messageBox("완료\n질량 %.1f kg\n외곽 %.0f x %.0f x %.0f mm\n간섭 %d건\n결과: %s"%(mass,size[0],size[1],size[2],nint,out))
    except:
        if ui: ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
