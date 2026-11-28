"""Structural GLB validation independent of Fusion and three.js."""
import argparse, json, struct
from pathlib import Path
import importlib.util
s=importlib.util.spec_from_file_location('stacker',Path(__file__).resolve().parents[1]/'stacker/spec_stacker.py'); G=importlib.util.module_from_spec(s); s.loader.exec_module(G)
def check(path,require_all=True,limit=20*1024*1024):
    data=Path(path).read_bytes(); assert 28<=len(data)<=limit
    magic,version,size=struct.unpack_from('<4sII',data); assert (magic,version,size)==(b'glTF',2,len(data))
    off=12; chunks=[]
    while off<len(data):
        n,kind=struct.unpack_from('<I4s',data,off); assert n%4==0 and off+8+n<=len(data)
        chunks.append((kind,data[off+8:off+8+n])); off+=8+n
    assert off==len(data) and [x[0] for x in chunks]==[b'JSON',b'BIN\0']
    doc=json.loads(chunks[0][1]); assert doc['asset']['version']=='2.0'
    names=[x['name'] for x in doc['nodes']]; assert len(names)==len(set(names))
    assert set(names)<=set(G.NAMES),names
    if require_all: assert set(names)==set(G.NAMES)
    assert doc['extras']['units']=='m' and doc['buffers'][0]['byteLength']==len(chunks[1][1])
    binary=chunks[1][1]
    for view in doc['bufferViews']: assert view.get('byteOffset',0)+view['byteLength']<=len(binary)
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            pos=doc['accessors'][prim['attributes']['POSITION']]; idx=doc['accessors'][prim['indices']]
            assert pos['type']=='VEC3' and pos['componentType']==5126 and idx['count']%3==0
            view=doc['bufferViews'][idx['bufferView']]; offset=view.get('byteOffset',0)+idx.get('byteOffset',0)
            indices=struct.unpack_from('<'+'I'*idx['count'],binary,offset); assert max(indices)<pos['count']
    result=dict(status='PASS',bytes=len(data),nodes=names); print(json.dumps(result)); return doc
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('path',type=Path); a=p.parse_args(); check(a.path)
