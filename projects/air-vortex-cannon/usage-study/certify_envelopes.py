"""Conservative continuous-envelope clearance certificates under stated CAD inputs.

Distance-to-a-closed-obstacle is 1-Lipschitz. A surface grid with a known
cover radius c and minimum certified sample distance d has entire-surface
clearance >=d-c. Entry translations add half the maximum translation step.
This says nothing about real tools/hands, deflection or manufacturing error.
"""
from pathlib import Path
import sys,json,math,hashlib
import numpy as np,trimesh
ROOT=Path(__file__).resolve().parents[1];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(ROOT/'ancillary-study')]
from check_usage import make_fixed,sampled_clearance,radial_bounds
from check_recommended import load_recommended
from model_ancillary import load_meshes,band_graph

def cylinder_boundary(origin,axis,radius,length,angular,axial_step,radial_step):
    axis=np.asarray(axis,dtype=float);axis/=np.linalg.norm(axis)
    t=np.cross(axis,[1.,0,0])
    if np.linalg.norm(t)<.1:t=np.cross(axis,[0,1.,0])
    t/=np.linalg.norm(t);c=np.cross(axis,t)
    a=np.linspace(0,2*np.pi,angular,endpoint=False)
    ring=np.cos(a)[:,None]*t+np.sin(a)[:,None]*c
    zs=np.linspace(0,length,math.ceil(length/axial_step)+1)
    rr=np.linspace(0,radius,math.ceil(radius/radial_step)+1)
    side=np.array(origin)[None,None,:]+zs[:,None,None]*axis[None,None,:]+radius*ring[None,:,:]
    caps=np.concatenate([np.array(origin)[None,None,:]+z*axis[None,None,:]+rr[:,None,None]*ring[None,:,:] for z in [0,length]])
    points=np.vstack([side.reshape(-1,3),caps.reshape(-1,3)])
    da=2*np.pi/angular;dz=float(np.diff(zs).max());dr=float(np.diff(rr).max())
    angular_error=2*radius*math.sin(da/4)
    cover=max(math.hypot(dz/2,angular_error),math.hypot(dr/2,angular_error))
    return points,cover

def whole_obstacle_not_contained(obstacles,toolbounds):
    # A connected closed obstacle wholly inside the tool could avoid all tool
    # boundary samples. Demonstrate a point of every obstacle outside the
    # tool's AABB, hence outside the tool, to exclude that case.
    lo,hi=toolbounds
    return {k:bool(np.any(m.bounds[0]<lo-1e-9) or np.any(m.bounds[1]>hi+1e-9)) for k,m in obstacles.items()}

def main():
    rec,components=load_recommended();source,_,_=make_fixed()
    sm=json.loads((ROOT/'design-b/recommended-shells.json').read_text())
    for row in sm['shells']:source[f"stock-{row['object_id']}"]=trimesh.load_mesh(ROOT/row['path'])
    obstacles={**source,**components}
    obstacles['deployed-sight']=load_meshes()['obj_2_Sight2.STEP.stl']
    files=[ROOT/'design-b/recommended-assembly.json',ROOT/'design-b/recommended-shells.json',
           ROOT/'assembly-study/recover_core.py',ROOT/'ancillary-study/model_ancillary.py',HERE/'check_usage.py']
    files += [ROOT/c['path'] for c in rec['components']]+[ROOT/r['path'] for r in sm['shells']]
    h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    start={str(p.relative_to(ROOT)):h(p) for p in files}
    results=[]
    for j in rec['joints']:
        M=np.array(j['adapter_local_to_assembly']);p=M[:3,3];n=np.array(j['outward_axis'])
        obs={k:v for k,v in obstacles.items() if not k.startswith(j['id']+'--')}
        for side,r,L,astep,rstep,angular,z,axis in [
          ('inside',2.,35.,1.,.5,32,j['head_inner_face_local_z_mm']-.1,-n),
          ('outside',6.,30.,.3,.3,128,j['nut_outer_face_local_z_mm']+.1,n)]:
            origin=p+n*z
            pts,c=cylinder_boundary(origin,axis,r,L,angular,astep,rstep)
            rows=sampled_clearance(pts,obs)
            d=min(q['minimum_sampled_clearance_mm'] for q in rows)
            notinside=whole_obstacle_not_contained(obs,np.array([pts.min(0),pts.max(0)]))
            results.append({'joint':j['id'],'envelope':side+'-tool-static',
              'boundary_sample_count':len(pts),'surface_cover_radius_mm':c,
              'minimum_sample_bound_mm':d,'continuous_boundary_clearance_lower_bound_mm':d-c,
              'no_obstacle_wholly_inside_tool_AABB':all(notinside.values()),
              'conditional_geometric_clear':d>c and all(notinside.values()),'checks':rows})
            if side=='inside':
                travel=max(0,300.-origin[2]);shifts=np.linspace(0,travel,math.ceil(travel/1.)+1)
                # Reuse the exact cylinder boundary at every translation. A
                # point on an intermediate boundary is within half the largest
                # step from a checked translated boundary.
                allpts=np.vstack([pts+[0,0,s] for s in shifts])
                rows=sampled_clearance(allpts,obs)
                d=min(q['minimum_sampled_clearance_mm'] for q in rows)
                motion_cover=float(np.diff(shifts).max()/2)
                notinside=whole_obstacle_not_contained(obs,np.array([allpts.min(0),allpts.max(0)]))
                results.append({'joint':j['id'],'envelope':'interior-tool-rear-entry',
                  'boundary_sample_count':len(allpts),'translation_samples':len(shifts),
                  'translation_mm':travel,'surface_cover_radius_mm':c,'motion_cover_radius_mm':motion_cover,
                  'minimum_sample_bound_mm':d,'continuous_boundary_clearance_lower_bound_mm':d-c-motion_cover,
                  'no_obstacle_wholly_inside_tool_AABB':all(notinside.values()),
                  'conditional_geometric_clear':d>c+motion_cover and all(notinside.values()),'checks':rows,
                  'required_state':'Unloaded, membrane clear of entry corridor; actual rear-clamp release is separately unproved.'})
            print('certificate',j['id'],side,'done',flush=True)
    # Whole rigid moving components have radius bounded by source vertices;
    # pure axial motion and a boundedXYoffset cannot exceed that radius+offset.
    mov=load_meshes();radial=[];off=60*math.tan(math.radians(10))
    fixed_without_sight={**source,**components}
    min_fixed=min(radial_bounds(m)[0] for m in fixed_without_sight.values())
    for name,m in mov.items():
        if not name.startswith(('obj_5_','obj_17_','obj_9_')):continue
        r=float(np.linalg.norm(m.vertices[:,:2],axis=1).max())
        delta=0. if name.startswith('obj_9_') else off
        radial.append({'component':name,'rigid_max_radius_mm':r,'assumed_max_XY_translation_mm':delta,
          'minimum_fixed_surface_radius_mm':min_fixed,'continuous_radial_separation_mm':min_fixed-r-delta,
          'conditional_geometric_clear':min_fixed>r+delta,
          'scope':'All0..60mm axial positions andXYtranslation magnitude<=10.5796mm; rigidpieceskeepaxialorientation.'})
    result={'scope':'Conditional continuous CAD geometry certificate, not physical/tool/human validation',
      'method':'1-Lipschitz distance bound on dense cylinder boundary; translation cover adds half step. Every connected obstacle is shown not wholly contained within tool AABB. Rigid moving pieces use exact mesh radial envelopes.',
      'tolerance_statement':'Coordinates/mesh tessellation treated as exact inputs; no physical FDM, hardware, tool or deformation tolerance credited.',
      'tool_certificates':results,'continuous_rigid_motion':radial,
      'input_hashes':start,'inputs_unchanged_during_run':start=={str(p.relative_to(ROOT)):h(p) for p in files},
      'conditions':['Closed connected obstacle solids, rigidpositions as supplied','Specified cylindricaltoolenvelopes; targethardwareintentionalcontacts excluded',
                    'Unloadedserviceandmembraneclearofinteriorentry','Film,bandwrinklesandactualhandaccessnotcertifiedbytheseformulas']}
    (HERE/'continuous-envelope-certificates.json').write_text(json.dumps(result,indent=2)+'\n')
    print('WrotecontinuousCADenvelopecertificates',flush=True)

if __name__=='__main__':main()
