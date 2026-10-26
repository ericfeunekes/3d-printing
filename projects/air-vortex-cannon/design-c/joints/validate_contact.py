"""Inspect actual exported C interfaces; no strength/FEA claim."""
from pathlib import Path
import sys,json,hashlib
import numpy as np,trimesh
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'design-b'))
from fuse_shells import boolean_part,mesh_part,manifold3d

NAMES=['shoulder-bolt-reference','inner-M5-wide-washer-reference','outer-M4-wide-washer-reference','M4-nyloc-envelope-reference']

def threshold_contact(adapter,obstacle,direction):
 a=boolean_part(adapter);o=boolean_part(obstacle);direction=np.asarray(direction)
 def volume(t):return float((a.translate(tuple(direction*t))^o).volume())
 lo=0.;hi=1.
 assert volume(lo)<1e-4 and volume(hi)>1e-4
 for _ in range(20):
  mid=(lo+hi)/2
  if volume(mid)>1e-4:hi=mid
  else:lo=mid
 return {'nonintersecting_displacement_mm':lo,'intersecting_displacement_mm':hi,'intersection_threshold_mm3':1e-4}

def footprint(j,handle):
 M=np.array(j['adapter_local_to_assembly']); local=handle.copy();local.apply_transform(np.linalg.inv(M))
 # Actual annular OD12 washer projected over receiver. Rays travel inward
 # from its nominal inner face; the first receiver hit is bearing evidence.
 pts=[]
 for r in np.linspace(2.15,6.,41):
  for a in np.linspace(0,2*np.pi,256,endpoint=False):pts.append([r*np.cos(a),r*np.sin(a),j['outer_washer_local_z_mm']])
 pts=np.asarray(pts);directions=np.tile([0.,0.,-1.],(len(pts),1));hits,ir,it=local.ray.intersects_location(pts,directions,multiple_hits=False)
 z=float(hits[:,2].max());zmin=float(hits[:,2].min())
 return {'annular_probe_radii_mm':[2.15,6.],'annular_probe_count':len(pts),'receiver_hit_count':len(hits),
  'actual_receiver_surface_normal_z_range_mm':[zmin,z],'first_contact_travel_from_nominal_washer_mm':float(j['outer_washer_local_z_mm']-z),
  'dominant_plane_capture_gap_mm':j['nominal_capture_gap_mm'],
  'qualification':'Annular ray probes against actual receiver mesh. Sampling locates footprint first-contact approximately; it neither supplies full contact area nor validates washer stress.'}

def main():
 rec=json.loads((HERE/'lower-assembly.json').read_text());B=json.loads((ROOT/'design-b/recommended-assembly.json').read_text());handle=trimesh.load_mesh(ROOT/'assembly-study/parts/assembled-04.stl')
 rows=[]
 for j in rec['joints']:
  name=j['id'];M=np.array(j['adapter_local_to_assembly']);adapter=trimesh.load_mesh(HERE/'assembled'/f'{name}--conforming-keyed-adapter.stl')
  collar=trimesh.load_mesh(HERE/'assembled'/f'{name}--continuous-collar-reference.stl')
  source=trimesh.load_mesh(ROOT/'assembly-study/parts'/f"assembled-{j['shell_object']:02d}.stl")
  clip=trimesh.creation.box(extents=[15.,7.4,40.]);clip.apply_transform(M)
  keyregion=mesh_part(boolean_part(adapter)^boolean_part(clip))
  edges=[]
  for axis,idx in [('axial',0),('circumferential',1)]:
   for sign in [-1,1]:
    direction=sign*M[:3,idx]
    full=threshold_contact(adapter,collar,direction)
    c=threshold_contact(keyregion,collar,direction);s=threshold_contact(keyregion,source,direction)
    edges.append({'axis':axis,'direction_sign':sign,'collar_key_region_first_contact':c,'original_slot_key_region_first_contact':s,'whole_adapter_first_contact_with_collar':full,
      'nominal_collar_contact_precedence_mm':s['nonintersecting_displacement_mm']-c['intersecting_displacement_mm'],
      'basis':'Rigid translated exported adapter clipped to key15x7.4 footprint, positive Boolean overlap1e-4mm3 threshold. Whole-adapter contact also recorded: matching curved base faces can contact before key edge. No preload/friction credited; this is CAD sequence, not physical stiffness/load sharing.'})
  hardware=[]
  for part in NAMES:
   path=HERE/'assembled'/f'{name}--{part}.stl';a=trimesh.load_mesh(path);ref=trimesh.load_mesh(ROOT/'design-b/assembled-joints'/f'{name}--{part}.stl')
   ca=next(c for c in rec['components'] if c['joint']==name and c['name']==part)
   cb=next(c for c in B['components'] if c['joint']==name and c['name']==part)
   diff=float(np.abs(np.array(ca['matrix_local_to_assembly'])-np.array(cb['matrix_local_to_assembly'])).max())
   bounddiff=float(np.abs(a.bounds-ref.bounds).max())
   assert diff<1e-12 and bounddiff<.03,(name,part,diff,bounddiff)
   hardware.append({'name':part,'world_pose_matrix_max_difference_from_B':diff,'world_bounds_max_difference_from_B_mm':bounddiff,'note':'Same hardware parameters and pose; independent tessellation tolerances can differ.'})
  rows.append({'joint':name,'collar_world_Y_bounds_mm':collar.bounds[:,1].tolist(),'collar_entirely_in_lower_half':bool(collar.bounds[1,1]<0),
   'key_edge_contact_sequence':edges,'exported_curved_face_outward_normal_first_contact':threshold_contact(adapter,collar,M[:3,2]),'actual_outer_washer_footprint':footprint(j,handle),'hardware_pose_comparison_B':hardware})
 out={'units':'mm','source_manifest':'design-c/joints/lower-assembly.json','manifest_sha256':hashlib.sha256((HERE/'lower-assembly.json').read_bytes()).hexdigest(),
  'results':rows,'limitations':['Contact thresholds and clearance geometry are ideal meshes, not tolerances or strength.','Small collar-before-source contact margin can reverse with real print error.','Curved/recessed exterior washer support remains narrow and no B washer FEA transfer is claimed.']}
 (HERE/'contact-validation.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(out,indent=2))

if __name__=='__main__':main()
