"""Section view of all six actual recommended service datums and chosen tools."""
from pathlib import Path
import sys,json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/vortex-mpl')
import numpy as np,trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
ROOT=Path(__file__).resolve().parents[1];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'assembly-study'))
from recover_core import core

def main():
    d=json.loads((ROOT/'design-b/recommended-assembly.json').read_text())
    source,_,_=core()
    fig,ax=plt.subplots(figsize=(12,7),facecolor='white')
    for i in [3,4,6,7,8]:
        lines=trimesh.intersections.mesh_plane(source[i],[1,0,0],[0,0,0])
        ax.add_collection(LineCollection([np.column_stack([x[:,2],x[:,1]]) for x in lines],colors='#7590a0',lw=.7))
    for j in d['joints']:
        M=np.asarray(j['adapter_local_to_assembly']);p=M[:3,3];n=np.asarray(j['outward_axis'])
        inside=p+n*j['head_inner_face_local_z_mm'];outside=p+n*j['nut_outer_face_local_z_mm']
        for start,axis,length,c in [(inside,-n,35,'#c47d32'),(outside,n,30,'#6d8ab2')]:
            end=start+axis*length
            ax.annotate('',xy=(end[2],end[1]),xytext=(start[2],start[1]),arrowprops={'arrowstyle':'-|>','color':c,'lw':1.5})
            ax.plot(start[2],start[1],'o',color=c,ms=4)
        ax.annotate(j['id'],xy=(outside[2],outside[1]),xytext=(outside[2]-17,outside[1]+(36 if j['id'].startswith('top') else -37)),fontsize=8,color='#344f60',arrowprops={'arrowstyle':'-','color':'#aab7c0','lw':.6})
    # One representative complete interior entry: unloaded membrane must be
    # out of this corridor. Other paths are numerically checked separately.
    j=d['joints'][0];M=np.array(j['adapter_local_to_assembly']);n=np.array(j['outward_axis']);p=M[:3,3]+n*j['head_inner_face_local_z_mm']
    ax.annotate('',xy=(p[2],p[1]-15),xytext=(300,p[1]-15),arrowprops={'arrowstyle':'-|>','color':'#a883ad','ls':'--','lw':1.2})
    ax.text(232,p[1]-7,'Rear entry corridor',color='#86638f',fontsize=9)
    ax.axvline(261.8896408,color='#a883ad',ls=':',lw=1)
    ax.text(267,7,'Membrane unloaded\nand removed/held clear\nfor interior service',fontsize=9,color='#86638f')
    ax.set_xlim(-10,325);ax.set_ylim(-230,210);ax.set_aspect('equal');ax.grid(alpha=.13)
    ax.set(xlabel='Canonical Z rearward (mm)',ylabel='Canonical Y up (mm)')
    ax.set_title('All six service sites — actual shoulder-bolt datums',fontsize=14)
    fig.text(.5,.10,'Amber: chosen R2×35mm interior hex-key shaft envelope. Blue: chosen R6×30mm exterior socket envelope.',ha='center',fontsize=10,color='#425f71')
    fig.text(.5,.06,'Arrows show tool axes, not certified human access. Source section is shown; modified-shell clearances are reported numerically.',ha='center',fontsize=9,color='#725c43')
    fig.tight_layout(rect=[0,.14,1,1]);fig.savefig(HERE/'service-envelope.png',dpi=170);plt.close(fig)

if __name__=='__main__':main()
