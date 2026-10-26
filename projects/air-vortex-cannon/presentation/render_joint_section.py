from pathlib import Path
import sys,json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/vortex-asm-mpl')
import numpy as np,trimesh
from shapely.geometry import Polygon,box
from shapely.geometry.polygon import orient
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(HERE))
from scene_data import load_configuration,COLORS

def path_polygon(poly):
    p=orient(poly,sign=1);verts=[];codes=[]
    for ring in [p.exterior,*p.interiors]:
        xy=list(ring.coords);verts.extend(xy);codes.extend([MPath.MOVETO]+[MPath.LINETO]*(len(xy)-2)+[MPath.CLOSEPOLY])
    return MPath(verts,codes)

def main():
    parts,meta=load_configuration('recommended',final_shells=True)
    record=json.loads((ROOT/'design-b/recommended-assembly.json').read_text());j=record['joints'][0]
    inv=np.linalg.inv(j['adapter_local_to_assembly'])
    chosen=[p for p in parts if p['key'] in ['reinforced-6','stock-3'] or p['key'].startswith('top-front--')]
    fig,ax=plt.subplots(figsize=(14,10),facecolor='white')
    for p in chosen:
        mesh=p['mesh'].copy();mesh.apply_transform(inv)
        sec=mesh.section(plane_normal=[0,1,0],plane_origin=[0,0,0])
        if sec is None:continue
        material=Polygon()
        for loop in sec.discrete:
            shape=Polygon(loop[:,[0,2]])
            if not shape.is_valid:shape=shape.buffer(0)
            material=material.symmetric_difference(shape)
        material=material.intersection(box(-24,-12,24,26))
        polygons=list(material.geoms) if material.geom_type=='MultiPolygon' else [material]
        color=np.asarray(COLORS[p['role']][:3])/255
        for poly in polygons:
            if not poly.is_empty and poly.area>1e-8:ax.add_patch(PathPatch(path_polygon(poly),facecolor=color,edgecolor='#304c60',lw=.65))
    gap=j['nominal_capture_gap_mm'];g=j['reinforced_grip_mm'];w=j['outer_washer_local_z_mm']
    ax.annotate('',xy=(17.5,g),xytext=(17.5,w),arrowprops={'arrowstyle':'<->','color':'#a56d28','lw':1.4})
    ax.plot([15.5,18.4],[g,g],color='#a56d28',lw=.8);ax.plot([7,18.4],[w,w],color='#a56d28',lw=.8)
    ax.text(18.5,13.7,f'{gap:.2f} mm\ndatum-plane separation',fontsize=10,color='#805a27',va='center')
    style={'arrowstyle':'-','color':'#526b7a','lw':1}
    ax.annotate('Self-locking nut reference',xy=(2.5,18.2),xytext=(-22,23.4),fontsize=11,arrowprops=style)
    ax.annotate('Outer washer meets metal shoulder',xy=(4.6,15),xytext=(5,23.4),fontsize=11,arrowprops=style)
    ax.annotate('Original exterior rail',xy=(-14,8),xytext=(-22,15),fontsize=11,arrowprops=style)
    ax.annotate('Continuous local shell reinforcement',xy=(-13,1),xytext=(-22,5),fontsize=11,arrowprops=style)
    ax.annotate('Keyed printed adapter',xy=(-12,-2),xytext=(-22,-5.5),fontsize=11,arrowprops=style)
    ax.annotate('Shoulder bolt + wide inner washer',xy=(3,-6.5),xytext=(-22,-10.5),fontsize=11,arrowprops=style)
    ax.text(25,-8,'INSIDE',fontsize=10,color='#657d8b',rotation=90,ha='center')
    ax.text(25,20,'OUTSIDE',fontsize=10,color='#657d8b',rotation=90,ha='center')
    ax.set_xlim(-24,29);ax.set_ylim(-12,26);ax.set_aspect('equal');ax.grid(alpha=.18)
    ax.set_xlabel('Axial tangent at the joint (mm)');ax.set_ylabel('Outward joint-normal coordinate (mm)')
    ax.set_title('Proposed top-front joint · centre section from the delivered meshes',fontsize=17,pad=16)
    fig.text(.5,.04,'Nominal geometric capture; no clamp-friction credit. Hardware threads are envelopes. Actual printed fit, locking and strength require physical evidence.',ha='center',fontsize=10,color='#725335')
    fig.text(.5,.015,'Datum-plane separation is not free play: the nominal OD12 washer-footprint study gives about 0.74–0.76 mm to first contact across six sites.',ha='center',fontsize=9,color='#725335')
    fig.tight_layout(rect=[0,.08,1,1]);fig.savefig(HERE/'proposed-joint-section.png',dpi=160);plt.close(fig)
    print('Rendered actual joint cross-section with datum-plane / first-contact distinction.')

if __name__=='__main__':main()
