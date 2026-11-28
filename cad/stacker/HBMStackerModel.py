# Fusion API script: MSE489 educational die bonder - concept assembly (auto-generated)
import adsk.core, adsk.fusion, traceback, os, json, math
# Extended from cad/midterm/DieBonderModel/DieBonderModel.py (read-only original).
# Reload spec explicitly: Fusion Text Commands may reuse the Python process.
import importlib.util
from pathlib import Path
_spec=importlib.util.spec_from_file_location('stacker_geometry',Path(__file__).resolve().with_name('spec_stacker.py'))
G=importlib.util.module_from_spec(_spec); _spec.loader.exec_module(G)
D,P,CUTS=G.D,G.P,G.CUTS
COLORS={"Frame":(150,165,185),"Head":(170,130,200),"Stage":(225,190,120),"Optics":(90,190,150),"Process":(80,140,210),"Electrical":(120,120,120)}
MATCOL={"granite":(70,70,75),"macor":(245,245,240),"aln":(230,120,90),"quartz":(200,230,255)}
def run(context):
    ui=None
    try:
        app=adsk.core.Application.get(); ui=app.userInterface
        out=os.path.join(os.path.dirname(os.path.realpath(__file__)),"out"); os.makedirs(out,exist_ok=True)
        mesh=os.path.join(out,'mesh'); os.makedirs(mesh,exist_ok=True)
        # Delete only stale generated STL files; avoid mixing meshes from previous runs.
        for path in Path(mesh).glob('*.stl'): path.unlink()
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
        cut={}
        for n,kind,params in CUTS: cut.setdefault(n,[]).append((kind,params))
        groups={}; mass=0.0; rows=[]
        for t,n,g,m,p in P:
            if g not in groups:
                go=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); go.component.name=g; groups[g]=go.component
            occ=groups[g].occurrences.addNewComponent(adsk.core.Matrix3D.create()); c=occ.component; c.name=n
            if t=="box": body=tbox(*p)
            elif t=="cyl": body=tcyl(*p)
            else:
                cx,cy,z0,z1,ro,ri=p; body=tcyl(cx,cy,z0,z1,ro); tb.booleanOperation(body,tcyl(cx,cy,z0-1,z1+1,ri),adsk.fusion.BooleanTypes.DifferenceBooleanType)
            for kind,params in cut.get(n,[]):
                tool=tbox(*params) if kind=='box' else tcyl(*params)
                if not tb.booleanOperation(body,tool,adsk.fusion.BooleanTypes.DifferenceBooleanType):
                    raise RuntimeError('Boolean cut failed: '+n)
            b=c.bRepBodies.add(body); b.name=n
            kg=b.volume*D[m]/1000.0; mass+=kg; rows.append([g,n,m,round(kg,3)])
            ap=appearance(m if m in MATCOL else g, MATCOL.get(m,COLORS.get(g,(150,170,190))))
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
        # STEP + group meshes. All child occurrence transforms are identity;
        # dimensions are absolute in the shared assembly coordinate system.
        em=design.exportManager
        if not em.execute(em.createSTEPExportOptions(os.path.join(out,"HBMStacker.step"),root)):
            raise RuntimeError('STEP export failed')
        exported=[]
        for name,component in groups.items():
            options=em.createSTLExportOptions(component,os.path.join(mesh,name+'.stl'))
            options.isBinaryFormat=True
            options.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
            if not em.execute(options): raise RuntimeError('STL export failed: '+name)
            exported.append(name)
        try: fmass=sum(occ.component.bRepBodies.item(0).physicalProperties.mass for occ in root.allOccurrences if occ.component.bRepBodies.count>0)
        except: fmass=-1
        nap=sum(1 for v in apcache.values() if v)
        summary={"fusion_mass_kg":round(fmass,2),"appearances_created":nap,"mass_kg":round(mass,2),"bbox_mm":[round(s,1) for s in size],"interference_count":nint,"interference_pairs":pairs,"parts":rows,"mass_kind":"참고값; density-based mass is primary, Fusion library fallback may differ",
          "mesh_groups":exported,"mesh_units":"mm (Fusion STL default; validate 590 mm base before GLB)",
          "footprint_KPI_pass":max(size[:2])<=G.LIMITS['footprint'],
          "interference_pass":nint==0,"model_state":"parked tooling, unvalidated conceptual assembly",
          "design_review":"calc/hardware/*.json FAIL/REVIEW items must be resolved before fabrication"}
        json.dump(summary,open(os.path.join(out,"summary.json"),"w"),ensure_ascii=False,indent=1)
        ui.messageBox("완료\n질량 %.1f kg\n외곽 %.0f x %.0f x %.0f mm\n간섭 %d건\n결과: %s"%(mass,size[0],size[1],size[2],nint,out))
    except:
        if ui: ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
        raise
