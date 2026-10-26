"""Actual exported front-lower C mesh sections; no redrawn joint geometry."""
from pathlib import Path
import sys,json
import numpy as np,trimesh,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def main():
 rec=json.loads((HERE/'lower-assembly.json').read_text());j=rec['joints'][0];Minv=np.linalg.inv(np.array(j['adapter_local_to_assembly']))
 parts=[('Continuous shell + lower collar',HERE/'fit-coupon/c-conical-collar-shell-coupon-assembled.stl','#3872a0'),('Original handle receiver',HERE/'fit-coupon/original-handle-receiver-coupon-assembled.stl','#279da1')]
 for c in rec['components']:
  if c['joint']!='bottom-front':continue
  parts.append(('Curved inner keyed adapter' if c['manufactured_here'] else c['name'],ROOT/c['path'],'#db9729' if c['manufactured_here'] else '#727b83'))
 fig,axes=plt.subplots(1,2,figsize=(12,7),width_ratios=[1.5,1])
 for label,path,color in parts:
  mesh=trimesh.load_mesh(path);mesh.apply_transform(Minv)
  sec=mesh.section(plane_origin=[0,0,0],plane_normal=[1,0,0])
  if sec is None:continue
  for k,line in enumerate(sec.discrete):
   for ax in axes:ax.plot(line[:,1],line[:,2],color=color,lw=1.8,label=label if k==0 else None)
 for ax in axes:ax.set_aspect('equal');ax.grid(alpha=.2);ax.set_xlabel('Circumferential tangent / mm');ax.set_ylabel('Outward normal / mm')
 axes[0].set_xlim(-16,16);axes[0].set_ylim(-14,22);axes[0].set_title('Actual mesh section at axial tangent X = 0')
 axes[1].set_xlim(-12,12);axes[1].set_ylim(-8.5,2);axes[1].set_title('Conforming inner face and flat metal washer seat')
 axes[1].annotate('Native design gap 0.05 mm\nSTL first contact occurs earlier',xy=(9,-2.95),xytext=(-11,1.15),arrowprops={'arrowstyle':'-','color':'#555'},fontsize=9)
 axes[0].legend(loc='upper left',bbox_to_anchor=(0,-.13),fontsize=8,ncol=2)
 fig.suptitle('Revision C · front lower attachment · ideal CAD candidate',fontsize=15)
 fig.text(.51,.03,'No outer printed pad. Original slot retained. Metal references DO NOT PRINT.\nGeometry and contact fit are untested physically; this is not a strength or safety rating.',ha='center',fontsize=10)
 fig.tight_layout(rect=[0,.11,1,.94]);fig.savefig(HERE/'front-lower-actual-section.png',dpi=190)

if __name__=='__main__':main()
