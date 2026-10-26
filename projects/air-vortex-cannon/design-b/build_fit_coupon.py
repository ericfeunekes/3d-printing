"""Cut a representative real shell/rail pair for a later small fit trial.

Original print-axis directions retained; no print or physical proof performed.
The coupon is not a strength specimen or a substitute for all-six access.
"""
from pathlib import Path
import sys,json
import numpy as np
import trimesh
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(HERE))
from fuse_shells import boolean_part,mesh_part

def main():
    out=HERE/'fit-coupon';out.mkdir(exist_ok=True)
    core=json.loads((ROOT/'assembly-study/core-assembly.json').read_text())
    j=next(r for r in core['joints'] if r['id']=='bottom-front')
    p=np.array(j['inner_surface_center_mm'])
    # Axis-aligned cutting box gives flat axial ends on the shell coupon.
    box=trimesh.creation.box(extents=[36.,42.,50.])
    box.apply_translation([p[0],p[1]-5.,p[2]])
    rows=[]
    for name,i,path in [('reinforced-shell-coupon',6,HERE/'reinforced-shells/shell-6-assembled.stl'),
                         ('original-rail-coupon',4,ROOT/'assembly-study/parts/assembled-04.stl')]:
        original=trimesh.load_mesh(path)
        cut=boolean_part(original)^boolean_part(box)
        assert str(cut.status()).endswith('NoError')
        m=mesh_part(cut.simplify(.002))
        pieces=[x for x in m.split(only_watertight=False) if abs(x.volume)>1e-7]
        assert len(pieces)==1
        m=pieces[0]
        m.export(out/(name+'-assembled.stl'))
        print_m=m.copy();print_m.apply_transform(np.linalg.inv(np.array(core['source_transforms'][str(i)])))
        print_m.apply_translation(-print_m.bounds[0])
        pathout=out/(name+'-print.stl');print_m.export(pathout)
        test=trimesh.load_mesh(pathout);test.process(validate=True)
        assert test.is_watertight and test.is_winding_consistent and len(test.split())==1
        test.export(pathout)
        assert trimesh.load_mesh(pathout).is_watertight
        rows.append({'name':name,'source_object':i,'source_path':str(path.relative_to(ROOT)),
                     'print_bounds_mm':test.extents.tolist(),'watertight':True,
                     'method':'Intersection with world36x42x50mm box; inverse original print rotation; translation tobedZ0. Mating surfaces not redesigned.'})
    (out/'coupon.json').write_text(json.dumps({'joint':'bottom-front','parts':rows,
      'use_with':'one keyed-adapter-print.stl plus actual specified hardware',
      'limits':['Fit trial only, not load or fatigue specimen','Cut free edges alter stiffness relative to whole cannon',
                'Shell collar lower ledge support/slice inspection still required','Other five installed positions remain separate checks']},indent=2)+'\n')
    print(json.dumps(rows,indent=2))

if __name__=='__main__':main()
