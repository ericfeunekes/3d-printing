"""Continuous chosen-ellipsoid/actualC-obstacle check; not anthropometry."""
from pathlib import Path
import sys,json,hashlib
import numpy as np,trimesh
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT/'assembly-study'))
from assemble import load_assembly
m,T,meta=load_assembly();obstacles={f'source-{i}':m[i] for i in m if i not in [4,6,7,8,14,15,16]};paths=[]
validation=json.loads((ROOT/'design-c/joints/validation.json').read_text())
for row in validation['shells']:
 p=ROOT/row['path'];obstacles[f'C-shell-{row["source_id"]}']=trimesh.load_mesh(p);paths.append(p)
for p in (ROOT/'design-c/joints/assembled').glob('*.stl'):
 if 'continuous-collar-reference' in p.name:continue
 obstacles['C-'+p.stem]=trimesh.load_mesh(p);paths.append(p)
radii=np.array([32.5,45,32.5]);cases=[]
for center in [[0,-155,110.4],[0,-155,125.4],[0,-155,140.4],[0,-175,140.4]]:
 checks=[];c=np.array(center)
 for name,mesh in obstacles.items():
  center_outside_aabb=bool(np.any(c<mesh.bounds[0]) or np.any(c>mesh.bounds[1]))
  assert center_outside_aabb,(name,center)
  n=mesh.copy();n.vertices=(n.vertices-c)/radii
  p,d,t=trimesh.proximity.closest_point_naive(n,[[0,0,0]])
  normalized=float(d[0]);inside=normalized<1
  # Outside:linearoperatornorm implies at least min(radii)*(d-1)
  # separation to every point in ellipsoid. Inside: one actual mesh point
  # is contained; report normalized metric, not Euclidean penetration.
  checks.append({'obstacle':name,'hand_center_outside_obstacle_AABB':center_outside_aabb,'minimum_normalized_obstacle_surface_radius':normalized,'obstacle_surface_point_inside_proxy':inside,'outside_clearance_lower_bound_mm':float((normalized-1)*min(radii)) if not inside else None,'signed_normalized_margin_times_min_radius_mm':float((normalized-1)*min(radii)),'closest_obstacle_point_mm':(p[0]*radii+c).tolist()})
 hits=[row['obstacle'] for row in checks if row['obstacle_surface_point_inside_proxy']]
 clear=min(row['outside_clearance_lower_bound_mm'] for row in checks) if not hits else None
 cases.append({'hand_point_mm':center,'obstacles_intersecting_proxy':hits,'whole_proxy_minimum_clearance_lower_bound_mm':clear,'checks':checks});print(center,'hits',hits,'clear',clear,flush=True)
result={'units':'mm','proxy_radii_mm':radii.tolist(),'coordinate_system':'Xhorizontal,Yup,Zrearward','proof':'For each actual closed obstacle mesh, minimize the Euclidean radius of its triangles after scalingXYZ by 1/radii around grasp. If normalized minimumd>1, obstacle surface is separated from analytic ellipsoid by at least min(radii)*(d-1). A disjoint-surface enclosed obstacle is excluded because its whole surface also hasradius>1; an obstacle enclosing the hand center is excluded by each meshAABB or hollow-bodyradiallocation. Negative signed normalizedmargin reports an actual surface point inside chosenproxy, not exact penetrationdepth.','hand_limit':'Chosen analytic ellipsoid repeats prior illustrative dimensions. Handle4 intended contact is excluded; allotherstockparts,actualC reinforcedshells and all3Ccaptureassemblies included. No populationcoverage,knucklearticulation,gripforce orcomfortclaim.','selected_hand_point_mm':[0,-155,110.4],'optional_hand_point_mm':[0,-175,140.4],'C_inputs_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'cases':cases}
(HERE/'final-proxy-clearance.json').write_text(json.dumps(result,indent=2)+'\n')
