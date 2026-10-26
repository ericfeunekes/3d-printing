from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/vortex-asm-mpl')
import numpy as np,trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(__file__).resolve().parent
files={int(p.name.split('_')[1]):p for p in (ROOT/'source/egordv').glob('*.stl')}
fig,axs=plt.subplots(2,3,figsize=(17,10))
for ax,i in zip(axs[0],[6,8,7]):
 m=trimesh.load_mesh(files[i]);sec=trimesh.intersections.mesh_plane(m,[0,1,0],[0,128,0])
 for s in sec:
  if s[:,0].mean()>128:ax.plot(s[:,2],s[:,0]-128,color='navy',lw=.6)
 ax.set_aspect('equal');ax.grid();ax.set_title(files[i].name);ax.set_xlabel('source Z');ax.set_ylabel('radius')
for ax,i in zip(axs[1],[3,4,10]):
 m=trimesh.load_mesh(files[i]);n=m.face_normals
 # projected triangles, using surface layer shading.
 v=m.vertices.copy();v[:,:2]-=m.bounds.mean(axis=0)[:2]
 tri=v[m.faces]
 from matplotlib.collections import PolyCollection
 ax.add_collection(PolyCollection(tri[:,:,:2],facecolors=np.where((n[:,2]>.8)[:,None],np.array([.3,.5,.7,1]),np.array([.8,.85,.9,.5])),edgecolors='none'))
 ax.autoscale();ax.set_aspect('equal');ax.grid();ax.set_title(files[i].name)
fig.tight_layout();fig.savefig(OUT/'source-sections.png',dpi=140)

# Large planar faces are useful datums and repeated slot faces.
for i in [3,4,6,8,7]:
 m=trimesh.load_mesh(files[i]);n=m.face_normals;c=m.triangles_center;a=m.area_faces
 print('\nPART',i)
 for axis in range(3):
  use=np.abs(n[:,axis])>.99999
  bins={}
  for center,area in zip(c[use,axis],a[use]):
   key=round(float(center),3);bins[key]=bins.get(key,0)+area
  print('AXIS',axis, sorted([(k,round(v,2)) for k,v in bins.items() if v>5],key=lambda q:-q[1])[:35])
