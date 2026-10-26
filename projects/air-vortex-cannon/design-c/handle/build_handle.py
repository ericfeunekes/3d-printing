"""Design C handle comparison, mm. Single owner of optional replacement geometry.

The recommendation retains source handle4; the optional rear/drop grip is a
reviewable geometric alternative, not an ergonomic or strength improvement.
Source mesh evidence is immutable. No B part is modified.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np,trimesh
from build123d import BuildPart,BuildSketch,BuildLine,Plane,Spline,ThreePointArc,Line,make_face,extrude,fillet,export_step,export_stl,import_step
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'assembly-study'));sys.path.insert(0,'/tmp/vortex-manifold')
import manifold3d as mf
from assemble import load_assembly
PARAMS={'rearward_grasp_shift_mm':30.,'grasp_drop_mm':20.,'grip_width_x_mm':25.,'grip_fore_aft_at_grasp_mm':30.,'edge_radius_mm':3.,'source_grip_cut_y_mm':-123.,'source_grip_cut_z_interval_mm':[70.,135.],'native_top_y_mm':-120.,'native_top_z_interval_mm':[84.,119.],'native_mesh_tolerance_mm':.04,'native_mesh_angular_tolerance_rad':.12}
SELECTED_HAND=[0.,-155.,110.4]

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def solid(mesh):
 s=mf.Manifold(mf.Mesh(np.asarray(mesh.vertices,dtype=np.float32),np.asarray(mesh.faces,dtype=np.uint32)))
 assert str(s.status()).endswith('NoError'),str(s.status())
 return s

def mesh(s):
 r=s.to_mesh64();v=np.asarray(r.vert_properties)[:,:3];f=np.asarray(r.tri_verts);remap=np.arange(len(v))
 for a,b in zip(r.merge_from_vert,r.merge_to_vert):remap[a]=b
 for _ in range(8):remap=remap[remap]
 m=trimesh.Trimesh(v,remap[f],process=False);m.remove_unreferenced_vertices();return m

def clean_export(m,p):
 m.export(p);r=trimesh.load_mesh(p);r.process(validate=True)
 assert r.is_watertight and r.is_winding_consistent and len(r.split())==1,(p,r.is_watertight,len(r.split()))
 r.export(p);rr=trimesh.load_mesh(p)
 assert rr.is_watertight and rr.is_winding_consistent and len(rr.split())==1
 return rr

def native_grip():
 dz=PARAMS['rearward_grasp_shift_mm'];drop=PARAMS['grasp_drop_mm'];g=110.4+dz
 width=PARAMS['grip_width_x_mm'];top_y=PARAMS['native_top_y_mm'];top_front,top_rear=PARAMS['native_top_z_interval_mm']
 # Profile in Z,Y. The top/throat stays at its original datum; lower profile
 # moves rearward and downward. Smooth interpolants are geometry hypotheses.
 half=PARAMS['grip_fore_aft_at_grasp_mm']/2
 front=[(top_front,top_y),(92,-130-.25*drop),(g-30.4,-142-.65*drop),(g-half,-155-drop),(g-13.9,-174-drop),(g-11.4,-185-drop)]
 rear=[(g+16.6,-184-drop),(g+17.6,-174-drop),(g+half,-155-drop),(g+3.6,-138-drop),(127,-124-.8*drop),(top_rear,top_y)]
 P=Plane(origin=(width/2,0,0),x_dir=(0,0,1),z_dir=(-1,0,0))
 with BuildPart() as b:
  with BuildSketch(P):
   with BuildLine():
    Spline(*front)
    ThreePointArc(front[-1],(g+2.6,-188-drop),rear[0])
    Spline(*rear)
    Line(rear[-1],front[0])
   make_face()
  extrude(amount=PARAMS['grip_width_x_mm'])
  edge=[e for e in b.part.edges() if abs(abs(e.center().X)-width/2)<1e-5]
  fillet(edge,PARAMS['edge_radius_mm'])
 assert b.part.is_valid and len(b.part.solids())==1
 return b.part,front,rear

def main():
 originals,T,meta=load_assembly();source=originals[4];s=solid(source)
 native,front,rear=native_grip()
 export_step(native,HERE/'optional-grip-native.step')
 step_roundtrip=import_step(HERE/'optional-grip-native.step')
 assert step_roundtrip.is_valid and len(step_roundtrip.solids())==1
 step_volume_relative_error=abs(step_roundtrip.volume-native.volume)/native.volume
 assert step_volume_relative_error<1e-6
 export_stl(native,HERE/'optional-grip-native.stl',tolerance=PARAMS['native_mesh_tolerance_mm'],angular_tolerance=PARAMS['native_mesh_angular_tolerance_rad'])
 add=solid(trimesh.load_mesh(HERE/'optional-grip-native.stl'))
 # Only hanging grip is removed. All original rail/receiver regions are kept.
 z_start,z_end=PARAMS['source_grip_cut_z_interval_mm'];cut_y=PARAMS['source_grip_cut_y_mm']
 cutter=mf.Manifold.cube([100.,200.,z_end-z_start]).translate([-50.,cut_y-200.,z_start])
 retained=s-cutter;removed=s^cutter
 revised=retained+add
 assert str(revised.status()).endswith('NoError')
 assert len(revised.decompose())==1
 assembled=clean_export(mesh(revised),HERE/'optional-handle-assembled.stl')
 clean_export(mesh(retained),HERE/'retained-source-rail.stl')
 # Original source's broad flat X face lies on plate; print XY are assembled
 # Z/Y, thickness is assembledX. Rigid transform, no scale change.
 P=np.array([[0.,0.,1.,0.],[0.,1.,0.,0.],[-1.,0.,0.,0.],[0.,0.,0.,1.]])
 pr=assembled.copy();pr.apply_transform(P);offset=-pr.bounds[0];P[:3,3]=offset
 pr=assembled.copy();pr.apply_transform(P);printed=clean_export(pr,HERE/'optional-handle-print.stl')
 protects=[]
 for j in [x for x in meta['joints'] if x['rail_object']==4]:
  # Boxes in actual joint frame: axial±15,cross±20, from2mminside to20mm
  # outward of inner shell. Includes original aperture and receiver surfaces.
  M=np.array(j['pin_local_to_assembly']);box=trimesh.creation.box(extents=[30,40,24]);box.apply_translation([0,0,10]);box.apply_transform(M);q=solid(box)
  before=s^q;after=revised^q
  changed=(before-after).volume()+(after-before).volume()
  assert changed<1e-5,(j['id'],changed)
  protects.append({'joint':j['id'],'changed_material_volume_mm3':changed,'protected_joint_local_box_mm':{'axial':[-15,15],'cross':[-20,20],'normal':[-2,22]},'position_and_original_receiver_geometry':'unchanged'})
 collisions=[]
 rec=json.loads((ROOT/'design-b/recommended-assembly.json').read_text())
 obstacles={f'source-{i}':m for i,m in originals.items() if i not in [4,14,15,16]}
 c_validation=ROOT/'design-c/joints/validation.json'
 if c_validation.exists():
  c=json.loads(c_validation.read_text())
  for row in c['shells']:obstacles[f"source-{row['source_id']}"]=trimesh.load_mesh(ROOT/row['path'])
  for p in (ROOT/'design-c/joints/assembled').glob('*.stl'):
   if 'continuous-collar-reference' not in p.name:obstacles['C/'+p.stem]=trimesh.load_mesh(p)
 else:
  obstacles.update({r['joint']+'/'+r['name']:trimesh.load_mesh(ROOT/r['path']) for r in rec['components'] if r['joint'].startswith('bottom-') and r['name']!='keyed-adapter-local'})
 for name,o in obstacles.items():
  vol=(revised^solid(o)).volume()
  collisions.append({'obstacle':name,'intersection_volume_mm3':vol})
 # Original has tiny shell nominal tangency contact; added native region must
 # introduce no new collision with any retained part or identical C hardware.
 added_collisions=[{'obstacle':name,'added_native_intersection_mm3':(add^solid(o)).volume()} for name,o in obstacles.items()]
 assert max(r['added_native_intersection_mm3'] for r in added_collisions)<1e-5
 optional_hand=[0.,-155.-PARAMS['grasp_drop_mm'],110.4+PARAMS['rearward_grasp_shift_mm']]
 assert source.contains([SELECTED_HAND])[0] and assembled.contains([optional_hand])[0]
 result={'units':'mm','coordinate_system':'Xhorizontal,Yup,Zrearward;frontoutletZ0','status':'Original source grip selected. Optional rear/drop native grip is a comparison prototype, unqualified for strength/comfort.','geometry_owner':'design-c/handle/build_handle.py','selected_handle':{'source_id':4,'source_path':'source/egordv/obj_4_Handle03.STEP.stl','source_sha256':digest(ROOT/'source/egordv/obj_4_Handle03.STEP.stl'),'source_to_assembly':T[4].tolist(),'hand_point_mm':SELECTED_HAND,'volume_mm3':source.volume,'centroid_mm':source.center_mass.tolist()},'optional_handle':{'parameters':PARAMS,'hand_point_mm':optional_hand,'native_profile_front_zy_mm':front,'native_profile_rear_zy_mm':rear,'native_solid_valid':bool(native.is_valid),'native_solid_count':len(native.solids()),'native_volume_mm3':native.volume,'removed_source_grip_volume_mm3':removed.volume(),'native_overlap_with_retained_rail_mm3':(retained^add).volume(),'final_manifold_status':str(revised.status()),'watertight':assembled.is_watertight,'winding_consistent':assembled.is_winding_consistent,'components':len(assembled.split()),'volume_mm3':assembled.volume,'centroid_mm':assembled.center_mass.tolist(),'assembled_bounds_mm':assembled.bounds.tolist(),'print_bounds_mm':printed.extents.tolist(),'assembly_to_print':P.tolist(),'print_orientation':'Broad side on plate; assembledX is buildnormal, all main hand/rail in-plane forcepaths lie in layers. Confirm source receiver bridges/supports in actual slicer.','print_envelope_limit':'Fits nominal256×256×260mmbuildenvelope; noactualprinterprofile,slicing,print ormaterialstrengthcheckperformed.','mount_protection':protects,'solid_part_intersections':collisions,'native_added_region_intersections':added_collisions,'source_and_export_units':'Millimetres,STLisunitless;GLBconsumermustscale0.001.'},'exchange_limit':'Source handle is supplied only as triangulated STL despite STEP in filename. STEP represents the exact new native replacement region only; fused wholehandle is a boolean mesh, rebuilt from thisowner.','physical_limits':['Hand ellipsoid is a chosen proxy, not measured anthropometry; positive clearance does not prove finger articulation or comfort.','New throat web loads the unmodified original rail, then three receivers, keys, washers and bolts; actual reaction distribution and root/rail capacity are unproved.','FDM fillets and valid solids do not prove strength, fatigue, layer bonds or hardware locking.','Original upper rail/pins, three body positions, bag/elastic/outlet remain outside handle modification.', 'Optional replacement grip blocks the assumed middle exterior R6 x 30 mm tool envelope; see motion-service-checks.json. It is not a service-qualified recommendation.']}
 result['optional_handle']['native_step_roundtrip']={'valid':bool(step_roundtrip.is_valid),'solid_count':len(step_roundtrip.solids()),'volume_mm3':step_roundtrip.volume,'volume_relative_error':step_volume_relative_error,'note':'STEP import/re-export kernel volume integration differs slightly; no claim of identical tessellation.'}
 (HERE/'handle-validation.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'selected_hand':SELECTED_HAND,'optional_hand':optional_hand,'volume_mm3':assembled.volume,'centroid_mm':assembled.center_mass.tolist(),'print_bounds_mm':printed.extents.tolist(),'mount_protection':protects},indent=2))
if __name__=='__main__':main()
