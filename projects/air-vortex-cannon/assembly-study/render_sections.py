from pathlib import Path
import os,sys
os.environ.setdefault('MPLCONFIGDIR','/tmp/vortex-asm-mpl')
import numpy as np,trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from assemble import load_assembly
meshes,T,meta=load_assembly()
fig,axs=plt.subplots(1,2,figsize=(16,9),gridspec_kw={'width_ratios':[2.2,1]})
colors={6:'#24598c',8:'#478db7',7:'#70b2d0',3:'#13959b',4:'#13959b'}
for i,m in meshes.items():
    lines=trimesh.intersections.mesh_plane(m,[1,0,0],[0,0,0])
    for ax in axs:
        for seg in lines:
            ax.plot(seg[:,2],seg[:,1],color=colors.get(i,'#665543'),lw=.7 if i in [6,7,8] else 1)
    if i in [6,8,7]:
        centre=m.bounds.mean(0);axs[0].text(centre[2],-5,{6:'Front',8:'Middle',7:'Rear'}[i],ha='center',fontsize=11,color=colors[i])
rear=meta['rear_shell_plane_mm']
axs[0].plot([rear+2,rear+2],[-116.8533,116.8533],color='#b06ca0',lw=1,ls='--',label='Film rest plane (study)')
for sign in [1,-1]:
    axs[0].plot([rear+2,rear+62],[sign*116.8533,sign*20],color='#b06ca0',lw=1,ls=':',label='60 mm assumed pull' if sign==1 else None)
axs[0].scatter([110.4],[-155],s=30,color='#c45645',label='Assumed hand contact')
axs[0].set_xlim(-10,rear+75);axs[0].set_ylim(-205,155)
axs[0].set_title('Full stock assembly · centre-plane section',fontsize=14)
axs[1].set_xlim(45,80);axs[1].set_ylim(86,117)
axs[1].set_title('Top-front joint detail',fontsize=14)
for ax in axs:
    ax.set_aspect('equal');ax.set_xlabel('Z · rearward axis (mm)');ax.set_ylabel('Y · vertical (mm)');ax.grid(alpha=.25)
axs[0].legend(loc='lower right',fontsize=9)
fig.suptitle('Recovered 17-part stock geometry and assumed usage envelope',fontsize=18,color='#173246')
fig.text(.5,.045,'Mating geometry + original assembly video establish nominal poses. Film motion and hand contact are assumptions; no physical strength or ring-performance proof.',ha='center',fontsize=10,color='#516571')
fig.tight_layout(rect=[0,.07,1,.94]);fig.savefig(HERE/'full-stock-sections.png',dpi=160);plt.close(fig)
print('Savedfull17partsectionandjointdetail.')
