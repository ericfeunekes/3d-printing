"""Revision A: independent parametric keeper for egordv's stock split pin.

Units: mm. Source meshes remain immutable. No third-party lock geometry used.
CAD XY is the stock pin's X/Z profile; CAD Z is extrusion/print height.
"""
from pathlib import Path
from dataclasses import dataclass, asdict
import hashlib
import json
import math
import numpy as np
import trimesh
from build123d import Circle, Rectangle, RectangleRounded, Polygon, Pos, extrude, export_step, export_stl, import_step

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / 'parts'
OUT.mkdir(exist_ok=True)
SOURCE = ROOT / 'source/egordv/obj_11_AirZookaPin04.STEP.stl'

@dataclass(frozen=True)
class Spec:
    # Recovered stock interface, not dimensions of a physical printed sample.
    stock_gap: float = 9.0
    stock_body_depth: float = 7.3
    stock_u_center_z: float = 6.5
    stock_tip_z: float = 12.5
    # New prototype choices, all untested manufacturing fits.
    foot_radius: float = 4.3
    body_depth: float = 6.8
    taper_start_z: float = 10.0
    cap_width: float = 12.0
    cap_bottom_z: float = 12.5
    cap_top_z: float = 14.5
    eye_width: float = 8.0
    eye_bottom_z: float = 13.2
    eye_top_z: float = 18.8
    eye_hole_diameter: float = 3.2
    eye_hole_center_z: float = 16.1

S = Spec()

def make_keeper(seat_width):
    r,zc=S.foot_radius,S.stock_u_center_z
    # Rounded leading foot fits inside the recovered R4.5 U bottom.
    # Full circle overlaps the stem; its upper half is contained by the stem.
    # Overlap avoids coincident-edge-only unions in the planar CAD kernel.
    foot=Pos(0,zc)*Circle(r)
    stem=Polygon((r,zc),(r,S.taper_start_z),(seat_width/2,S.stock_tip_z),
                 (seat_width/2,S.stock_tip_z+.2),(-seat_width/2,S.stock_tip_z+.2),
                 (-seat_width/2,S.stock_tip_z),(-r,S.taper_start_z),(-r,zc),align=None)
    # Cap contacts the ends of the arms; the eye supports deliberate removal.
    # Neither is asserted to provide self-retention. That requires a fit trial.
    cap=Pos(0,(S.cap_bottom_z+S.cap_top_z)/2)*Rectangle(S.cap_width,S.cap_top_z-S.cap_bottom_z)
    eye=Pos(0,(S.eye_bottom_z+S.eye_top_z)/2)*RectangleRounded(S.eye_width,S.eye_top_z-S.eye_bottom_z,1.6)
    hole=Pos(0,S.eye_hole_center_z)*Circle(S.eye_hole_diameter/2)
    profile=(foot+stem+cap+eye)-hole
    shape=extrude(profile,amount=S.body_depth,dir=(0,0,1))
    pieces=shape.solids()
    shape=pieces[0].fuse(*pieces[1:]).clean()
    # Normalize print orientation to nonnegative XYZ with full profile on bed.
    shape=Pos(S.cap_width/2,-(zc-r),0)*shape
    return shape

def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

results=[]
# Do not issue an intentional interference variant: spreading the stock clip
# would be poorly matched to the reported clip and thin-shell fractures.
for obsolete in [OUT/'keeper-snug.stl', OUT/'keeper-snug.step']:
    if obsolete.exists(): obsolete.unlink()
for tag,width in [('clearance',8.9),('nominal',9.0)]:
    shape=make_keeper(width)
    assert shape.is_valid and len(shape.solids())==1, (shape.is_valid, len(shape.solids()), [s.volume for s in shape.solids()])
    step=OUT/f'keeper-{tag}.step'
    stl=OUT/f'keeper-{tag}.stl'
    export_step(shape,step)
    export_stl(shape,stl,tolerance=.015,angular_tolerance=.1)
    reloaded=import_step(step)
    mesh=trimesh.load_mesh(stl)
    assert mesh.is_watertight and mesh.is_winding_consistent
    assert len(mesh.split())==1
    assert abs(reloaded.volume-shape.volume)<.01
    # mm, at 100%; no slicer or physical-fit claim follows from this envelope.
    assert np.all(mesh.extents < [256,256,260])
    results.append({'name':tag,'seat_width_mm':width,
                    'total_gap_at_full_seat_mm':S.stock_gap-width,
                    'body_depth_total_clearance_mm':S.stock_body_depth-S.body_depth,
                    'bounds_mm':mesh.extents.tolist(),'volume_mm3':shape.volume,
                    'valid_solid':shape.is_valid,'watertight':mesh.is_watertight,
                    'connected_components':len(mesh.split()),
                    'step_roundtrip_volume_delta_mm3':reloaded.volume-shape.volume,
                    'stl_sha256':file_hash(stl),'step_sha256':file_hash(step),
                    'designed_seat_interference_per_face_mm':max(0,(width-S.stock_gap)/2)})

# Unchanged reference geometry with only a rigid orientation/placement change.
pin=trimesh.load_mesh(SOURCE)
pin.apply_translation([-pin.bounds.mean(axis=0)[0],-pin.bounds.mean(axis=0)[1],-pin.bounds[0,2]])
pin_reference=pin.copy()
pin_reference.apply_translation([11.65,7.65,0])
pin_reference.export(OUT/'stock-pin-reference.stl')
side=pin.copy()
side.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]))
side.apply_translation(-side.bounds[0])
side.export(OUT/'stock-pin-side-trial.stl')

manifest={'revision':'A','status':'UNPRINTED PROTOTYPE — fit and retention unverified',
          'base_design':'egordv, Air Vortex Cannon, designer profile 348811',
          'source_url':'https://makerworld.com/en/models/442826-air-vortex-cannon#profileId-348811',
          'license':'CC BY-NC-SA 4.0; https://creativecommons.org/licenses/by-nc-sa/4.0/',
          'source_pin_sha256':file_hash(SOURCE),
          'native_cad_owner':'build_revision.py / Spec; new keeper geometry only',
          'units':'millimetres','spec':asdict(S),'variants':results,
          'limits':['No complete-assembly collision or load validation',
                    'Keeper seating assumes access from barbed end of installed clip',
                    'Friction fit/self-retention and removal require a physical test',
                    'Cap geometry is not a positive lock',
                    'No intentional interference variant issued; never force a fit',
                    'No increased elastic load, range, accuracy or ring-coherence claim',
                    'No slicer project, toolpath, print or purchase generated'],
          'reference_pin':{'rigid_transform_only':True,'stock_watertight':pin.is_watertight,
                           'side_trial_supports':'Required under elevated body; slice inspection pending'}}
(HERE/'validation.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'revision':'A','variants':results},indent=2))
