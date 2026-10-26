"""CPU derived before/after views. Consumes owning mesh exports, no redesign."""
from pathlib import Path
import sys,json
import numpy as np,trimesh,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'assembly-study'));sys.path.insert(0,str(ROOT/'presentation'))
from assemble import load_assembly
from render_views import raster,font
m,T,meta=load_assembly();v=json.loads((HERE/'handle-validation.json').read_text());revised=trimesh.load_mesh(HERE/'optional-handle-assembled.stl')
rec=json.loads((ROOT/'design-b/recommended-assembly.json').read_text())
# C lower hardware poses are intentionally exactlyB; new adapter/reinforced
# shell geometry is authored by the independent lower-joint owner.
hardware=[{'mesh':trimesh.load_mesh(ROOT/r['path']),'role':'metal'} for r in rec['components'] if r['joint'].startswith('bottom-') and r['name']!='keyed-adapter-local']
if (ROOT/'design-c/joints/validation.json').exists():
 for row in json.loads((ROOT/'design-c/joints/validation.json').read_text())['shells']:
  m[row['source_id']]=trimesh.load_mesh(ROOT/row['path'])
 hardware=[{'mesh':trimesh.load_mesh(p),'role':'adapter' if 'conforming-keyed-adapter' in p.name else 'metal'} for p in (ROOT/'design-c/joints/assembled').glob('*.stl') if 'continuous-collar-reference' not in p.name]
can=Image.new('RGB',(2400,1500),'white');d=ImageDraw.Draw(can)
d.text((60,35),'Handle choice: retain original; inspect a rearward alternative',font=font(38),fill='#1b3447')
d.text((60,100),'All three mounting receivers remain at their original datums. Native new grip joins the retained source rail.',font=font(24),fill='#5d7281')
for k,(hm,title,hand) in enumerate([(m[4],'SELECTED · original grip',[0,-155,110.4]),(revised,'OPTIONAL · rear30 / down20 mm',[0,-175,140.4])]):
 parts=[{'mesh':m[i],'role':'shell'} for i in [6,8,7]]+[{'mesh':hm,'role':'rail'}]+hardware
 im,proj=raster(parts,1140,1000,direction=(-1,.1,-.18),crop=([-30,-215,30],[30,-85,225]))
 can.paste(im,(30+k*1200,225));d.text((60+k*1200,175),title,font=font(28),fill='#1b3447')
 px=proj(np.array([hand]))[0]+np.array([30+k*1200,225]);d.ellipse((px[0]-6,px[1]-6,px[0]+6,px[1]+6),fill='#ee9626')
 d.text((60+k*1200,1260),f'Assumed grasp {hand} mm',font=font(24),fill='#1b3447')
 d.text((60+k*1200,1310),'Original source4 / three original receivers' if k==0 else 'One fused mesh / native grip STEP region included',font=font(22),fill='#5d7281')
d.text((60,1390),'Geometry only. Hand proxy, printed strength, finger articulation and actual comfort are unverified.',font=font(24),fill='#7b5635')
can.save(HERE/'handle-before-after.png')
fig,ax=plt.subplots(figsize=(13,8))
for mesh,color,lw in [(m[8],'#5287a5',1.2),(m[6],'#5287a5',1.2),(m[7],'#5287a5',1.2),(m[4],'#147a83',2),(revised,'#e18828',2)]:
 sec=mesh.section([1,0,0],[0,0,0])
 for p in sec.discrete:ax.plot(p[:,2],p[:,1],color=color,lw=lw)
for p in hardware:
 sec=p['mesh'].section([1,0,0],[0,0,0])
 if sec:
  for q in sec.discrete:ax.plot(q[:,2],q[:,1],color='#596370',lw=1)
for c,col,label in [([0,-155,110.4],'#147a83','Selected'),([0,-155,140.4],'#ac4358','Same-height +30 (proxy conflicts hardware)'),([0,-175,140.4],'#e18828','Optional +30 / down20')]:
 ax.add_patch(Ellipse((c[2],c[1]),65,90,fc='none',ec=col,ls='--',lw=1.5));ax.scatter(c[2],c[1],c=col,s=25)
ax.plot([],[],color='#147a83',label='Original grip');ax.plot([],[],color='#e18828',label='Optional native grip');ax.plot([],[],color='#ac4358',ls='--',label='Same-height rear30 proxy')
ax.set_xlim(30,220);ax.set_ylim(-225,-85);ax.set_aspect('equal');ax.set_xlabel('Z rearward / mm');ax.set_ylabel('Y up / mm');ax.grid(alpha=.25);ax.legend(loc='lower left');ax.set_title('Actual-mesh section and chosen hand envelopes — not measured hand fit')
fig.text(.12,.015,'Dashed envelopes have fixed radii [32.5,45,32.5] mm. Only intended grip/rail contact is excluded; lower hardware remains an obstacle.',fontsize=10)
fig.savefig(HERE/'handle-clearance-section.png',dpi=180)
