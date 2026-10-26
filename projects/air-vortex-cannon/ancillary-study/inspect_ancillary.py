from pathlib import Path
import os,json
os.environ.setdefault('MPLCONFIGDIR','/tmp/vortex-ancillary-mpl')
import numpy as np,trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
names=['obj_1_SightPin2.STEP.stl','obj_2_Sight2.STEP.stl','obj_5_PinchRingCap3.STEP.stl','obj_9_RubberBandCarabiner01.STEP.stl','obj_10_BackClampRing4.STEP.stl','obj_17_PinchRing3.STEP.stl']
def draw(ax,m):
    col=Poly3DCollection(m.triangles,edgecolor='none')
    n=m.face_normals;l=np.array([.3,-.4,.85]);l/=np.linalg.norm(l)
    shade=.4+.55*np.maximum(0,n@l);base=np.array([.32,.61,.76])
    col.set_facecolor(np.column_stack([shade[:,None]*base,np.ones(len(shade))]));ax.add_collection3d(col)
    cen=m.bounds.mean(axis=0);span=max(m.extents)*.58
    for fn,c in zip([ax.set_xlim,ax.set_ylim,ax.set_zlim],cen):fn(c-span,c+span)
    ax.view_init(25,-65);ax.set_proj_type('ortho');ax.set_box_aspect([1,1,1]);ax.set_axis_off()
fig=plt.figure(figsize=(14,9))
data={}
for i,name in enumerate(names):
    m=trimesh.load_mesh(ROOT/'source/egordv'/name)
    cen=m.bounds.mean(axis=0)
    data[name]={'bounds':m.bounds.tolist(),'center':cen.tolist(),'volume':m.volume,'watertight':m.is_watertight}
    m.apply_translation(-cen)
    ax=fig.add_subplot(2,3,i+1,projection='3d');draw(ax,m);ax.set_title(name.replace('.STEP.stl',''),fontsize=11)
fig.tight_layout();fig.savefig(HERE/'ancillary-overview.png',dpi=180);plt.close(fig)
(HERE/'source-summary.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(data,indent=2))
