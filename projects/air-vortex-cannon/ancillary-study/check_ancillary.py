from pathlib import Path
import importlib.util,json
import numpy as np,trimesh

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ancillary',HERE/'model_ancillary.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
record={}
def circle_fit(points,dims):
    p=points[:,dims]
    a=np.column_stack([2*p[:,0],2*p[:,1],np.ones(len(p))]);b=(p*p).sum(1)
    fit=np.linalg.lstsq(a,b,rcond=None)[0];c=fit[:2];r=np.sqrt(fit[2]+c@c)
    err=np.linalg.norm(p-c,axis=1)-r
    return {'center':c.tolist(),'radius':float(r),'max_radial_residual_mm':float(np.abs(err).max())}

for name,normal,origin,dims in [
    ('obj_2_Sight2.STEP.stl',[0,1,0],[0,126.6264,0],[0,2]),
    ('obj_3_TopClamp3.STEP.stl',[0,0,1],[0,0,9],[0,1])]:
    mesh=trimesh.load_mesh(module.SOURCE/name)
    paths=mesh.section(plane_normal=normal,plane_origin=origin).discrete
    candidates=[]
    for path in paths:
        ext=path[:,dims].max(0)-path[:,dims].min(0)
        if np.all(abs(ext-5)<.02):candidates.append(circle_fit(path,dims))
    record[name]={'circle_fit':candidates}

meshes=module.load_meshes()
male=meshes['obj_17_PinchRing3.STEP.stl']
cap=meshes['obj_5_PinchRingCap3.STEP.stl']
# Probe actual outer snap-face points, shifted 0.01 mm into the male material,
# rather than treating a heavy global ray sample as a complete contact proof.
film_z=259.8896408+2
centres=male.triangles_center
r=np.linalg.norm(centres[:,:2],axis=1)
radial=np.column_stack([centres[:,:2]/r[:,None],np.zeros(len(r))])
outward=(male.face_normals*radial).sum(1)
indices=np.where((centres[:,2]>film_z+.01)&(r>7.05)&(outward>.6))[0]
indices=indices[np.linspace(0,len(indices)-1,min(24,len(indices)),dtype=int)]
pts=centres[indices]-male.face_normals[indices]*.01
d=trimesh.proximity.signed_distance(cap,pts)
male_inside=male.contains(pts)
record['central_male_into_cap_nominal_pose']={
    'sampled_points':len(pts),'max_sampled_penetration_mm':float(max(0,d[male_inside].max())) if male_inside.any() else None,
    'points_over_0_02mm':int(((d>.02)&male_inside).sum()),
    'candidate_points_inside_male':male_inside.tolist(),
    'probe_points_canonical_mm':pts.tolist(),
    'meaning':'Sampled actual snap-face probe only. A positive depth counts only when point lies in male material too. Neither continuous rigid-clear mating nor elastic deformation is proved.'}

back=trimesh.load_mesh(module.SOURCE/'obj_7_AirZooka03_RingBack.STEP.stl')
back.apply_translation([-128,-128,171])
clamp=meshes['obj_10_BackClampRing4.STEP.stl']
pts=np.vstack([clamp.vertices[::max(1,len(clamp.vertices)//50)],clamp.triangles_center[::max(1,len(clamp.faces)//50)]])
d=trimesh.proximity.signed_distance(back,pts)
record['rear_clamp_seated']={'sampled_points':len(pts),'max_sampled_penetration_mm':float(max(0,d.max())),
                            'points_over_0_02mm':int((d>.02).sum()),
                            'meaning':'Rigid static sample only; insertion/removal snap deformation and film are excluded.'}
raw=trimesh.load_mesh(module.SOURCE/'obj_10_BackClampRing4.STEP.stl')
vv=raw.vertices-np.array([435.1999817,127.9999962,0]);rr=np.linalg.norm(vv[:,:2],axis=1)
ii=np.where(vv[:,2]>2.001)[0];kk=ii[np.argmax(rr[ii])]
record['rear_clamp_withdrawal_geometry']={
    'maximum_sleeve_radius_mm':float(rr[kk]),'at_source_z_mm':float(vv[kk,2]),
    'shell_lip_bore_radius_mm':120.584,
    'coaxial_rigid_radial_overlap_mm':float(rr[kk]-120.584),
    'meaning':'Withdrawal interference, not elastic strain or force. Flex/tilt/removal kinematics remain unresolved.'}
(HERE/'ancillary-checks.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
