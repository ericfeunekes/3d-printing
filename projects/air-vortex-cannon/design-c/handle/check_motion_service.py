"""Additional scoped handles/motion/tool checks against owning geometry."""
from pathlib import Path
import sys,json
import numpy as np,trimesh
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT/'assembly-study'));sys.path.insert(0,str(HERE))
from assemble import load_assembly
from build_handle import solid
from model_ancillary import membrane_mesh
meshes,T,meta=load_assembly();record=json.loads((ROOT/'design-b/recommended-assembly.json').read_text());v=json.loads((HERE/'handle-validation.json').read_text());out=[]
for name,h in [('selected-original',meshes[4]),('optional-rear30-down20',trimesh.load_mesh(HERE/'optional-handle-assembled.stl'))]:
 s=solid(h);tools=[]
 for j in record['joints']:
  if not j['id'].startswith('bottom-'):continue
  M=np.array(j['adapter_local_to_assembly']);n=np.array(j['outward_axis']);start=M[:3,3]+n*(j['nut_outer_face_local_z_mm']+.1)
  tool=trimesh.creation.cylinder(radius=6,segment=np.array([start,start+n*30]),sections=96)
  tools.append({'joint':j['id'],'tool_origin_mm':start.tolist(),'tool_axis':n.tolist(),'tool_diameter_mm':12,'tool_length_mm':30,'handle_tool_intersection_mm3':(s^solid(tool)).volume()})
 rear=meta['rear_shell_plane_mm'];film_front=float(membrane_mesh(rear_plane=rear,stroke=0).bounds[0,2]);maxz=float(h.bounds[1,2]);maxy=float(h.bounds[1,1])
 out.append({'handle':name,'bottom_exterior_tool_checks':tools,'assumed_motion_clearance_bounds_mm':{'taut_film_cone_all_axial_strokes_0to60mm_axial_gap':film_front-maxz,'central_male_ring_all_axial_strokes_0to60mm_axial_gap':float(meshes[17].bounds[0,2]-maxz),'central_cap_all_axial_strokes_0to60mm_axial_gap':float(meshes[5].bounds[0,2]-maxz),'straight_elastic_tube_radius1p5mm_Y_gap':-1.5-maxy},'limits':'Taut film and straight bands are chosen prior geometry; actual bag folds, band slack, knot motion and human fingers not modeled. OffaxisXY motion does not change these axial bounds. Carabiner remains on assumed centerline.'})
(HERE/'motion-service-checks.json').write_text(json.dumps({'units':'mm','scope':'Handles only. Exterior tool is an assumed R6×30mm cylinder identical to prior study, not a purchased tool. C hardware worldposes equal B. No full assembly service certificate asserted.','results':out},indent=2)+'\n');print(json.dumps(out,indent=2))
