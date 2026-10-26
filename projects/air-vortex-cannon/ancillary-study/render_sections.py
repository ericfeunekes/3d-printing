from pathlib import Path
import importlib.util,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/vortex-ancillary-mpl')
import numpy as np,trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ancillary',HERE/'model_ancillary.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
poses=m.load_meshes()
rear=259.8896408;film=rear+2
fig,axs=plt.subplots(1,3,figsize=(15,5),facecolor='white')
def lines(ax,mesh,normal,origin,xaxis,yaxis,color,label,filter_fn=None):
    segs=trimesh.intersections.mesh_plane(mesh,normal,origin)
    first=True
    for seg in segs:
        if filter_fn is not None and not filter_fn(seg):continue
        ax.plot(seg[:,xaxis],seg[:,yaxis],color=color,lw=1.2,label=label if first else None);first=False
shell=trimesh.load_mesh(m.SOURCE/'obj_7_AirZooka03_RingBack.STEP.stl');shell.apply_translation([-128,-128,171])
lines(axs[0],shell,[0,1,0],[0,0,0],2,0,'#477e9e','Rear shell',lambda a:a[:,0].min()>0)
lines(axs[0],poses['obj_10_BackClampRing4.STEP.stl'],[0,1,0],[0,0,0],2,0,'#df9146','Clamp sleeve',lambda a:a[:,0].min()>0)
axs[0].axvline(rear,color='#71828a',ls=':',lw=1);axs[0].set_xlim(rear-12,rear+4);axs[0].set_ylim(115,126)
axs[0].set_title('Rear clamp / shell section');axs[0].set_xlabel('Rearward Z (mm)');axs[0].set_ylabel('Radius (mm)')
axs[0].text(.02,.03,'Nominal lip gap ≈ 0.10 mm radial\nBead withdrawal needs snap deformation',transform=axs[0].transAxes,fontsize=9)
for name,col,label in [('obj_17_PinchRing3.STEP.stl','#477e9e','Male ring'),('obj_5_PinchRingCap3.STEP.stl','#df9146','Pull cap')]:
    temp=poses[name].copy();temp.apply_translation([0,0,-film]);lines(axs[1],temp,[0,1,0],[0,0,0],0,2,col,label)
axs[1].set_xlim(-21,21);axs[1].set_ylim(-6,9);axs[1].set_title('Nominal central snap-clamp section');axs[1].set_xlabel('Horizontal X (mm)');axs[1].set_ylabel('Z relative to film (mm)')
axs[1].axhline(0,color='#71828a',ls=':',lw=1);axs[1].text(.02,.03,'Coaxial reconstruction; snap-contact\nand film compression remain unresolved',transform=axs[1].transAxes,fontsize=9)
rail=trimesh.load_mesh(m.SOURCE/'obj_3_TopClamp3.STEP.stl')
rail.apply_transform(np.array([[0,0,1,-12.5],[0,-1,0,275.85478059],[1,0,0,-326.79839304],[0,0,0,1]]))
lines(axs[2],rail,[1,0,0],[0,0,0],2,1,'#9aabb4','Rail section')
for ang,col in [(0,'#477e9e'),(45,'#b49b44'),(90,'#865397')]:
    sight=m.load_meshes(sight_fold_degrees=ang)['obj_2_Sight2.STEP.stl']
    lines(axs[2],sight,[1,0,0],[0,0,0],2,1,col,f'{ang}° pose')
axs[2].set_xlim(10,85);axs[2].set_ylim(90,158);axs[2].set_title('Sight hinge pose study');axs[2].set_xlabel('Rearward Z (mm)');axs[2].set_ylabel('Upward Y (mm)')
axs[2].text(.02,.03,'Poses only; complete-assembly\ncontinuous sweep assessed separately',transform=axs[2].transAxes,fontsize=9)
for ax in axs:
    ax.grid(alpha=.15);ax.legend(fontsize=8,loc='upper left');ax.set_aspect('equal',adjustable='box')
fig.suptitle('Source-derived ancillary geometry — measured sections and stated assumptions',fontsize=16,color='#183141')
fig.tight_layout();fig.savefig(HERE/'ancillary-sections.png',dpi=170);plt.close(fig)
