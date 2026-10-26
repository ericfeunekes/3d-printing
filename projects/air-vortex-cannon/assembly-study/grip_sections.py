from pathlib import Path
import json,sys
import numpy as np,trimesh
sys.path.insert(0,str(Path(__file__).resolve().parent))
from recover_core import core
OUT=Path(__file__).resolve().parent
meshes,T,joints=core()
rows=[]
for j in joints:
 inv=np.linalg.inv(j['pin_local_to_assembly'])
 receivers={}
 for name,i in [('shell',j['shell_object']),('rail',j['rail_object'])]:
  m=meshes[i].copy();m.apply_transform(inv);receivers[name]=m
 row={'joint':j['id'],'normal_rays':[],'shell_hole_sections':[]}
 for x,y in [(0,0),(0,5),(0,6),(10,0),(-10,0),(10,6)]:
  rr={'local_xy':[x,y]}
  for name,m in receivers.items():
   seg=trimesh.intersections.mesh_plane(m,[0,1,0],[0,y,0])
   a,b=seg[:,0],seg[:,1];dx=b[:,0]-a[:,0]
   use=(abs(dx)>1e-7)&((x-a[:,0])*(x-b[:,0])<=0)
   a,b,dx=a[use],b[use],dx[use]
   z=a[:,2]+(x-a[:,0])/dx*(b[:,2]-a[:,2])
   rr[name]=np.unique(np.round(z[(z>-5)&(z<25)],5)).tolist()
  row['normal_rays'].append(rr)
 for z in [2.25,2.5,2.75]:
  sec=receivers['shell'].section(plane_origin=[0,0,z],plane_normal=[0,0,1])
  if sec:
   for q in sec.discrete:
    lo=q.min(0);hi=q.max(0)
    if max(abs(lo[:2]))<14 and max(abs(hi[:2]))<14:
     row['shell_hole_sections'].append({'normal_z':z,'bounds':[lo.tolist(),hi.tolist()],'vertices':q.tolist()})
 rows.append(row)
 print(j['id'],row['normal_rays'],flush=True)
(OUT/'grip-sections.json').write_text(json.dumps(rows,indent=2)+'\n')
