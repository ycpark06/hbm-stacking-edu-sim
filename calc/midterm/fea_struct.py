import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as sla, json, time, sys
h=float(sys.argv[1]) if len(sys.argv)>1 else 5.0   # voxel size mm
MODE=sys.argv[2] if len(sys.argv)>2 else "static"
VAR=sys.argv[3] if len(sys.argv)>3 else "v1"
ECC=float(sys.argv[4]) if len(sys.argv)>4 else 0.0
MAT={"al":(69e3,2.70e-9),"steel":(200e3,7.85e-9),"macor":(66.9e3,2.52e-9),"aln":(330e3,3.26e-9)}  # E[MPa], rho[t/mm3]
dz=-35.0  # head lowered toward bonding (collet tip 5 mm above chuck)
S1=[ # name, mat, kind, params (box: cx,cy,cz,lx,ly,lz ; cyl: cx,cy,z0,z1,r)
("col_L","al","box",(-235,120,285,40,60,470)),("col_R","al","box",(235,120,285,40,60,470)),
("beam","al","box",(0,120,542.5,510,60,45)),("arm","al","box",(0,20,542.5,200,140,45)),
("z_column","al","box",(0,30,420,70,20,260)),
("z_carriage","al","box",(0,0,363+dz,70,40,74)),("theta","steel","cyl",(0,0,310+dz,326+dz,30)),
("flexure","steel","box",(0,0,301+dz,50,50,18)),("loadcell","steel","cyl",(0,0,276+dz,292+dz,20)),
("gimbal","steel","cyl",(0,0,260+dz,276+dz,25)),("jacket","al","box",(0,0,254+dz,44,44,12)),
("macor","macor","box",(0,0,240+dz,40,40,16)),("heater","aln","box",(0,0,226+dz,30,30,12)),
("collet","steel","box",(0,0,215+dz,10,10,10)),
("stageX","al","box",(0,0,65,220,200,30)),("stageY","al","box",(0,0,95,220,200,30)),
("fine","al","box",(0,0,125,120,120,30)),("coolplate","al","box",(0,0,143,110,110,6)),
("insul","macor","box",(0,0,149,110,110,6)),("chuck","al","box",(0,0,161,100,100,18)),
]
HEAD=[x for x in S1 if x[0] in ("z_carriage","theta","flexure","loadcell","gimbal","jacket","macor","heater","collet")]
STAGE=[x for x in S1 if x[0] in ("stageX","stageY","fine","coolplate","insul","chuck")]
S2=[("col_L","al","box",(-235,0,280,40,80,460)),("col_R","al","box",(235,0,280,40,80,460)),
    ("beam","al","box",(0,0,540,510,80,60)),
    ("zrail_L","steel","box",(-45,0,400,20,40,220)),("zrail_R","steel","box",(45,0,400,20,40,220))]+HEAD+STAGE
S3=[("col_L","al","box",(-235,0,280,40,100,460)),("col_R","al","box",(235,0,280,40,100,460)),
    ("beam","al","box",(0,0,540,510,100,60)),
    ("zrail_L","steel","box",(-45,0,400,20,80,220)),("zrail_R","steel","box",(45,0,400,20,80,220))]+HEAD+STAGE
S4=[("col_L","al","box",(-235,0,280,40,160,460)),("col_R","al","box",(235,0,280,40,160,460)),
    ("beam","al","box",(0,0,540,510,100,60)),("shearwall","al","box",(0,60,355,440,20,310)),
    ("zrail_L","steel","box",(-45,0,400,20,80,220)),("zrail_R","steel","box",(45,0,400,20,80,220))]+HEAD+STAGE
S5=[("col_L","al","box",(-255,0,280,80,160,460)),("col_R","al","box",(255,0,280,80,160,460)),
    ("beam","al","box",(0,0,540,590,100,60)),("gus_L","al","box",(-185,0,480,60,100,60)),("gus_R","al","box",(185,0,480,60,100,60)),
    ("zrail_L","steel","box",(-45,0,400,20,80,220)),("zrail_R","steel","box",(45,0,400,20,80,220))]+HEAD+STAGE
S={"v1":S1,"v2":S2,"v3":S3,"v4":S4,"v5":S5}[VAR]
if MODE=="modal":
    frame=[x for x in S if x[0] in ("col_L","col_R","beam","arm","z_column","zrail_L","zrail_R","shearwall","gus_L","gus_R")]
    S=frame+[("carriage","al","box",(0,0,330,80,40,80)),("headblk","steel","box",(0,0,235,50,40,110)),
             ("stageXY","al","box",(0,0,80,220,200,60)),("fine","al","box",(0,0,125,120,120,30)),("stackblk","al","box",(0,0,155,110,110,30))]
CUT=[(("arm",),(0,20,535,170,110,30)),(("beam",),(0,120,535,480,40,30)),(("stageX","stageY","stageXY"),(40,0,80,80,40,60)),
     (("fine","coolplate","insul","chuck","stackblk"),(0,0,150,20,20,60))]
if VAR!="v1": CUT=[c for c in CUT if c[0]!=("arm",) and c[0]!=("beam",)]
xs=np.arange(-300+h/2,300,h); ys=np.arange(-110+h/2,160,h); zs=np.arange(50+h/2,570,h)
X,Y,Z=np.meshgrid(xs,ys,zs,indexing="ij")
mat=np.full(X.shape,-1,int); names=list(MAT)
def inbox(p): cx,cy,cz,lx,ly,lz=p; return (abs(X-cx)<lx/2)&(abs(Y-cy)<ly/2)&(abs(Z-cz)<lz/2)
for n,m,k,p in S:
    msk=inbox(p) if k=="box" else (((X-p[0])**2+(Y-p[1])**2<p[4]**2)&(Z>p[2])&(Z<p[3]))
    for parts,c in CUT:
        if n in parts: msk&=~inbox(c)
    mat[msk]=names.index(m)
el=np.argwhere(mat>=0); ne=len(el)
nx,ny,nz=len(xs)+1,len(ys)+1,len(zs)+1
nid=lambda i,j,k:(i*ny+j)*nz+k
off=np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]])
conn=nid(el[:,0,None]+off[:,0],el[:,1,None]+off[:,1],el[:,2,None]+off[:,2])
used,inv=np.unique(conn,return_inverse=True); conn=inv.reshape(conn.shape); nn=len(used)
# hex8 unit stiffness (E=1, cube side 1) via 2x2x2 Gauss
def kunit(nu):
    D=1/((1+nu)*(1-2*nu))*np.array([[1-nu,nu,nu,0,0,0],[nu,1-nu,nu,0,0,0],[nu,nu,1-nu,0,0,0],[0,0,0,(1-2*nu)/2,0,0],[0,0,0,0,(1-2*nu)/2,0],[0,0,0,0,0,(1-2*nu)/2]])
    K=np.zeros((24,24)); g=[0.5-0.5/np.sqrt(3),0.5+0.5/np.sqrt(3)]
    for a in g:
        for b in g:
            for c in g:
                dN=np.zeros((8,3))
                for q,(i,j,k) in enumerate(off):
                    fx=a if i else 1-a; fy=b if j else 1-b; fz=c if k else 1-c
                    sx=1 if i else -1; sy=1 if j else -1; sz=1 if k else -1
                    dN[q]=[sx*fy*fz,sy*fx*fz,sz*fx*fy]
                B=np.zeros((6,24))
                for q in range(8):
                    B[0,3*q]=dN[q,0];B[1,3*q+1]=dN[q,1];B[2,3*q+2]=dN[q,2]
                    B[3,3*q]=dN[q,1];B[3,3*q+1]=dN[q,0];B[4,3*q+1]=dN[q,2];B[4,3*q+2]=dN[q,1];B[5,3*q]=dN[q,2];B[5,3*q+2]=dN[q,0]
                K+=B.T@D@B/8
    return K
Ku=kunit(0.3)
Ee=np.array([MAT[names[m]][0] for m in mat[el[:,0],el[:,1],el[:,2]]]); rho=np.array([MAT[names[m]][1] for m in mat[el[:,0],el[:,1],el[:,2]]])
dofs=(3*conn[:,:,None]+np.arange(3)).reshape(ne,24)
rows=np.repeat(dofs,24,axis=1).ravel(); cols=np.tile(dofs,(1,24)).ravel()
vals=(Ee[:,None]*h*Ku.ravel()[None,:]).ravel()
K=sp.coo_matrix((vals,(rows,cols)),shape=(3*nn,3*nn)).tocsr(); del rows,cols,vals
# fixed: nodes on base top z=50 (k=0)
gk=used%nz; fixed=np.where(gk==0)[0]
free=np.setdiff1d(np.arange(3*nn),(3*fixed[:,None]+np.arange(3)).ravel())
coords=lambda n: np.array([ (n//nz)//ny, (n//nz)%ny, n%nz ])
def nearest_face_nodes(zface,x0,y0,rad,ry=None):
    ry=rad if ry is None else ry
    gi=(used//nz)//ny; gj=(used//nz)%ny
    xn=-300+gi*h; yn=-110+gj*h; zn=50+gk*h
    return np.where((abs(zn-zface)<1e-6)&(abs(xn-x0)<=rad)&(abs(yn-y0)<=ry))[0]
info={"h_mm":h,"elements":int(ne),"nodes":int(nn),"dof":int(3*nn)}
if MODE=="static":
    collet=nearest_face_nodes(215+dz-5,0,ECC,5,0.1 if ECC else 5); chuck=nearest_face_nodes(170,0,0,15)
    F=np.zeros(3*nn); F[3*collet+2]+=50/len(collet); F[3*chuck+2]-=50/len(chuck)
    Kf=K[free][:,free]; t=time.time()
    M=sp.diags(1/Kf.diagonal())
    u_f,inf=sla.cg(Kf,F[free],M=M,rtol=1e-10,maxiter=20000)
    u=np.zeros(3*nn); u[free]=u_f
    uc=u.reshape(-1,3)[collet].mean(0); uk=u.reshape(-1,3)[chuck].mean(0)
    rel=uc-uk
    info.update(dict(cg_info=int(inf),time_s=round(time.time()-t,1),collet_um=(uc*1e3).tolist(),chuck_um=(uk*1e3).tolist(),
        relative_um=(rel*1e3).tolist(),lateral_rel_um=float(np.hypot(rel[0],rel[1])*1e3),Kz_N_per_um=float(50/abs(rel[2]*1e3))))
    np.save("fea_u.npy",u); np.save("fea_used.npy",used)
    json.dump(dict(xs0=-260,ys0=-110,zs0=50,h=h,nx=nx,ny=ny,nz=nz),open("fea_grid.json","w"))
else:
    m_node=np.zeros(nn); np.add.at(m_node,conn.ravel(),np.repeat(rho*h**3/8,8))
    Mm=sp.diags(np.repeat(m_node,3)).tocsr()
    Kf=K[free][:,free]; Mf=Mm[free][:,free]; t=time.time()
    w2,V=sla.eigsh(Kf,k=6,M=Mf,sigma=0,which="LM")
    f=np.sqrt(np.abs(w2))/(2*np.pi)
    modes=[]
    for i in range(len(f)):
        v=np.zeros(3*nn); v[free]=V[:,i]; v=v.reshape(-1,3); a=np.abs(v).sum(0); modes.append(["XYZ"[int(np.argmax(a))]])
    info.update(dict(time_s=round(time.time()-t,1),freq_Hz=sorted(f.tolist()),dominant_dir=modes,mass_kg=float(m_node.sum()*1e3)))
print(json.dumps(info,indent=1))
info.update(variant=VAR,ecc_mm=ECC)
json.dump(info,open(f"fea_{MODE}_{VAR}_e{int(ECC)}_h{int(h)}.json","w"),indent=1)
