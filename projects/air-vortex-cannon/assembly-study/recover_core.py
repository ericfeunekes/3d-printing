"""Recover stock assembly from cone lips and repeated connection datums.

Millimetres. Canonical X=tangential horizontal, Y=up, Z=axial rearward.
Outlet front plane is Z=0. Source meshes remain immutable.
"""
from pathlib import Path
import json,math
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(__file__).resolve().parent
SRC=ROOT/'source/egordv'
FILES={int(p.name.split('_')[1]):p for p in SRC.glob('*.stl')}
K=1/10.4
C=1/math.sqrt(1+K*K)
S=K*C
SHELL_Z={6:0.0,8:84.0,7:171.0}
# Slot-wall extrema in the section's conical tangent coordinate u.
# Direct mesh-derived bounds of the side faces (source X=124/132 etc).
SHELL_U={
 6:{1:70.1159800182,-1:69.9901726638},
 8:{1:69.3858811185,-1:69.3863248779},
 7:{1:31.7980128205,-1:31.6309738156},
}
SHELL_INNER_V={
 6:{1:89.23129142,-1:89.23129142},
 8:{1:102.12071865,-1:102.12071865},
 7:{1:114.91828676,-1:114.91828676},
}
SHELL_OUTER_V={6:90.23128608,8:103.12071914,7:115.91827838}
# Slot centreline recovered from constant-v sections of rail's print Z=12.5.
RAIL_U={3:[368.90913,452.03174,500.874345],4:[358.379445,441.50204,490.344645]}
# Rail cone-contact datum: sum of shell outer-normal coordinate and source
# rail's curved contact-face normal coordinate. Residual finite mesh detail
# and radial assembly clearance remain explicit, not fitted away.
RAIL_V_OFFSET={3:305.867,4:266.7655}
OUTER_RAIL_SOURCE_V={3:[205.6169731757,200.7781581785,196.3073586227],
                     4:[166.5156057463,161.6767974458,157.2059944144]}

def mat(R=None,t=None):
 M=np.eye(4)
 if R is not None:M[:3,:3]=R
 if t is not None:M[:3,3]=t
 return M

def load_mesh(i):
 return trimesh.load_mesh(FILES[i])

def core():
 meshes={};transforms={};datums=[]
 for i,offset in SHELL_Z.items():
  M=mat(t=[-128,-128,offset]);transforms[i]=M
  m=load_mesh(i);m.apply_transform(M);meshes[i]=m
 for i,sign in [(3,1),(4,-1)]:
  su=np.array([SHELL_U[j][sign]+C*SHELL_Z[j] for j in [6,8,7]])
  ru=np.array(RAIL_U[i]);u0=float(np.mean(su-ru));v0=RAIL_V_OFFSET[i]
  z0=C*u0-S*v0;y0=S*u0+C*v0
  if sign==1:
   R=np.array([[0,0,1],[0,-1,0],[1,0,0]]);t=[-12.5,y0,z0]
  else:
   R=np.array([[0,0,-1],[0,1,0],[1,0,0]]);t=[12.5,-y0,z0]
  M=mat(R,t);transforms[i]=M;m=load_mesh(i);m.apply_transform(M);meshes[i]=m
  for order,j in enumerate([6,8,7]):
   # Use the common interval midpoint rather than pretend slight source
   # axial slot offsets vanish. They lie within the nominal fit allowance.
   us=float(su[order]);ur=float(ru[order]+u0);u=(us+ur)/2
   vin=SHELL_INNER_V[j][sign]-S*SHELL_Z[j]
   vout=SHELL_OUTER_V[j]-S*SHELL_Z[j]
   outer_rail_v=RAIL_V_OFFSET[i]-OUTER_RAIL_SOURCE_V[i][order]
   # Source rear lower slot is 0.243576 mm tangentially off centre. The
   # top rail's rear slot also has this offset in the opposite direction.
   xshell=-.24357605 if j==7 and sign==-1 else 0.0
   xrail=(.24357605 if sign==1 else -.24357605) if j==7 else 0.0
   x=(xshell+xrail)/2
   normal=np.array([0,sign*C,-S]);tangent=np.array([0,sign*S,C]);cross=np.array([sign,0,0])
   base_v=vin-2.0
   p=np.array([x,sign*(S*u+C*base_v),C*u-S*base_v])
   clip_i={1:[11,12,13],-1:[14,15,16]}[sign][order]
   raw=load_mesh(clip_i);cent=raw.bounds.mean(0)
   source_to_local=mat(t=[-cent[0],-cent[1],-raw.bounds[0,2]])
   local_to_assembly=mat(np.column_stack([tangent,cross,normal]),p)
   Mpin=local_to_assembly@source_to_local
   transforms[clip_i]=Mpin;raw.apply_transform(Mpin);meshes[clip_i]=raw
   surface=np.array([x,sign*(S*u+C*vin),C*u-S*vin])
   datums.append({'id':f'{"top" if sign==1 else "bottom"}-{ {6:"front",8:"middle",7:"rear"}[j]}',
     'shell_object':j,'rail_object':i,'pin_object':clip_i,'side':sign,
     'shell_u_mm':us,'rail_u_mm':ur,'pin_u_mm':u,'axial_tangent_mismatch_mm':ur-us,
     'slot_tangential_shell_center_mm':xshell,'slot_tangential_rail_center_mm':xrail,
     'pin_tangential_center_mm':x,'inner_normal_coordinate_mm':vin,'outer_normal_coordinate_mm':vout,
     'outer_rail_bearing_normal_coordinate_mm':outer_rail_v,
     'nominal_grip_stack_mm':outer_rail_v-vin,
     'outer_rail_bearing_plane_pin_local_z_mm':outer_rail_v-(vin-2),
     'grip_stack_basis':'inner cone tangent plane to dominant outer rail bearing plane; near-hole chamfers/recesses are lower',
     'inner_surface_center_mm':surface.tolist(),'pin_base_origin_mm':p.tolist(),
     'outward_axis':normal.tolist(),'axial_tangent':tangent.tolist(),'cross_tangent':cross.tolist(),
     'pin_local_to_assembly':local_to_assembly.tolist(),
     'evidence':'cone-axis radial profile gives tangent-centre wall datum; slot side faces give u; video confirms head inside/tips outward',
     'uncertainty':'Rigid seated pose assumes head face at inner cone; flexible snap engagement and printed fit not proved'})
 return meshes,transforms,datums

def main():
 meshes,transforms,datums=core()
 d={'units':'mm','coordinates':'X=tangential horizontal,Y=up,Z=axial rearward; outletfrontplaneZ0',
    'datum_revision':2,'cone_slope':K,'cone_half_angle_deg':math.degrees(math.atan(K)),
    'shell_axial_offsets_mm':SHELL_Z,'rear_shell_end_mm':171+load_mesh(7).bounds[1,2],
    'source_transforms':{str(i):M.tolist() for i,M in transforms.items()},'joints':datums,
    'nominal_grasp_point_mm':[0,-155,110.4],
    'grasp_basis':'assumed hand contact within actual grip cross-sections, not a measured user hand pose',
    'assumptions':['Shell offset84/171 selected from lip fit; nominal CAD assembly, not measured object',
     'Rail normal pose includes0.10mm outward refinement from source section intersections; slight slot mismatches retained',
     'Clip pose is undeformed final seating assumption; no snap-flex/insertion-force proof'],
    'video_evidence':{'url':'https://www.youtube.com/watch?v=NKO3LCNGTJY&t=278s',
       'observed':'At4:38and4:43 builder hand inside barrel pushes blue clips outward; tips appear outside and cyan rail remains external',
       'inspection_date':'2026-10-25'}}
 (OUT/'core-assembly.json').write_text(json.dumps(d,indent=2)+'\n')
 (OUT/'parts').mkdir(exist_ok=True)
 for i,m in meshes.items():m.export(OUT/'parts'/f'assembled-{i:02d}.stl')
 scene=trimesh.Scene()
 for i,m in meshes.items():scene.add_geometry(m,node_name=FILES[i].stem)
 scene.apply_scale(.001)
 scene.export(OUT/'core-assembly.glb')
 print(json.dumps({'joints':datums,'rear_plane':d['rear_shell_end_mm']},indent=2))

if __name__=='__main__':main()
