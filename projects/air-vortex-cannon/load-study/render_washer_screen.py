from pathlib import Path
import os,json
os.environ.setdefault('MPLCONFIGDIR','/tmp/vortex-load-mpl')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle

HERE=Path(__file__).resolve().parent
F=json.loads((HERE/'washer-fea-results.json').read_text())
R=json.loads((HERE/'results.json').read_text())
normal=max(d['normal_force_demand_N'] for d in R['local_demands'])
fig,axs=plt.subplots(1,3,figsize=(14,5),facecolor='white')
ax=axs[0]
outer=Circle((0,0),6,facecolor='#e0e8ec',edgecolor='#24485b',lw=1.6)
ax.add_patch(outer)
for x in [-6,4]:
    p=Rectangle((x,-6),2,12,facecolor='#4a879f',alpha=.7)
    p.set_clip_path(outer);ax.add_patch(p)
ax.add_patch(Circle((0,0),3.5,facecolor='#d89a4d',alpha=.8))
ax.add_patch(Circle((0,0),2.15,facecolor='white',edgecolor='#24485b',lw=1.0))
ax.annotate('',xy=(-4,-7),xytext=(4,-7),arrowprops={'arrowstyle':'<->','color':'#24485b'})
ax.text(0,-8,'8 mm unsupported rail opening',ha='center',fontsize=9,color='#24485b')
ax.text(0,7.3,'Nominal OD12 / ID4.3 / t1.6 mm',ha='center',fontsize=10,color='#24485b')
ax.text(0,-11,'Blue: prescribed bottom supports\nAmber: assumed nut-face load',ha='center',fontsize=8,color='#516571')
ax.set_xlim(-9,9);ax.set_ylim(-13,9);ax.set_aspect('equal');ax.axis('off')
ax.set_title('Local FE model',fontsize=13,color='#183141')
colors={'nominal_t1p6':'#40758b','worst_tolerance_t1p3':'#bd7e35'}
labels={'nominal_t1p6':'Nominal 1.6 mm','worst_tolerance_t1p3':'Adverse 1.3 mm dimensions'}
for key in colors:
    cs=[c for c in F['cases'] if c['case']==key]
    x=[c['mesh']['nodes']/1000 for c in cs]
    axs[1].plot(x,[c['max_displacement_mm_per_N']*normal*1000 for c in cs],'o-',color=colors[key],label=labels[key])
    axs[2].plot(x,[c['bulk_region_max_von_mises_MPa_per_N']*normal for c in cs],'o-',color=colors[key],label=labels[key])
axs[1].set_ylabel('Maximum displacement (µm)');axs[1].set_title('Elastic deflection demand',fontsize=13,color='#183141')
axs[2].set_ylabel('Bulk-region max von Mises (MPa)');axs[2].set_title('Stress demand, not material capacity',fontsize=13,color='#183141')
for ax in axs[1:]:
    ax.set_xlabel('Quadratic-mesh nodes (thousands)');ax.grid(alpha=.2);ax.legend(fontsize=8);ax.set_ylim(bottom=0)
fig.suptitle(f'Outer washer FE screen · {normal:.1f} N normal-force example',fontsize=17,color='#183141',y=.97)
fig.text(.5,.05,'Assumed isotropic steel E=200 GPa; rigid bearing patches. No yield or fatigue rating. Sharp boundary peaks remain mesh-sensitive.',ha='center',fontsize=9,color='#72532f')
fig.tight_layout(rect=[0,.10,1,.92]);fig.savefig(HERE/'washer-fea-review.png',dpi=160,facecolor='white')
