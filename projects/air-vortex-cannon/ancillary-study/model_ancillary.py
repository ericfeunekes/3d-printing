"""Stock ancillary assembly reconstruction, mm, right-handed X/Y/Z.

Canonical X is horizontal, Y up, Z rearward; outlet plane Z=0.
This owns ancillary poses only, not shells/rails. Source meshes stay immutable.
"""
from pathlib import Path
import json, math
import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
SOURCE=ROOT/'source/egordv'

def pose(rotation, source_datum, target_datum):
    r=np.asarray(rotation,dtype=float)
    t=np.asarray(target_datum)-r@np.asarray(source_datum)
    m=np.eye(4);m[:3,:3]=r;m[:3,3]=t
    assert abs(np.linalg.det(r)-1)<1e-9
    return m

def around_x(point, angle):
    c,s=math.cos(angle),math.sin(angle)
    r=np.array([[1,0,0],[0,c,-s],[0,s,c]])
    return pose(r,point,point)

def make_transforms(rear_plane=259.8896408, stroke=0.0, sight_fold_degrees=0.0,
                    membrane_face_offset=2.0, film_gap=.05, junction_z=None):
    """Return source-to-canonical matrices and explicit observation/assumption tags.

    stroke and junction_z are study parameters, not measured operating travel.
    Central cap/male seating is coaxial with a nominal film sandwich. It needs
    flex/contact analysis; do not assert that this snap fit is rigidly clear.
    """
    film_z=rear_plane+membrane_face_offset
    center_z=film_z+stroke
    hinge=np.array([0.0,109.31366559,26.76465696])
    # Fore/aft orientation matters even though both rotations align the bore:
    # native Z faces rearward, putting the native bottom foot forward of the
    # hinge rather than inside the rail bridge. Verified deployed samples.
    sight_rotation=np.array([[0,-1,0],[1,0,0],[0,0,1]])
    sight=pose(sight_rotation,[112.13520,126.9764,7.86755],hinge)
    sight=around_x(hinge,math.radians(sight_fold_degrees))@sight
    # The shaft starts immediately outside the negative-X fork ear.
    axle_rotation=np.array([[0,1,0],[1,0,0],[0,0,-1]])
    axle=pose(axle_rotation,[375.8040619,98.5329437,2.0],[-4.5,hinge[1],hinge[2]])
    if junction_z is None:
        junction_z=(4.050995+center_z)/2
    r_carabiner=np.array([[1,0,0],[0,0,-1],[0,1,0]])
    return {
      'obj_10_BackClampRing4.STEP.stl':{
        'matrix':pose(np.diag([1,-1,-1]),[435.1999817,127.9999962,2],[0,0,rear_plane]).tolist(),
        'basis':'Measured sleeve OD120.484 radius versus rear shell lip ID120.584. Clamp shoulder Z2 aligned rear end; sleeve points forward.',
        'status':'geometry-derived nominal seat; film thickness and snap deformation unverified'},
      'obj_17_PinchRing3.STEP.stl':{
        'matrix':pose(np.eye(3),[466.3531494,87.8349037,5],[0,0,center_z]).tolist(),
        'basis':'Measured flange upper face source Z5, 40mm flange, split cylindrical projection to Z11.55.',
        'status':'coaxial film-sandwich reconstruction; flexible snap seating not validated'},
      'obj_5_PinchRingCap3.STEP.stl':{
        'matrix':pose(np.eye(3),[509.6119995,78.9592590,0],[0,0,center_z+film_gap]).tolist(),
        'basis':'Video2:28/4:18 shows finger loop outside rear diaphragm. Disk axis source Z; large plane areas confirm datum.',
        'status':'coaxial film-sandwich reconstruction; expects snap-contact interference, not rigid-clearance proof'},
      'obj_9_RubberBandCarabiner01.STEP.stl':{
        'matrix':pose(r_carabiner,[359.8718567,105.0827446,1.5],[0,0,junction_z]).tolist(),
        'basis':'Video3:23 connects two additional bands with carabiner;3:48 joins front anchor loops;4:08 passes loops through pinch-ring hole.',
        'status':'schematic axial junction; its exact Z and orientation depend on unmeasured elastic lengths/stiffness'},
      'obj_2_Sight2.STEP.stl':{
        'matrix':sight.tolist(),
        'basis':'Measured R2.5 hole centre; ear thickness4.3 versus rail fork gap5.0, nominal0.35mm per face. NativeZ maps canonical+Z; deployed1805point check found no penetration over0.02mm without hinge exclusions. Video5:38 confirms broadly deployed orientation.',
        'status':'deployed reconstruction only. Sampled15/30degree positive fold poses collide with rail; no continuous folding claim'},
      'obj_1_SightPin2.STEP.stl':{
        'matrix':axle.tolist(),
        'basis':'Measured axis sourceY, centre X375.8040619/Z2; sourceY98.5329437 shoulder placed outside rail fork at X-4.5.',
        'status':'geometry-derived axial pose; printed snap retention unverified'},
    }

def load_meshes(**kwargs):
    out={}
    for name,row in make_transforms(**kwargs).items():
        m=trimesh.load_mesh(SOURCE/name);m.apply_transform(np.array(row['matrix']));out[name]=m
    return out

def membrane_mesh(rear_plane=259.8896408, stroke=0.0, outer_radius=116.8533,
                  inner_radius=20.0, radial_steps=16, angular_steps=96):
    """Annular truncated-cone study surface; zero thickness, no constitutive model.

    It deliberately does not pretend to recover shopping-bag slack/wrinkles.
    Outer edge lies at rear_plane+2, central rigid clamp translates by stroke.
    """
    vv=[];ff=[];base=rear_plane+2
    for i,r in enumerate(np.linspace(inner_radius,outer_radius,radial_steps)):
        z=base+stroke*(outer_radius-r)/(outer_radius-inner_radius)
        for a in np.linspace(0,2*np.pi,angular_steps,endpoint=False):vv.append([r*np.cos(a),r*np.sin(a),z])
    for i in range(radial_steps-1):
        for j in range(angular_steps):
            a=i*angular_steps+j;b=i*angular_steps+(j+1)%angular_steps;c=(i+1)*angular_steps+j;d=(i+1)*angular_steps+(j+1)%angular_steps
            ff.extend([[a,c,b],[b,c,d]])
    return trimesh.Trimesh(vertices=np.array(vv),faces=np.array(ff),process=False)

def band_graph(rear_plane=259.8896408, stroke=0.0, junction_z=None):
    pz=rear_plane+2+stroke
    if junction_z is None:junction_z=(4.050995+pz)/2
    return {
      'nodes':{'front_left':[-72.730,0,4.050995],'front_right':[72.730,0,4.050995],
               'carabiner':[0,0,junction_z],'membrane_centre':[0,0,pz]},
      'edges':[['front_left','carabiner'],['front_right','carabiner'],
               ['carabiner','membrane_centre'],['carabiner','membrane_centre']],
      'basis':'Four-band topology observed at designer video3:03,3:23,3:48,4:08 and4:18.',
      'assumption':'Band loops represented as line segments. Junction Z, routing at tie points, rest lengths and constitutive law unmeasured. The default midpoint is a display parameter, not a static equilibrium solution.'}

def membrane_requirements(stroke=60.0,outer_radius=116.8533,inner_radius=20.0):
    span=outer_radius-inner_radius
    meridian=math.hypot(span,stroke)
    flat_area=math.pi*(outer_radius**2-inner_radius**2)
    cone_area=math.pi*(outer_radius+inner_radius)*meridian
    return {'stroke_mm':stroke,'flat_annular_area_mm2':flat_area,'cone_envelope_area_mm2':cone_area,
            'area_ratio':cone_area/flat_area,'minimum_extra_area_fraction':cone_area/flat_area-1,
            'meridian_length_mm':meridian,'extra_meridian_length_mm':meridian-span,
            'meaning':'Necessary geometric slack/strain bound for the idealized cone, not a recovered bag pattern or constitutive proof. Source bag wrinkles/slack are unmeasured.'}

def main():
    out=HERE/'posed';out.mkdir(exist_ok=True)
    poses=make_transforms()
    for name,m in load_meshes().items():m.export(out/name)
    membrane_mesh().export(out/'membrane-flat-study.stl')
    membrane_mesh(stroke=60).export(out/'membrane-60mm-pull-study.stl')
    record={'units':'mm','canonical_axes':'X horizontal, Y up, Z rearward, outlet Z0',
            'rear_shell_end_z':259.8896408,'nominal_membrane_edge_z':261.8896408,
            'poses':poses,'elastic_graph':band_graph(),
            'motion_study':{'stroke_values_mm':[0,15,30,45,60],
                            'status':'Illustrative user-approved assumed travel. Not measured travel, recommended maximum, or energy optimization.'},
            'membrane_area_requirements_60mm':membrane_requirements(60),
            'remaining_checks':['Central snap fit contact/deformation','Rear clamp bead snap insertion/removal deformation',
                                'Sight sweep against assembled rail/shell','Actual film slack/thickness and band properties']}
    (HERE/'ancillary-poses.json').write_text(json.dumps(record,indent=2)+'\n')
    print('Wrote ancillary poses and six posed original mesh copies.')

if __name__=='__main__':main()
