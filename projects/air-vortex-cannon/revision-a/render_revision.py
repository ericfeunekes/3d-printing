"""Views and a source-mesh contact check derived from the delivered STL files."""
from pathlib import Path
import os, json
os.environ.setdefault('MPLCONFIGDIR','/tmp/vortex-mpl')
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
P=json.loads((HERE/'validation.json').read_text())
S=P['spec']
pin=trimesh.load_mesh(ROOT/'source/egordv/obj_11_AirZookaPin04.STEP.stl')
pin.apply_translation([-pin.bounds.mean(axis=0)[0],-pin.bounds.mean(axis=0)[1],-pin.bounds[0,2]])

def installed(mesh):
    out=mesh.copy()
    # Proper rotation from print coordinates to stock pin coordinates.
    out.apply_transform(np.array([[1,0,0,-S['cap_width']/2],
                                  [0,0,-1,S['body_depth']/2],
                                  [0,1,0,S['stock_u_center_z']-S['foot_radius']],
                                  [0,0,0,1]]))
    return out

def draw(ax, objects, elev=18,azim=-65):
    bounds=[]
    for mesh,color in objects:
        base=np.array(matplotlib.colors.to_rgb(color))
        normals=mesh.face_normals
        light=np.array([.25,-.35,.9]);light/=np.linalg.norm(light)
        shade=.55+.4*np.maximum(0,normals@light)
        faces=Poly3DCollection(mesh.triangles,edgecolor='none')
        faces.set_facecolor(np.column_stack([shade[:,None]*base,np.ones(len(shade))]))
        ax.add_collection3d(faces);bounds.extend(mesh.bounds)
    bounds=np.array(bounds);lo=bounds.min(axis=0);hi=bounds.max(axis=0)
    center=(lo+hi)/2; span=max(hi-lo)*.58
    for setter,c in zip([ax.set_xlim,ax.set_ylim,ax.set_zlim],center):setter(c-span,c+span)
    ax.view_init(elev=elev,azim=azim);ax.set_proj_type('ortho');ax.set_box_aspect([1,1,1]);ax.set_axis_off()

keeper=installed(trimesh.load_mesh(HERE/'parts/keeper-nominal.stl'))
exploded=keeper.copy();exploded.apply_translation([0,0,10])
fig=plt.figure(figsize=(14,7),facecolor='white')
ax=fig.add_subplot(1,3,1,projection='3d')
draw(ax,[(pin,'#588caa'),(keeper,'#e99a43')]);ax.set_title('Proposed seating in stock clip',fontsize=13,pad=5,color='#183141')
ax=fig.add_subplot(1,3,2,projection='3d')
draw(ax,[(pin,'#588caa'),(exploded,'#e99a43')]);ax.set_title('Removal direction',fontsize=13,pad=5,color='#183141')
ax=fig.add_subplot(1,3,3)
mesh=trimesh.load_mesh(HERE/'parts/keeper-nominal.stl')
for tri in mesh.triangles:
    ax.fill(tri[:,0],tri[:,1],facecolor='#e99a43',edgecolor='none')
# White overlay of the actual cylindrical eye opening for clean projection.
eye_y=S['eye_hole_center_z']-(S['stock_u_center_z']-S['foot_radius'])
ax.add_patch(plt.Circle((S['cap_width']/2,eye_y),S['eye_hole_diameter']/2,color='white'))
ax.annotate('Pull / removal eye',xy=(6,eye_y),xytext=(18,15),fontsize=10,color='#183141',arrowprops={'arrowstyle':'-','color':'#78909c'})
ax.annotate('Seating stop',xy=(12,11.3),xytext=(18,10),fontsize=10,color='#183141',arrowprops={'arrowstyle':'-','color':'#78909c'})
ax.annotate('Tapered fit surface',xy=(10.4,8.5),xytext=(18,5),fontsize=10,color='#183141',arrowprops={'arrowstyle':'-','color':'#78909c'})
ax.set_xlim(-3,39);ax.set_ylim(-2,23);ax.set_aspect('equal');ax.set_axis_off()
ax.set_title('New keeper · print flat',fontsize=13,color='#183141')
fig.suptitle('Air Vortex Cannon — Revision A prototype',fontsize=21,color='#183141',y=.93)
fig.text(.5,.84,'Blue: unchanged egordv clip   ·   Amber: new removable keeper',ha='center',fontsize=12,color='#516571')
fig.text(.5,.14,'Intended to limit the clip arms closing inward after assembly.',ha='center',fontsize=13,color='#183141')
fig.text(.5,.095,'UNPRINTED: seating, self-retention and installed clearance require a fit trial.',ha='center',fontsize=11,color='#72532f')
fig.text(.5,.055,'No increased elastic load or airflow-performance claim. Base design: egordv · CC BY-NC-SA 4.0.',ha='center',fontsize=10,color='#516571')
fig.subplots_adjust(top=.8,bottom=.2,left=.01,right=.99,wspace=.02)
fig.savefig(HERE/'revision-a-review.png',dpi=170,facecolor='white');plt.close(fig)

# Direct source-mesh check. This verifies only this pin/keeper placement; the
# enclosing rail/shell, elastic and diaphragm were not assembled digitally.
contact=[]
for v in P['variants']:
    mesh=installed(trimesh.load_mesh(HERE/f"parts/keeper-{v['name']}.stl"))
    # Densely sample the delivered mesh's center-plane boundary too. Vertices
    # and triangle centroids alone can miss a short tapered contact region.
    sections=trimesh.intersections.mesh_plane(mesh,[0,1,0],[0,0,0])
    weights=np.linspace(0,1,101)
    dense=np.concatenate([a[None,:]*(1-weights[:,None])+b[None,:]*weights[:,None] for a,b in sections])
    points=np.vstack([mesh.vertices,mesh.triangles_center,dense])
    d=trimesh.proximity.signed_distance(pin,points)
    penetration=float(max(0,d.max()))
    contact.append({'variant':v['name'],'sampled_points':len(points),
                    'max_sampled_penetration_mm':penetration,
                    'points_more_than_0_02mm_inside_stock_pin':int((d>.02).sum()),
                    'scope':'stock pin only, seated assumption; not complete assembly'})
P['source_mesh_contact_check']=contact
P['view']='revision-a-review.png, derived from delivered meshes'
(HERE/'validation.json').write_text(json.dumps(P,indent=2)+'\n')
print(json.dumps(contact,indent=2))
