import unittest, tempfile, struct
from pathlib import Path
import numpy as np
from to_glb import convert, read_stl, index_mesh, build
from check_glb import check, G

def box():
    v=np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]],dtype=float)*10
    f=np.array([[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]])
    return v[f]
def write(path,tris,binary):
    if binary:
        raw=b'solid binary header'.ljust(80,b' ')+struct.pack('<I',len(tris))
        for t in tris: raw+=struct.pack('<12fH',0,0,0,*t.reshape(-1),0)
        path.write_bytes(raw)
    else:
        path.write_text('solid test\n'+''.join('facet normal 0 0 0\nouter loop\n'+''.join('vertex '+' '.join(map(str,v))+'\n' for v in t)+'endloop\nendfacet\n' for t in tris)+'endsolid test\n')
class Conversion(unittest.TestCase):
    def test_ascii_binary_names_units_and_indices(self):
        with tempfile.TemporaryDirectory() as folder:
            d=Path(folder); tris=box()
            for i,name in enumerate(G.NAMES): write(d/(name+'.stl'),tris+np.array([i*20,0,0]),i%2==0)
            result=convert(d,d/'test.glb'); doc=check(d/'test.glb')
            self.assertEqual(result['triangles'],120); np.testing.assert_allclose(doc['accessors'][0]['max'],[.19,.01,.01],rtol=1e-6)
            self.assertEqual(len(index_mesh(tris)[0]),8)
            for p in d.glob('*.stl'): self.assertEqual(read_stl(p).shape,(12,3,3))
    def test_cluster_removes_collapsed_triangles(self):
        tris=np.concatenate([box(),np.array([[[0,0,0],[.001,0,0],[0,.001,0]]])])
        _,f,_=index_mesh(tris,1); self.assertEqual(len(f),12)
    def test_invalid_stl(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'bad.stl'; p.write_text('solid empty\nendsolid')
            with self.assertRaises(ValueError): read_stl(p)
    def test_size_limit_fails_without_partial_output(self):
        with tempfile.TemporaryDirectory() as folder:
            d=Path(folder); write(d/'frame.stl',box(),True)
            with self.assertRaises(ValueError): convert(d,d/'bad.glb',limit=100)
            self.assertFalse((d/'bad.glb').exists())
if __name__=='__main__': unittest.main()
