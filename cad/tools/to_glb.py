"""STL -> indexed glTF 2.0 binary; Python stdlib + numpy, no trimesh.
Positions emitted in metres. STL input unit is explicitly selected (default mm).
Vertex clustering preserves volume approximately; never silently drops parts.
"""
from pathlib import Path
import argparse, json, struct
import numpy as np
MAX_BYTES=20*1024*1024

def read_stl(path):
    raw=Path(path).read_bytes()
    if len(raw)>=84:
        count=struct.unpack_from('<I',raw,80)[0]
        if 84+50*count==len(raw):
            dt=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attr','<u2')])
            triangles=np.frombuffer(raw,dtype=dt,offset=84,count=count)['vertices'].astype(np.float64)
        else: triangles=None
    else: triangles=None
    if triangles is None:
        vertices=[]
        for line in raw.decode('ascii').splitlines():
            words=line.split()
            if words and words[0].lower()=='vertex':
                if len(words)!=4: raise ValueError('Invalid ASCII vertex')
                vertices.append([float(x) for x in words[1:]])
        if not vertices or len(vertices)%3: raise ValueError(f'Invalid or empty STL: {path}')
        triangles=np.array(vertices,dtype=np.float64).reshape(-1,3,3)
    if not triangles.size or not np.isfinite(triangles).all(): raise ValueError('Empty/nonfinite STL')
    return triangles

def index_mesh(triangles,cell=0):
    points=triangles.reshape(-1,3)
    if cell:
        key=np.floor((points-points.min(axis=0))/cell).astype(np.int64)
        _,inverse=np.unique(key,axis=0,return_inverse=True)
        count=np.bincount(inverse)
        vertices=np.stack([np.bincount(inverse,weights=points[:,i])/count for i in range(3)],axis=1)
    else: vertices,inverse=np.unique(points,axis=0,return_inverse=True)
    faces=inverse.reshape(-1,3)
    keep=(faces[:,0]!=faces[:,1])&(faces[:,1]!=faces[:,2])&(faces[:,2]!=faces[:,0]); faces=faces[keep]
    if not len(faces): raise ValueError('Clustering collapsed a mesh; use finer cell or a larger size limit')
    area=np.linalg.norm(np.cross(vertices[faces[:,1]]-vertices[faces[:,0]],vertices[faces[:,2]]-vertices[faces[:,0]]),axis=1)
    faces=faces[area>0]
    if not len(faces): raise ValueError('All triangles degenerate')
    # Smooth vertex normals. Flat CAD faces may look rounded at sharp edges.
    normal=np.zeros_like(vertices)
    fn=np.cross(vertices[faces[:,1]]-vertices[faces[:,0]],vertices[faces[:,2]]-vertices[faces[:,0]])
    for i in range(3): np.add.at(normal,faces[:,i],fn)
    length=np.linalg.norm(normal,axis=1); normal[length>0]/=length[length>0,None]
    return vertices.astype('<f4'),faces.astype('<u4'),normal.astype('<f4')

def build(meshes,unit='mm',cell=0):
    doc=dict(asset={'version':'2.0','generator':'W4 stdlib+numpy STL converter'},scene=0,scenes=[{'nodes':[]}],nodes=[],meshes=[],materials=[],buffers=[],bufferViews=[],accessors=[],
             extras={'units':'m','sourceUnits':unit,'sourceToMetres':.001 if unit=='mm' else 1,'clusterCellSourceUnits':cell})
    blob=bytearray(); total=0
    def add(array,typ,component,target):
        while len(blob)%4: blob.append(0)
        offset=len(blob); data=array.tobytes(); blob.extend(data)
        vi=len(doc['bufferViews']); doc['bufferViews'].append(dict(buffer=0,byteOffset=offset,byteLength=len(data),target=target))
        access=dict(bufferView=vi,componentType=component,count=len(array),type=typ)
        if typ=='VEC3': access.update(min=array.min(axis=0).tolist(),max=array.max(axis=0).tolist())
        ai=len(doc['accessors']); doc['accessors'].append(access); return ai
    for i,(name,tris) in enumerate(meshes):
        v,f,n=index_mesh(tris,cell); v*=.001 if unit=='mm' else 1; total+=len(f)
        pos=add(v,'VEC3',5126,34962); norm=add(n,'VEC3',5126,34962); indices=add(f.reshape(-1),'SCALAR',5125,34963)
        colors=((.50,.58,.66,1),(.78,.48,.32,1),(.34,.63,.65,1))
        doc['materials'].append({'name':name,'pbrMetallicRoughness':{'baseColorFactor':colors[i%len(colors)],'metallicFactor':.15,'roughnessFactor':.65},'doubleSided':True})
        doc['meshes'].append({'name':name,'primitives':[{'attributes':{'POSITION':pos,'NORMAL':norm},'indices':indices,'material':i,'mode':4}]})
        doc['nodes'].append({'name':name,'mesh':i,'extras':{'sourceSTL':name+'.stl','units':'m'}}); doc['scenes'][0]['nodes'].append(i)
    # Fusion Z-up -> glTF Y-up: -90 degree rotation around X at each node, same world origin.
    for node in doc['nodes']: node['rotation']=[-2**-.5,0,0,2**-.5]
    while len(blob)%4: blob.append(0)
    doc['buffers']=[{'byteLength':len(blob)}]
    jb=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode(); jb+=b' '*((-len(jb))%4)
    length=12+8+len(jb)+8+len(blob)
    return struct.pack('<4sII',b'glTF',2,length)+struct.pack('<I4s',len(jb),b'JSON')+jb+struct.pack('<I4s',len(blob),b'BIN\x00')+blob,total

def convert(input_dir,output,unit='mm',limit=MAX_BYTES):
    paths=sorted(Path(input_dir).glob('*.stl'))
    if not paths: raise ValueError(f'No STL files: {input_dir}')
    meshes=[(p.stem,read_stl(p)) for p in paths]; cell=0
    extent=max(float(np.ptp(t.reshape(-1,3),axis=0).max()) for _,t in meshes)
    for attempt in range(18):
        data,triangles=build(meshes,unit,cell)
        if len(data)<=limit:
            Path(output).parent.mkdir(parents=True,exist_ok=True); Path(output).write_bytes(data)
            result=dict(bytes=len(data),triangles=triangles,nodes=[n for n,_ in meshes],cluster_cell=cell,units='m'); print(json.dumps(result)); return result
        cell=extent/2000 if not cell else cell*1.5
    raise ValueError('Cannot meet size limit while retaining all parts')
if __name__=='__main__':
    root=Path(__file__).resolve().parents[2]; p=argparse.ArgumentParser(); p.add_argument('--input',type=Path,default=root/'cad/stacker/out/mesh'); p.add_argument('--output',type=Path,default=root/'cad/web/hbm_stacker.glb'); p.add_argument('--unit',choices=['mm','m'],default='mm'); a=p.parse_args(); convert(a.input,a.output,a.unit)
