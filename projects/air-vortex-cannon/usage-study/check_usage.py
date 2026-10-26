"""Sampled mechanism/clearance study of recovered stock CAD assembly.

Millimetres. Assumed motion is not measured film/elastic/hand behaviour.
No source, owning CAD, or other agent's outputs are changed by this script.
"""
from pathlib import Path
import sys, json, math, os
os.environ.setdefault('MPLCONFIGDIR','/tmp/vortex-mpl')
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'assembly-study'))
sys.path.insert(0,str(ROOT/'ancillary-study'))
from recover_core import core
from model_ancillary import load_meshes, membrane_mesh, band_graph, make_transforms

def deterministic_points(mesh,max_points=900):
    v=np.asarray(mesh.vertices); f=np.asarray(mesh.triangles_center)
    nv=max_points//2; nf=max_points-nv
    pts=np.vstack([v[np.linspace(0,len(v)-1,min(nv,len(v))).astype(int)],
                   f[np.linspace(0,len(f)-1,min(nf,len(f))).astype(int)]])
    # Keep each axis extremum independently of the face indexing/sample limit.
    ext=np.unique(np.r_[v.argmin(axis=0),v.argmax(axis=0)])
    return np.vstack([pts,v[ext]])

def signed(mesh,points,chunk=384):
    return np.concatenate([trimesh.proximity.signed_distance(mesh,p) for p in np.array_split(points,max(1,math.ceil(len(points)/chunk)))])

def radial_bounds(mesh):
    if 'usage_radial_bounds' in mesh.metadata:return mesh.metadata['usage_radial_bounds']
    tri=mesh.triangles[:,:,:2]
    edge_min=[]
    for i in range(3):
        a=tri[:,i];d=tri[:,(i+1)%3]-a
        den=np.einsum('ij,ij->i',d,d)
        t=np.divide(-np.einsum('ij,ij->i',a,d),den,out=np.zeros(len(d)),where=den>1e-20)
        q=a+np.clip(t,0,1)[:,None]*d
        edge_min.append(np.linalg.norm(q,axis=1))
    nearest=np.min(edge_min,axis=0)
    def cross(a,b):return a[:,0]*b[:,1]-a[:,1]*b[:,0]
    area=cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    signs=np.array([cross(tri[:,(i+1)%3]-tri[:,i],-tri[:,i]) for i in range(3)])
    contains_origin=(np.abs(area)>1e-10)&((np.all(signs>=-1e-10,axis=0))|(np.all(signs<=1e-10,axis=0)))
    nearest[contains_origin]=0.
    bounds=(float(nearest.min()),float(np.linalg.norm(tri,axis=2).max()))
    mesh.metadata['usage_face_radial_min']=nearest
    mesh.metadata['usage_face_radial_max']=np.linalg.norm(tri,axis=2).max(axis=1)
    mesh.metadata['usage_face_z_min']=mesh.triangles[:,:,2].min(axis=1)
    mesh.metadata['usage_face_z_max']=mesh.triangles[:,:,2].max(axis=1)
    mesh.metadata['usage_radial_bounds']=bounds
    return bounds

def local_slab_bounds(mesh,points):
    """Conservative outside-distance bound from actual faces in axial windows.

    The window extends at least10mm beyond queryZ. Faces excluded from the
    window cannot be nearer than that axial distance. Included faces bound
    the complete cross-section at queryZ. Local radial lower bounds are used
    only when the source's complete closed surface omits the central axis.
    """
    glo,_=radial_bounds(mesh)
    rmin=mesh.metadata['usage_face_radial_min'];rmax=mesh.metadata['usage_face_radial_max']
    zmin=mesh.metadata['usage_face_z_min'];zmax=mesh.metadata['usage_face_z_max']
    tri=mesh.triangles
    group=np.floor(points[:,2]/10).astype(int)
    out=np.zeros(len(points))
    cache=mesh.metadata.setdefault('usage_slab_cache',{})
    for g in np.unique(group):
        idx=np.where(group==g)[0];p=points[idx]
        low=g*10-10;high=(g+1)*10+10
        excluded_z=np.minimum(p[:,2]-low,high-p[:,2])
        if int(g) not in cache:
            hit=(zmin<=high)&(zmax>=low)
            if np.any(hit):
                t=tri[hit];cache[int(g)]=(t.min(axis=(0,1)),t.max(axis=(0,1)),float(rmin[hit].min()),float(rmax[hit].max()))
            else:cache[int(g)]=None
        row=cache[int(g)]
        if row is None:out[idx]=excluded_z;continue
        lo,hi,a,b=row
        box=np.linalg.norm(np.maximum(np.maximum(lo-p,p-hi),0),axis=1)
        r=np.linalg.norm(p[:,:2],axis=1)
        inner=np.maximum(a-r,0) if glo>1e-5 else np.zeros(len(p))
        outer=np.maximum(r-b,0)
        out[idx]=np.minimum(np.maximum(box,np.maximum(inner,outer)),excluded_z)
    return out

def sampled_clearance(points,obstacles,margin=0.):
    rows=[]
    for name,m in obstacles.items():
        # Rigorous mesh-derived AABB/radial lower bounds avoid expensive
        # nearest-triangle work for deep interior points far from a hollow
        # shell. A positive lower bound proves these sample points outside;
        # exact signed distances resolve only the ambiguous near samples.
        lo,hi=m.bounds
        box_delta=np.maximum(np.maximum(lo-points,points-hi),0)
        box_bound=np.linalg.norm(box_delta,axis=1)
        rlo,rhi=radial_bounds(m);r=np.linalg.norm(points[:,:2],axis=1)
        radial_bound=np.maximum(np.maximum(rlo-r,r-rhi),0)
        bound=np.maximum(box_bound,radial_bound)
        if np.any(bound<=margin+.020001):
            bound=np.maximum(bound,local_slab_bounds(m,points))
        safe=bound>margin+.020001
        d=-bound
        if np.any(~safe):d[~safe]=signed(m,points[~safe])
        penetration=float(max(0,d.max()+margin))
        # Positive when outside, negative when inside or violating tube radius.
        min_clearance=float((-d-margin).min())
        rows.append({'obstacle':str(name),'sample_count':len(points),
          'minimum_sampled_clearance_mm':min_clearance,
          'maximum_sampled_penetration_mm':penetration,
          'points_over_0_02mm_penetration':int((d+margin>.02).sum()),
          'mesh_bound_only_samples':int(safe.sum()),'exact_triangle_distance_samples':int((~safe).sum()),
          'distance_reporting':'Outside lower bounds where positive; exact triangle signed distances only for ambiguous near samples. Reported clearance is conservative, not exact minimum.'})
    return rows

def line_points(a,b,trim_start=0.,trim_end=0.,spacing=4.):
    a=np.array(a,dtype=float);b=np.array(b,dtype=float)
    length=float(np.linalg.norm(b-a));direction=(b-a)/length
    a=a+trim_start*direction;b=b-trim_end*direction
    if np.linalg.norm(b-a)<.01:return np.array([(a+b)/2])
    return a[None,:]+np.linspace(0,1,max(2,math.ceil(np.linalg.norm(b-a)/spacing)+1))[:,None]*(b-a)[None,:]

def cylinder_points(origin,axis,radius,length,angular=24,axial=13):
    axis=np.array(axis,dtype=float);axis/=np.linalg.norm(axis)
    tangent=np.cross(axis,[1,0,0])
    if np.linalg.norm(tangent)<.1:tangent=np.cross(axis,[0,1,0])
    tangent/=np.linalg.norm(tangent);cross=np.cross(axis,tangent)
    points=[]
    for z in np.linspace(0,length,axial):
        for r in [0.,radius*.5,radius]:
            for a in np.linspace(0,2*np.pi,angular,endpoint=False):
                points.append(np.array(origin)+axis*z+r*(tangent*np.cos(a)+cross*np.sin(a)))
    return np.asarray(points)

def make_fixed():
    meshes,_,datums=core()
    ancillary=load_meshes()
    # Clip meshes remain source reference but moving pieces only need shell,
    # rails and rear clamp. Central snap contacts are separately labelled.
    structure={f'stock-{i}':meshes[i] for i in [3,4,6,7,8]}
    structure['rear-clamp']=ancillary['obj_10_BackClampRing4.STEP.stl']
    return structure,meshes,datums

def pull_study(structure):
    result=[]
    for stroke in [0.,10.,20.,30.,40.,50.,60.]:
        anc=load_meshes(stroke=stroke)
        moving={name:m for name,m in anc.items() if name.startswith(('obj_5_','obj_17_','obj_9_'))}
        row={'stroke_mm':stroke,'rigid_components':{},'membrane':{},'bands':{}}
        for name,m in moving.items():
            row['rigid_components'][name]=sampled_clearance(deterministic_points(m,520),structure)
        # Exclude intended centre clamp and perimeter clamping contacts. No
        # film material, wrinkling, thickness or stress model is implied.
        film=membrane_mesh(stroke=stroke,radial_steps=16,angular_steps=48)
        p=film.vertices;rad=np.linalg.norm(p[:,:2],axis=1)
        p=p[(rad>22)&(rad<114.5)]
        row['membrane']['intentional_contacts_excluded']='R<=22mm centre clamp; R>=114.5mm perimeter clamp'
        row['membrane']['checks']=sampled_clearance(p,structure)
        graph=band_graph(stroke=stroke)
        for idx,(a,b) in enumerate(graph['edges']):
            # Tie knots/loops and centre through-ring routing are not recovered;
            # trim endpoints rather than claiming no contact at attachments.
            pts=line_points(graph['nodes'][a],graph['nodes'][b],8.,20. if b=='membrane_centre' else 8.)
            row['bands'][f'{idx}-{a}-to-{b}']=sampled_clearance(pts,structure,margin=1.5)
        result.append(row)
        print('pull',stroke,'done',flush=True)
    return result

def sight_study(structure):
    result=[]
    obs={k:v for k,v in structure.items() if k in ['stock-3','stock-6']}
    for angle in range(0,96,5):
        m=load_meshes(sight_fold_degrees=angle)['obj_2_Sight2.STEP.stl']
        pts=deterministic_points(m,1800)
        # Hinge ear and its direct mating axle are intentionally contacting.
        hinge=np.array([0.,109.214125,26.77423])
        pts=pts[np.linalg.norm(pts[:,1:]-hinge[1:],axis=1)>4.0]
        checks=sampled_clearance(pts,obs)
        result.append({'fold_angle_deg':angle,'checks':checks,
          'excluded_contact':'Points within4mm of hingeaxis; axle/ear contact is not a rigid clearance claim.'})
        print('sight',angle,'done',flush=True)
    return result

def original_service_study(structure,datums):
    results=[]
    for j in datums:
        p=np.array(j['inner_surface_center_mm']);n=np.array(j['outward_axis'])
        # The source pin tips are10.5mm outward from inner shell contact
        # (source pin base local0; innercontactlocal2; tiplocal12.5).
        # These are common illustrative tool envelopes, not a stocktool need.
        for side,radius,length,offset in [('inside',2.0,35.,-4.),('outside',6.0,30.,11.)]:
            axis=-n if side=='inside' else n
            pts=cylinder_points(p+n*offset,axis,radius,length)
            checks=sampled_clearance(pts,structure)
            results.append({'joint':j['id'],'side':side,'tool_radius_mm':radius,
              'tool_length_mm':length,'start_normal_offset_mm':offset,'checks':checks,
              'scope':'Stock reference geometry; source pin is excluded. Recommended exact head/nut datum must replace these illustrative offsets.'})
        print('service',j['id'],'done',flush=True)
    return results

def render_usage(structure):
    fig,ax=plt.subplots(figsize=(12,7),facecolor='white')
    for name,m in structure.items():
        try:seg=trimesh.intersections.mesh_plane(m,[1,0,0],[0,0,0])
        except Exception:continue
        lines=[np.column_stack([s[:,2],s[:,1]]) for s in seg]
        ax.add_collection(LineCollection(lines,colors='#486f87',linewidths=.6,alpha=.8))
    for stroke,color in [(0,'#d58a33'),(30,'#69a77a'),(60,'#b75545')]:
        z0=261.8896408
        for sign in [-1,1]:
            ax.plot([z0,z0+stroke],[sign*116.8533,sign*20],color=color,lw=2,label=f'{stroke}mm assumed pull' if sign==1 else None)
        ax.plot([z0+stroke,z0+stroke+47.84],[0,0],color=color,lw=3)
    # Explicitly illustrative hand clearance proxies, never ergonomic proof.
    from matplotlib.patches import Ellipse
    ax.add_patch(Ellipse((110.4,-155),65,90,fill=False,edgecolor='#926eab',lw=1.5,ls='--'))
    ax.text(60,-208,'Grip-hand proxy\n65mm axial ×90mm vertical',fontsize=9,color='#73528a')
    ax.add_patch(Ellipse((261.8896408+60+60,10),80,75,fill=False,edgecolor='#926eab',lw=1.5,ls='--'))
    ax.text(345,65,'Pull-hand proxy\nassumed shape/position',fontsize=9,color='#73528a')
    ax.set(xlim=(-15,445),ylim=(-220,165),xlabel='Canonical Z rearward (mm)',ylabel='Canonical Y up (mm)')
    ax.set_aspect('equal');ax.grid(alpha=.15);ax.legend(loc='upper left')
    ax.set_title('Full usage envelope — recovered source section + assumed0–60mm pull',fontsize=14)
    fig.text(.5,.04,'Film is a zero-thickness cone study. No film stress, band force, hand fit or ring-performance proof is implied.',ha='center',fontsize=10,color='#735b42')
    fig.tight_layout(rect=[0,.07,1,1]);fig.savefig(HERE/'usage-envelope.png',dpi=170);plt.close(fig)

def main():
    HERE.mkdir(exist_ok=True)
    structure,meshes,datums=make_fixed()
    render_usage(structure)
    pull=pull_study(structure)
    sight=sight_study(structure)
    service=original_service_study(structure,datums)
    d={'units':'mm','scope':'Conditional sampled stock mechanism/usage clearance; not physical proof',
      'assumptions':{'pull_stroke_mm':[0,10,20,30,40,50,60],
       'band_radius_mm':1.5,'band_junction':'display midpoint, not force equilibrium',
       'film':'zero-thickness conical annular surface; known edge contacts excluded',
       'generic_tools':'insideR2x35mm cylinder; outsideR6x30mm cylinder at source-derived reference offsets',
       'hands':'illustrative ellipses/volumes, not anthropometric population coverage'},
      'method':'Deterministic vertex/face-centroid samples. Positive mesh-derived AABB/radial distance lower bounds establish outside points; ambiguous samples use exact triangle signed distances. >.02mm sampled penetration counted. Reported positive clearance is a conservative bound. Samples do not prove continuous collision freedom.',
      'pull_study':pull,'sight_study':sight,'source_service_envelopes':service,
      'not_proved':['Actual film slack/wrinkling/contact/deformation','Band stiffness/rest lengths/force','Snap-fit deformation','Strength, durability, physical print fit','Recommended hardware service until exact final assembly supplied']}
    (HERE/'usage-results.json').write_text(json.dumps(d,indent=2)+'\n')
    print('Wrote full usage study',flush=True)

if __name__=='__main__':main()
