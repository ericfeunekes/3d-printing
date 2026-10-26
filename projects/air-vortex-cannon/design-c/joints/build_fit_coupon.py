"""C front-lower actual-interface fit coupon; mm, no strength proof/print."""
from pathlib import Path
import sys,json,hashlib
import numpy as np,trimesh
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE));from build_lower import cleaned_export_mesh
sys.path.insert(0,str(ROOT/'design-b'));from fuse_shells import boolean_part,mesh_part

def main():
 out=HERE/'fit-coupon';out.mkdir(exist_ok=True)
 core=json.loads((ROOT/'assembly-study/core-assembly.json').read_text());j=next(r for r in core['joints'] if r['id']=='bottom-front');p=np.array(j['inner_surface_center_mm'])
 box=trimesh.creation.box(extents=[36.,42.,50.]);box.apply_translation([p[0],p[1]-5.,p[2]])
 rows=[]
 for name,i,path in [('c-conical-collar-shell-coupon',6,HERE/'reinforced-shells/lower-only-shell-6-assembled.stl'),('original-handle-receiver-coupon',4,ROOT/'assembly-study/parts/assembled-04.stl')]:
  cut=boolean_part(trimesh.load_mesh(path))^boolean_part(box);assert str(cut.status()).endswith('NoError')
  m=mesh_part(cut.simplify(.002));pieces=[x for x in m.split(only_watertight=False) if abs(x.volume)>1e-7];assert len(pieces)==1
  m,cleanup=cleaned_export_mesh(pieces[0],out/(name+'-assembled.stl'))
  print_m=m.copy();T=np.linalg.inv(np.array(core['source_transforms'][str(i)]));print_m.apply_transform(T)
  translation=-print_m.bounds[0];print_m.apply_translation(translation);P=np.eye(4);P[:3,3]=translation;P=P@T
  check,print_cleanup=cleaned_export_mesh(print_m,out/(name+'-print.stl'))
  assert abs(check.bounds[0,2])<1e-6
  rows.append({'name':name,'source_object':i,'source_path':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
   'assembled_path':str((out/(name+'-assembled.stl')).relative_to(ROOT)),'print_path':str((out/(name+'-print.stl')).relative_to(ROOT)),
   'print_bounds_mm':check.extents.tolist(),'assembly_to_print_transform':P.tolist(),'watertight':True,'single_solid':True,
   'method':'Derived from actual interface meshes by intersection with world36x42x50mm box, then simplify(.002mm), STL numerical cleanup, inverse original print rotation and translation to bedZ0. No deliberate mating-surface redesign; final mesh surfaces are not mathematically identical to the unsimplified cut.',
   'cleanup':cleanup,'print_cleanup':print_cleanup})
 data={'joint':'bottom-front','units':'mm','parts':rows,'use_with':{'adapter_path':'design-c/joints/print/bottom-front-conforming-keyed-adapter.stl','quantity':1,'hardware':'One actual D5/L20/M4 shoulderbolt +ID5.3OD15t1.2innerwasher +ID4.3OD12t1.6outerwasher +AF7h5M4lockingnut; simplified reference meshes DO NOT PRINT'},
  'limits':['Fit coupon only, not a load or fatigue specimen.','Cut edges change stiffness; full shell/handle and all3lowerinstalledpositions remain physical checks.','C matching curved contact includes0.05mm nominal normalgap; originalslots retained.','Actual printer/profile/support/bore/neck layer inspection still required; no print started.'],
  'fit_checks':['Hand insertion of15x7.4key through collar15.6x7.8andoriginalapproximately16x8slots after normal supportcleanup.','Conforming curved face fit and flat innerwasher seat.','Actual shoulderstop, measured positive freecapturegap, nutlocking and threadprojection.','Unloaded retention, handling wheninverted, deliberate unthreading/removal and tool access.']}
 (out/'coupon.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(rows,indent=2))

if __name__=='__main__':main()
