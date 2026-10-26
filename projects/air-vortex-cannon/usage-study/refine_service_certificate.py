"""Refine only low positive mesh bounds that could not prove a tool cover gap."""
from pathlib import Path
import json,sys,math,hashlib
import numpy as np,trimesh
ROOT=Path(__file__).resolve().parents[1];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(ROOT/'ancillary-study')]
from check_usage import make_fixed,radial_bounds,local_slab_bounds,signed
from check_recommended import load_recommended
from certify_envelopes import cylinder_boundary
from model_ancillary import load_meshes

def signed_axis(mesh,points):
    """Triangle proximity plus bidirectional axis-ray containment.

    CanonicalX rays traverse the narrow rail rather than the long diagonal
    AABB of the library's default direction. Unique hit locations are counted
    to avoid duplicate shared-edge triangle hits. Disagreement falls back to
    the library's signed query; points on the surface have zero distance.
    """
    _,distance,_=trimesh.proximity.closest_point(mesh,points)
    counts=[]
    for sign in [1.,-1.]:
        directions=np.tile([sign,0.,0.],(len(points),1))
        _,ray_index,_=mesh.ray.intersects_location(points,directions,multiple_hits=True)
        counts.append(np.bincount(ray_index,minlength=len(points))%2==1)
    agree=counts[0]==counts[1]
    out=np.where(counts[0],distance,-distance)
    out[distance<1e-8]=0.
    ambiguous=(~agree)&(distance>=1e-8)
    if np.any(ambiguous):out[ambiguous]=signed(mesh,points[ambiguous],chunk=64)
    return out,int(ambiguous.sum())

def main():
    f=HERE/'continuous-envelope-certificates.json';base=json.loads(f.read_text())
    rec,components=load_recommended();source,_,_=make_fixed()
    for row in json.loads((ROOT/'design-b/recommended-shells.json').read_text())['shells']:
        source[f"stock-{row['object_id']}"]=trimesh.load_mesh(ROOT/row['path'])
    obs={**source,**components,'deployed-sight':load_meshes()['obj_2_Sight2.STEP.stl']}
    refinements=[]
    for row in base['tool_certificates']:
        if row['conditional_geometric_clear']:continue
        if row['envelope']!='outside-tool-static':raise ValueError('Unsupported refinement target')
        j=next(j for j in rec['joints'] if j['id']==row['joint'])
        M=np.asarray(j['adapter_local_to_assembly']);n=np.asarray(j['outward_axis']);origin=M[:3,3]+n*(j['nut_outer_face_local_z_mm']+.1)
        pts,cover=cylinder_boundary(origin,n,6.,30.,128,.3,.3)
        changes=[]
        for q in row['checks']:
            if q['minimum_sampled_clearance_mm']>cover+.025:continue
            mesh=obs[q['obstacle']];lo,hi=mesh.bounds
            box=np.linalg.norm(np.maximum(np.maximum(lo-pts,pts-hi),0),axis=1)
            a,b=radial_bounds(mesh);r=np.linalg.norm(pts[:,:2],axis=1)
            radial=np.maximum(np.maximum(a-r,r-b),0)
            bound=np.maximum(np.maximum(box,radial),local_slab_bounds(mesh,pts))
            near=bound<=cover+.025
            distance=bound.copy();values,ambiguous=signed_axis(mesh,pts[near]);distance[near]=-values
            qold=q['minimum_sampled_clearance_mm']
            q['minimum_sampled_clearance_mm']=float(distance.min())
            q['maximum_sampled_penetration_mm']=float(max(0,-distance.min()))
            q['points_over_0_02mm_penetration']=int((distance<-.02).sum())
            q['certificate_refinement']='All mesh-bound samples below surface-cover+.025mm replaced with exact triangle signed distance.'
            changes.append({'obstacle':q['obstacle'],'prior_minimum_bound_mm':qold,'exact_refined_samples':int(near.sum()),'axis_ray_disagreement_fallback_count':ambiguous,'new_minimum_bound_mm':float(distance.min())})
        d=min(q['minimum_sampled_clearance_mm'] for q in row['checks'])
        row['minimum_sample_bound_mm']=d;row['continuous_boundary_clearance_lower_bound_mm']=d-cover
        row['conditional_geometric_clear']=d>cover and row['no_obstacle_wholly_inside_tool_AABB']
        row['refinement']=changes
        refinements.append({'joint':row['joint'],'envelope':row['envelope'],'changes':changes,'new_continuous_bound_mm':d-cover,'conditional_geometric_clear':row['conditional_geometric_clear']})
    base['unrefined_certificate_sha256']=hashlib.sha256(f.read_bytes()).hexdigest()
    base['refinement_artifact']='continuous-envelope-certificates-refined.json'
    base['semantic_rebaseline_record']='semantic-rebaseline.json; old assembly JSON hash is preserved and geometry/service pose equivalence independently checked.'
    (HERE/'continuous-envelope-certificates-refined.json').write_text(json.dumps(base,indent=2)+'\n')
    (HERE/'certificate-refinement.json').write_text(json.dumps(refinements,indent=2)+'\n')
    print(json.dumps(refinements,indent=2),flush=True)

if __name__=='__main__':main()
