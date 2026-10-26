"""One practical optional tool requirement: top-rear outer body OD<=11mm.

This is a tool-envelope requirement, not a claim about any purchased socket.
Only this site changes from the main R6×30mm cylinder to R5.5×30mm.
"""
from pathlib import Path
import sys,json,hashlib,numpy as np,trimesh
ROOT=Path(__file__).resolve().parents[1];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(ROOT/'ancillary-study')]
from check_usage import make_fixed,sampled_clearance,radial_bounds,local_slab_bounds
from check_recommended import load_recommended
from certify_envelopes import cylinder_boundary,whole_obstacle_not_contained
from refine_service_certificate import signed_axis
from model_ancillary import load_meshes

def main():
    rec,components=load_recommended();source,_,_=make_fixed()
    for row in json.loads((ROOT/'design-b/recommended-shells.json').read_text())['shells']:
        source[f"stock-{row['object_id']}"]=trimesh.load_mesh(ROOT/row['path'])
    obs={**source,**components,'deployed-sight':load_meshes()['obj_2_Sight2.STEP.stl']}
    j=next(j for j in rec['joints'] if j['id']=='top-rear')
    obs={k:v for k,v in obs.items() if not k.startswith(j['id']+'--')}
    M=np.array(j['adapter_local_to_assembly']);n=np.array(j['outward_axis'])
    origin=M[:3,3]+n*(j['nut_outer_face_local_z_mm']+.1)
    pts,cover=cylinder_boundary(origin,n,5.5,30.,128,.25,.25)
    rows=sampled_clearance(pts,obs)
    # Tighten loose geometry bounds near the site enough to evaluate a useful
    # margin, rather than stopping at a merely positive certificate.
    refinements=[]
    target_sample_bound=1.2
    for q in rows:
        if q['minimum_sampled_clearance_mm']>=target_sample_bound:continue
        mesh=obs[q['obstacle']];lo,hi=mesh.bounds
        box=np.linalg.norm(np.maximum(np.maximum(lo-pts,pts-hi),0),axis=1)
        a,b=radial_bounds(mesh);r=np.linalg.norm(pts[:,:2],axis=1)
        bound=np.maximum(np.maximum(box,np.maximum(np.maximum(a-r,r-b),0)),local_slab_bounds(mesh,pts))
        near=bound<target_sample_bound
        values,ambiguous=signed_axis(mesh,pts[near])
        distances=bound.copy();distances[near]=-values
        old=q['minimum_sampled_clearance_mm']
        q['minimum_sampled_clearance_mm']=float(distances.min())
        q['maximum_sampled_penetration_mm']=float(max(0,-distances.min()))
        q['points_over_0_02mm_penetration']=int((distances<-.02).sum())
        refinements.append({'obstacle':q['obstacle'],'previous_loose_bound_mm':old,
          'exact_triangle_refined_samples':int(near.sum()),'bidirectional_ray_disagreement_fallbacks':ambiguous,
          'minimum_refined_bound_mm':float(distances.min())})
    d=min(q['minimum_sampled_clearance_mm'] for q in rows)
    notcontained=whole_obstacle_not_contained(obs,np.array([pts.min(0),pts.max(0)]))
    result={'joint':'top-rear','scope':'Optional exterior7mmnut tool body requirement; no purchased tool verified',
      'tool_body_maximum_OD_mm':11.,'tool_envelope_length_mm':30.,
      'tool_origin_mm':origin.tolist(),'tool_axis':n.tolist(),'surface_sample_count':len(pts),
      'surface_cover_radius_mm':cover,'minimum_sample_bound_mm':d,
      'continuous_CAD_clearance_lower_bound_mm':d-cover,
      'no_obstacle_wholly_inside_tool_AABB':all(notcontained.values()),
      'conditional_geometric_clear':d>cover and all(notcontained.values()),
      'checks':rows,'low_bound_refinements':refinements,
      'assembly_json_sha256':hashlib.sha256((ROOT/'design-b/recommended-assembly.json').read_bytes()).hexdigest(),
      'limits':'All other sites retain mainR6envelope. Realtoolshape/OD, FDMandhardwareerror, grasp/reach and movingclearances still require matching the assumptions.'}
    (HERE/'slim-tool-option.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['checks']},indent=2),flush=True)

if __name__=='__main__':main()
