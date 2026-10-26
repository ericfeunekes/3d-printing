from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/vortex-mpl')
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent

def draw(ax, mesh, elev, azim, title):
    triangles = mesh.triangles
    collection = Poly3DCollection(triangles, facecolor='#4b94b8', edgecolor='none', alpha=1)
    normals = mesh.face_normals
    light = np.array([.3,-.4,.9]); light /= np.linalg.norm(light)
    shade = .45 + .5 * np.maximum(0, normals @ light)
    base = np.array([.27,.58,.73])
    collection.set_facecolor(np.column_stack([shade[:,None]*base, np.ones(len(shade))]))
    ax.add_collection3d(collection)
    center=mesh.bounds.mean(axis=0); span=max(mesh.extents)*.58
    for fn,c in zip([ax.set_xlim,ax.set_ylim,ax.set_zlim],center): fn(c-span,c+span)
    ax.view_init(elev=elev, azim=azim); ax.set_proj_type('ortho'); ax.set_box_aspect([1,1,1]); ax.set_axis_off()
    ax.set_title(title, fontsize=13, color='#183141')

pin = trimesh.load_mesh(ROOT/'source/egordv/obj_11_AirZookaPin04.STEP.stl')
pin.apply_translation(-pin.bounds.mean(axis=0))
fig=plt.figure(figsize=(14,5),facecolor='white')
for n,(el,az,title) in enumerate([(25,-60,'Stock pin · oblique'),(0,-90,'Side · X / Z'),(90,-90,'Top · X / Y')],1):
    draw(fig.add_subplot(1,3,n,projection='3d'),pin,el,az,title)
fig.suptitle('egordv Air Vortex Cannon — original retention pin',fontsize=18,color='#183141')
fig.text(.5,.045,'Source mesh at original scale · no geometry changes · overall 23.3 × 15.3 × 12.5 mm',ha='center',fontsize=11,color='#516571')
plt.savefig(OUT/'stock-pin.png',dpi=160,bbox_inches='tight'); plt.close(fig)
v=pin.vertices
print('pin centered unique coordinates (rounded .01mm):')
for i in range(3):
    unique,count=np.unique(np.round(v[:,i],2),return_counts=True)
    inds=np.argsort(count)[-22:]
    print('XYZ'[i],sorted(zip(unique[inds].tolist(),count[inds].tolist())))
