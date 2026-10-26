"""Revision C lower-three joint candidate; millimetres, source geometry immutable.

Native CAD owns the new conical collars, mating keyed adapters and metal
reference envelopes. Original closed triangle shells remain triangle evidence;
only a union adds one lower collar per shell. No source aperture is subtracted.
Local X=axial tangent, Y=circumferential tangent, Z=outward normal. World
coordinates and receiver datums come from assembly-study/core-assembly.json.
"""
from pathlib import Path
import sys,json,hashlib,math
import numpy as np
import trimesh
import build123d as b
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'joint-study'))
sys.path.insert(0,str(ROOT/'design-b'))
from build_options import _clean,make_shoulder_hardware_reference
from fuse_shells import boolean_part,mesh_part

SPEC={
 'collar_footprint_mm':[32.,24.], 'collar_corner_radius_mm':5.,
 'collar_inward_depth_mm':2.5,'collar_source_overlap_mm':.30,
 'collar_aperture_mm':[15.6,7.8],'collar_aperture_corner_radius_mm':3.5,
 'adapter_footprint_mm':[30.,22.],'adapter_corner_radius_mm':4.,
 'adapter_flat_washer_seat_z_mm':-7.1,
 'adapter_center_thickness_mm':4.55,'conforming_face_normal_clearance_mm':.05,
 'key_mm':[15.,7.4], 'key_corner_radius_mm':3.5,'key_outer_end_original_frame_mm':10.9,
 'bore_diameter_mm':5.4,'shoulder_diameter_mm':5.,'shoulder_length_mm':20.,'thread_M4_length_mm':8.,
 'inner_washer_mm':[5.3,15.,1.2],'outer_washer_mm':[4.3,12.,1.6],
 'nut_mm':{'across_flats':7.,'height':5.},
 'assumed_stack_errors_mm':{'adapter_thickness':.15,'collar_position':.15,'rail_stack':.10,'inner_washer_thickness':.10},
 'manufacturer_shoulder_length_tolerance_mm':[0.,.25],
}

def frame(j):
 M=np.eye(4);M[:3,:3]=np.column_stack([j['axial_tangent'],j['cross_tangent'],j['outward_axis']]);M[:3,3]=j['inner_surface_center_mm'];return M

def cone_in_frame(j,slope):
 """Exact world-axis cone transformed to each slot frame, including rear offset.

 Its radius at the centre's world Z is the recovered radius of that datum.
 Source triangulation deviation is separately sampled; this is not a reverse
 engineered exact source BREP or a claim of exact nominal shell conformance.
 """
 p=np.asarray(j['inner_surface_center_mm']); radius=float(np.linalg.norm(p[:2])); length=100.
 world=b.Pos(0,0,float(p[2])-length/2)*b.Cone(radius-slope*length/2,radius+slope*length/2,length,
  align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))
 location=b.Location(b.Plane(origin=tuple(p),x_dir=tuple(j['axial_tangent']),z_dir=tuple(j['outward_axis'])))
 return world.moved(location.inverse())

def make_parts(j,slope):
 cone=cone_in_frame(j,slope)
 inward=b.Pos(0,0,-SPEC['collar_inward_depth_mm'])*cone
 outward=b.Pos(0,0,SPEC['collar_source_overlap_mm'])*cone
 collar_slab=b.Pos(0,0,-5.)*b.extrude(b.RectangleRounded(*SPEC['collar_footprint_mm'],SPEC['collar_corner_radius_mm']),amount=7.)
 opening=b.Pos(0,0,-10.)*b.extrude(b.RectangleRounded(*SPEC['collar_aperture_mm'],SPEC['collar_aperture_corner_radius_mm']),amount=24.)
 collar=_clean((collar_slab & outward)-inward-opening)
 bottom=SPEC['adapter_flat_washer_seat_z_mm']
 base=b.Pos(0,0,bottom)*b.extrude(b.RectangleRounded(*SPEC['adapter_footprint_mm'],SPEC['adapter_corner_radius_mm']),amount=9.)
 base=base & (b.Pos(0,0,-SPEC['conforming_face_normal_clearance_mm'])*inward)
 key=b.Pos(0,0,-4.)*b.extrude(b.RectangleRounded(*SPEC['key_mm'],SPEC['key_corner_radius_mm']),amount=SPEC['key_outer_end_original_frame_mm']+4.)
 bore=b.Pos(0,0,bottom-1)*b.Cylinder(SPEC['bore_diameter_mm']/2,22.,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))
 adapter=_clean(base+key-bore)
 return collar,adapter,opening

def cleaned_export_mesh(mesh,path):
 """Inspect the actual STL boundary and record only numerical cleanup."""
 mesh.export(path); rt=trimesh.load_mesh(path); n0=len(rt.faces);rt.process(validate=True)
 cap_area=0.
 if not rt.is_watertight:
  n=len(rt.faces);trimesh.repair.fill_holes(rt);cap_area=float(rt.area_faces[n:].sum());assert cap_area<1e-6,cap_area
 assert rt.is_watertight and rt.is_winding_consistent and len(rt.split())==1,(path,rt.is_watertight,len(rt.split()))
 rt.export(path); check=trimesh.load_mesh(path)
 assert check.is_watertight and check.is_winding_consistent and len(check.split())==1
 return check,{'duplicate_or_degenerate_faces_removed':n0-len(rt.faces),'numerical_pinhole_cap_area_mm2':cap_area}

def export_native(shape,path):
 assert shape.is_valid and len(shape.solids())==1
 b.export_step(shape,path.with_suffix('.step'));b.export_stl(shape,path.with_suffix('.stl'),tolerance=.015,angular_tolerance=.08)
 return cleaned_export_mesh(trimesh.load_mesh(path.with_suffix('.stl')),path.with_suffix('.stl'))[0]

def mesh_solid_volume(a,bmesh):
 return float((boolean_part(a)^boolean_part(bmesh)).volume())

def conical_source_probe(j,source,slope):
 M=frame(j);p=np.asarray(j['inner_surface_center_mm']); r0=np.linalg.norm(p[:2])-slope*p[2]
 # Exclude the slot; ray source points start inside the conical shell.
 xy=np.array([(x,y) for x in np.linspace(-15,15,13) for y in np.linspace(-11,11,13) if abs(x)>9 or abs(y)>5])
 local=np.column_stack([xy,np.full(len(xy),-4.)]);origins=trimesh.transform_points(local,M); directions=np.tile(M[:3,2],(len(local),1))
 hits,ir,it=source.ray.intersects_location(origins,directions,multiple_hits=False)
 assert len(hits)==len(xy),(j['id'],len(hits),len(xy))
 # Analytic cone residual signed along its local surface normal.
 residual=(np.linalg.norm(hits[:,:2],axis=1)-slope*hits[:,2]-r0)/math.sqrt(1+slope*slope)
 return {'probe_count':len(hits),'analytic_cone_to_source_inner_ray_hit_signed_range_mm':[float(residual.min()),float(residual.max())],
 'max_absolute_signed_surface_residual_mm':float(np.abs(residual).max()),
 'basis':'First outward ray contact on original triangulated source shell; points span collar footprint outside aperture. Conical inference, not exact source BREP.'}

def main():
 for dirname in ['parts','assembled','reinforced-shells','print']:(HERE/dirname).mkdir(parents=True,exist_ok=True)
 core=json.loads((ROOT/'assembly-study/core-assembly.json').read_text());slope=core['cone_slope']
 hardware=make_shoulder_hardware_reference(20.)
 hardware['outer-M4-wide-washer-reference']=_clean(b.Cylinder(6.,1.6,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))-
  b.Cylinder(2.15,1.6,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN)))
 refs={name:export_native(shape,HERE/'parts'/name) for name,shape in hardware.items()}
 source_handle=trimesh.load_mesh(ROOT/'assembly-study/parts/assembled-04.stl')
 components=[];collar_refs=[];joints=[];shells=[];valid=[]
 for j in [x for x in core['joints'] if x['side']==-1]:
  name=j['id'];M=frame(j);n=M[:3,2];p=M[:3,3];sid=j['shell_object']
  collar,adapter,opening=make_parts(j,slope)
  locals_={'continuous-collar':export_native(collar,HERE/'parts'/f'{name}-continuous-collar-local'),
   'conforming-keyed-adapter':export_native(adapter,HERE/'parts'/f'{name}-conforming-keyed-adapter-local')}
  openingmesh=export_native(opening,HERE/'parts'/f'{name}-collar-opening-tool-local')
  base_t=4.6;H=-7.1-1.2;E=H+20.;G=float(j['nominal_grip_stack_mm']);gap=E-G
  bounds=[gap-sum(SPEC['assumed_stack_errors_mm'].values()),gap+sum(SPEC['assumed_stack_errors_mm'].values())+.25]
  assert bounds[0]>0
  placements={'conforming-keyed-adapter':(locals_['conforming-keyed-adapter'],0.,True),
   'shoulder-bolt-reference':(refs['shoulder-bolt-reference'],H,False),
   'inner-M5-wide-washer-reference':(refs['inner-M5-wide-washer-reference'],H,False),
   'outer-M4-wide-washer-reference':(refs['outer-M4-wide-washer-reference'],E,False),
   'M4-nyloc-envelope-reference':(refs['M4-nyloc-envelope-reference'],E+1.6,False)}
  world={}
  for part,(mesh,z,printed) in placements.items():
   T=M.copy();T[:3,3]+=z*n; posed=mesh.copy();posed.apply_transform(T)
   path=HERE/'assembled'/f'{name}--{part}.stl'; posed,cleanup=cleaned_export_mesh(posed,path);world[part]=posed
   components.append({'joint':name,'name':part,'path':str(path.relative_to(ROOT)),'matrix_local_to_assembly':T.tolist(),
    'manufactured_here':printed,'material':'printed PETG candidate' if printed else 'purchased metal reference, DO NOT PRINT'})
  collarworld=locals_['continuous-collar'].copy();collarworld.apply_transform(M)
  cp=HERE/'assembled'/f'{name}--continuous-collar-reference.stl';collarworld,_=cleaned_export_mesh(collarworld,cp)
  # Collar mesh is a Boolean ingredient/reference, not an additional loose print.
  collar_refs.append({'joint':name,'name':'continuous-collar-reference','path':str(cp.relative_to(ROOT)),'matrix_local_to_assembly':M.tolist(),
   'manufactured_here':False,'material':'integrated portion of replacement shell; NOT a loose saddle or separate print'})
  srcpath=ROOT/'assembly-study/parts'/f'assembled-{sid:02d}.stl';source=trimesh.load_mesh(srcpath)
  solid=boolean_part(source)+boolean_part(collarworld)
  assert str(solid.status()).endswith('NoError')
  source_removed=float((boolean_part(source)-solid).volume()); assert abs(source_removed)<1e-3,source_removed
  overlap=float((boolean_part(source)^boolean_part(collarworld)).volume());assert overlap>0
  solid=solid.simplify(.002);mesh=mesh_part(solid)
  pieces=mesh.split(only_watertight=False);material=[a for a in pieces if abs(a.volume)>1e-7];assert len(material)==1
  reinforced,cleanup=cleaned_export_mesh(material[0],HERE/'reinforced-shells'/f'lower-only-shell-{sid}-assembled.stl')
  assert np.abs(reinforced.bounds-source.bounds).max()<.02
  Pinv=np.linalg.inv(np.array(core['source_transforms'][str(sid)]));ps=reinforced.copy();ps.apply_transform(Pinv)
  ps,print_cleanup=cleaned_export_mesh(ps,HERE/'print'/f'lower-only-shell-{sid}.stl')
  assert np.all(ps.extents<[256,256,260])
  shells.append({'source_id':sid,'path':str((HERE/'reinforced-shells'/f'lower-only-shell-{sid}-assembled.stl').relative_to(ROOT)),
   'print_path':str((HERE/'print'/f'lower-only-shell-{sid}.stl').relative_to(ROOT)),
   'source_mesh_path':str(srcpath.relative_to(ROOT)),'source_sha256':hashlib.sha256(srcpath.read_bytes()).hexdigest(),
   'source_subtraction_mm3':source_removed,'source_subtraction_measurement_stage':'Pre-simplification union diagnostic only; final STL undergoes whole-mesh numerical simplification and serialization. No deliberate source subtraction operation is used.','continuous_collar_source_overlap_mm3':overlap,'added_volume_mm3':float(reinforced.volume-source.volume),
   'print_extents_mm':ps.extents.tolist(),'print_transform_assembly_to_print':Pinv.tolist(),
   'print_orientation':'Original source shell orientation; open cone axis vertical; no support-free claim for inward collar ledge',
   'top_geometry':'No deliberately redesigned top slot/wall, upper collar or aperture cut. Whole-mesh simplify(.002mm) and float32 STL serialization alter tiny source facets including upper geometry; not mathematical surface identity.',
   'roundtrip_cleanup':cleanup,'print_roundtrip_cleanup':print_cleanup})
  # Positive adapter print transform: flat washer seat on Z0, bore vertical.
  P=np.eye(4);P[:3,3]=[15,11,7.1]
  ap=locals_['conforming-keyed-adapter'].copy();ap.apply_transform(P)
  ap,_=cleaned_export_mesh(ap,HERE/'print'/f'{name}-conforming-keyed-adapter.stl')
  # Exact Boolean interface checks against actual original receiver and fused shell.
  fit={'adapter_vs_original_shell_intersection_mm3':mesh_solid_volume(world['conforming-keyed-adapter'],source),
   'adapter_vs_original_handle_intersection_mm3':mesh_solid_volume(world['conforming-keyed-adapter'],source_handle),
   'adapter_vs_reinforced_shell_intersection_mm3':mesh_solid_volume(world['conforming-keyed-adapter'],reinforced),
   'adapter_vs_collar_intersection_mm3':mesh_solid_volume(world['conforming-keyed-adapter'],collarworld)}
  # Coincident CAD faces can tessellate to microscopic overlap; tolerance is
  # below .002mm Boolean simplification, not a physical manufacturing budget.
  assert max(fit.values())<.05,(name,fit)
  samples=np.asarray(locals_['conforming-keyed-adapter'].vertices)
  curved=samples[(samples[:,2]<-2.49)&(samples[:,2]>-6.99)&(np.linalg.norm(samples[:,:2],axis=1)>5)]
  min_body_thickness=float(curved[:,2].min()+7.1)
  row={'id':name,'shell_object':sid,'rail_object':4,'replaced_pin_object':j['pin_object'],'adapter_local_to_assembly':M.tolist(),
   'outward_axis':n.tolist(),'surface_center_mm':p.tolist(),'stock_grip_mm':G,
   'bolt_underhead_local_z_mm':H,'head_inner_face_local_z_mm':H-4.,'outer_washer_local_z_mm':E,'nut_outer_face_local_z_mm':E+1.6+5.,
   'nominal_capture_gap_mm':gap,'conditional_capture_gap_bounds_mm':bounds,'key_recess_at_outer_datum_mm':G-10.9,
   'thread_beyond_nut_nominal_mm':8.-1.6-5.,'adapter_min_sampled_body_thickness_mm':min_body_thickness,'conforming_face_nominal_normal_gap_mm':SPEC['conforming_face_normal_clearance_mm'],'conforming_face_nominal_gap_qualification':'Native CAD design gap, not uniform exported STL clearance; independent tessellation alters curved faces. Actual mesh closure must be probed.',
   'adapter_print_path':str((HERE/'print'/f'{name}-conforming-keyed-adapter.stl').relative_to(ROOT)),
   'adapter_print_local_transform':P.tolist(),'adapter_print_extents_mm':ap.extents.tolist(),
   'key_to_collar_clearance_per_face_mm':{'axial':.3,'circumferential':.2},
   'source_slot_min_about_mm':[16.,8.], 'source_aperture_cut':False,'source_aperture_cut_qualification':'No deliberate source opening recut; final whole-mesh numerical simplification and serialization do not preserve mathematical surface identity.',
   'conical_source_probe':conical_source_probe(j,source,slope),'exact_boolean_fit':fit}
  joints.append(row);valid.append({'joint':name,'native_solids_valid':True,'all_STL_exports_closed_single_solids':True,**fit})
  print(name,'done',fit,flush=True)
 record={'name':'Revision C lower-three conical-collar candidate','units':'mm','source_datum_revision':core['datum_revision'],'spec':SPEC,
  'joints':joints,'components':components,'collar_reference_components':collar_refs,'replacement_shells':shells,
  'printed_quantities':{'lower_only_reinforced_shells':3,'conforming_keyed_adapters':3},
  'removed_source_pin_ids':[14,15,16],'unchanged_upper_source_ids':[3,11,12,13],
  'outer_pad_decision':'No outer printed pad: fewer parts. OD12 metal washer remains over the actual curved/recessed handle receiver, with limited bearing patches after free play closes; not broad exterior conformal contact. No washer-strength or prior-FEA transfer claim.',
  'load_path':'Normal capture: head/inner metal washer -> flat adapter seat -> curved adapter/collar contact after0.05mm nominal face gap closes -> continuous shell. Opposite capture: outer washer/nut -> original rail. Shear: key into smaller reinforced collar opening, then continuous shell; no clamp-friction credit. Nominal collar-edge precedence is small and must survive real print tolerances.',
  'why_continuous':'Loose curved pads distribute normal pull-through but do not automatically thicken the source1mm slot edge against in-plane shear without justified preload/friction. This collar is manufactured continuously with the replacement shell.',
  'hardware_stop':'Outer washer ID4.3 < shoulder D5 creates metal stop at end of20mm shoulder. Nut must seat on washer against shoulder, leaving positive plastic capture gap. Physical hardware tolerances, undercut/chamfer/nyloc and locking remain unverified.',
  'capture_gap_basis':'Dominant outer receiver datum plane; footprint contact travel is separately probed. Stated interval includes the inherited assumed stack errors, not measured printer accuracy.',
  'source_mutation':'No original source or design-b files written; lower shells are source-mesh union one added collar each with no deliberate source subtraction or opening recut. Whole-mesh simplify(.002mm) and float32 export cleanup alter tiny source facets including upper geometry.',
  'print_scope':'Selective STL geometry and proposed orientations only. Actual printer/material/plate/slicer project, supports, layer paths and fit not verified; no print started.',
  'claim_boundary':'Geometric candidate only; no manufactured strength, fatigue, creep, comfort, airflow, range or safety rating. Existing B load/FE results do not transfer automatically.',
  'metal_reference_meshes_not_to_print':list(hardware)}
 (HERE/'lower-assembly.json').write_text(json.dumps(record,indent=2)+'\n')
 (HERE/'validation.json').write_text(json.dumps({'units':'mm','engine':'build123d native CAD + Manifold3.5.4','boolean_simplification_mm':.002,'results':valid,'shells':shells,
  'proof_boundary':record['claim_boundary']},indent=2)+'\n')
 print('Wrote',HERE/'lower-assembly.json',flush=True)

if __name__=='__main__':main()
