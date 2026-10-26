"""Continuous inner-shell collar candidates, derived from recovered joint poses.

Units mm. This creates new geometry; source meshes are never overwritten.
The matching opening is intentionally recut through the recommended shell.
No collar is a loose washer or credited with frictional shear transfer.
"""
from pathlib import Path
import sys,math,json
import numpy as np
import build123d as b

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'joint-study'))
from build_options import _clean

def cone_inside(radius,slope):
    length=100.
    shape=b.Pos(-length/2,0,-radius)*b.Rot(0,90,0)*b.Cone(
      radius-slope*length/2,radius+slope*length/2,length,
      align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))
    return b.Rot(0,math.degrees(math.atan(slope)),0)*shape

def make_collar(radius,slope,depth=2.5,length=32.,width=24.,
                opening_length=16.4,opening_width=8.2):
    slab=b.Pos(0,0,-depth)*b.extrude(b.RectangleRounded(length,width,5.),amount=depth+3.)
    # Extend .30mm into the original 1mm wall so the mesh union has overlap.
    collar=slab & (b.Pos(0,0,.30)*cone_inside(radius,slope))
    opening=b.Pos(0,0,-depth-1)*b.extrude(
       b.RectangleRounded(opening_length,opening_width,4.),amount=8.)
    collar=_clean(collar-opening)
    return collar,opening

def cad_to_mesh(shape,path):
    b.export_step(shape,path.with_suffix('.step'))
    b.export_stl(shape,path.with_suffix('.stl'),tolerance=.025,angular_tolerance=.12)

def main():
    data=json.loads((ROOT/'assembly-study/core-assembly.json').read_text())
    out=HERE/'collars';out.mkdir(parents=True,exist_ok=True)
    import trimesh
    rows=[]
    for j in data['joints']:
        p=np.array(j['inner_surface_center_mm'])
        M=np.eye(4);M[:3,:3]=np.column_stack([j['axial_tangent'],j['cross_tangent'],j['outward_axis']]);M[:3,3]=p
        radius=float(np.linalg.norm(p[:2]))
        collar,hole=make_collar(radius,data['cone_slope'])
        name=j['id'];cad_to_mesh(collar,out/(name+'-local'))
        cad_to_mesh(hole,out/(name+'-opening-local'))
        for suffix in ['','-opening']:
            m=trimesh.load_mesh(out/(name+suffix+'-local.stl'))
            assert m.is_watertight
            m.apply_transform(M);m.export(out/(name+suffix+'-assembled.stl'))
        rows.append({'joint':name,'shell_object':j['shell_object'],'radius_mm':radius,
          'local_to_assembly':M.tolist(),'collar_volume_mm3':collar.volume,
          'inner_depth_mm':2.5,'source_overlap_mm':.30,
          'footprint_mm':[32.,24.],'opening_mm':[16.4,8.2],
          'bearing_screen_thickness_mm':2.0,
          'limits':'Continuous fusion and all source-slot boundaries require exact mesh union and inspection; 2mm is conservative collar-only screening thickness, not a printed allowable.'})
    (out/'collar-specs.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps(rows,indent=2))

if __name__=='__main__':main()
