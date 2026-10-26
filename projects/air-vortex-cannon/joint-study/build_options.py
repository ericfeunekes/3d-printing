"""Parametric joint-architecture study, not the final installed connection.

Units mm. Local X=cone-generator tangent (radius increasing toward +X),
Y=circumferential tangent, Z=outward surface normal. Radius is the shell
INNER radius at the contact datum. Set axis_normal=False for radial axes.
Functions are importable; main writes only this study's outputs.
"""
from pathlib import Path
from dataclasses import dataclass,asdict
import math,json
import build123d as b

HERE=Path(__file__).resolve().parent

@dataclass(frozen=True)
class Spec:
    radius: float=110.0
    cone_slope: float=.09616
    grip_stack: float=6.0  # REPRESENTATIVE ONLY; replace from recovered assembly
    key_length: float=14.8
    key_width: float=7.4
    flange_length: float=24.0
    flange_width: float=16.0
    base_thickness: float=3.0
    hole_diameter: float=6.2  # M4/OD6 spacer option; .2mm total sleeve clearance
    capture_gap: float=.15   # intended capture play, not manufacturing guarantee
    outer_plate_thickness: float=2.0

def _clean(shape):
    pieces=shape.solids()
    if len(pieces)>1: shape=pieces[0].fuse(*pieces[1:])
    shape=shape.clean()
    assert shape.is_valid and len(shape.solids())==1,(shape.is_valid,len(shape.solids()))
    return shape

def make_inner_adapter(radius, cone_slope, grip_stack, key_length=14.8,
                       key_width=7.4,flange_length=24.,flange_width=16.,
                       base_thickness=3.,hole_diameter=6.2,capture_gap=.15,
                       axis_normal=True,key_end_z=None):
    # Curved shell contact comes from the actual conical surface, not a flat
    # washer credited as conformal. Bolt axis stays radial like the stock pin.
    cone_length=80.
    cone=b.Pos(-cone_length/2,0,-radius)*b.Rot(0,90,0)*b.Cone(
        radius-cone_slope*cone_length/2,radius+cone_slope*cone_length/2,
        cone_length,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))
    if axis_normal:
        cone=b.Rot(0,math.degrees(math.atan(cone_slope)),0)*cone
    profile=b.RectangleRounded(flange_length,flange_width,5.)
    slab=b.Pos(0,0,-base_thickness)*b.extrude(profile,amount=base_thickness+2.0)
    saddle=slab & cone
    end_z=grip_stack+capture_gap if key_end_z is None else key_end_z
    key=b.Pos(0,0,-2)*b.extrude(b.RectangleRounded(key_length,key_width,3.5),amount=end_z+2)
    hole=b.Pos(0,0,-base_thickness-1)*b.Cylinder(hole_diameter/2,
        grip_stack+base_thickness+capture_gap+3,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))
    return _clean(saddle+key-hole)

def make_outer_adapter(grip_stack,flange_length=24.,flange_width=16.,
                       hole_diameter=6.2,capture_gap=.15,thickness=2.,base_z=None):
    z=grip_stack+capture_gap if base_z is None else base_z
    plate=b.Pos(0,0,z)*b.extrude(
        b.RectangleRounded(flange_length,flange_width,5.),amount=thickness)
    hole=b.Pos(0,0,z-1)*b.Cylinder(hole_diameter/2,thickness+2,
        align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))
    return _clean(plate-hole)

def make_shoulder_hardware_reference(shoulder_length=16.):
    """Elesa/Ganter 5-M4-L + wide M5/M4 washers + M4 nut envelopes.

    Bolt under-head plane Z=0; unthreaded shoulder spans0..L and nominal
    M4thread envelope spansL..L+8. Unspecified chamfers/undercuts and threads
    are not modeled. Washer/nut returned at origin for caller placement.
    Manufacturer warns torque limited by shoulder/transition bearing points.
    """
    shoulder=b.Cylinder(2.5,shoulder_length,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))
    thread=b.Pos(0,0,shoulder_length)*b.Cylinder(2.,8.,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))
    head=b.Pos(0,0,-4)*b.Cylinder(4.5,4.,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))
    socket=b.Pos(0,0,-4.01)*b.extrude(b.RegularPolygon(2.5/math.sqrt(3),6),amount=2.51)
    bolt=_clean(shoulder+thread+head-socket)
    m5washer=_clean(b.Cylinder(7.5,1.2,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))-
        b.Cylinder(2.65,1.2,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN)))
    m4washer=_clean(b.Cylinder(6.,1.,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))-
        b.Cylinder(2.15,1.,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN)))
    nut=_clean(b.extrude(b.RegularPolygon(7/math.sqrt(3),6)-b.Circle(2.),amount=5.))
    return {'shoulder-bolt-reference':bolt,'inner-M5-wide-washer-reference':m5washer,
            'outer-M4-wide-washer-reference':m4washer,'M4-nyloc-envelope-reference':nut}

def make_printed_thread(height=9.,pitch=1.5,root_radius=2.2,crest_radius=3.,radial_clearance=0.):
    # Custom coarse thread study, NOT ISO M6 and NOT a print-fit recommendation.
    # Full matching helical geometry permits an axial-capture comparison.
    root=root_radius+radial_clearance
    crest=crest_radius+radial_clearance
    path=b.Helix(pitch,height,(root+crest)/2)
    triangle=b.Plane.XZ*b.Polygon((root-.15,-.45),(crest,0),(root-.15,.45),align=None)
    rib=b.sweep(triangle,path=path,is_frenet=True)
    core=b.Cylinder(root,height,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))
    clip=b.Cylinder(crest+.1,height,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))
    return _clean((core+rib)&clip)

def main():
    s=Spec();out=HERE/'parts';out.mkdir(exist_ok=True)
    inner=make_inner_adapter(**{k:v for k,v in asdict(s).items() if k not in ['outer_plate_thickness']})
    outer=make_outer_adapter(s.grip_stack,s.flange_length,s.flange_width,s.hole_diameter,s.capture_gap,s.outer_plate_thickness)
    metal_shaft=b.Pos(0,0,-s.base_thickness-1.1)*b.Cylinder(2.,20.,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))
    metal_head=b.Pos(0,0,-s.base_thickness-5.1)*b.Cylinder(3.5,4.,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))
    bolt=_clean(metal_shaft+metal_head)
    # Reference metal sleeve and washer make preload bypass explicit. Their
    # exact length must follow the final recovered stack and fit allowances.
    sleeve_length=s.grip_stack+s.base_thickness+s.capture_gap+s.outer_plate_thickness+.2
    sleeve=b.Pos(0,0,-s.base_thickness-.1)*(b.Cylinder(3.,sleeve_length,
        align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))-b.Cylinder(2.15,sleeve_length,
        align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN)))
    washer_z=s.grip_stack+s.capture_gap+s.outer_plate_thickness+.1
    washer=b.Pos(0,0,washer_z)*(b.Cylinder(6.,1.,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))-b.Cylinder(2.15,1.,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN)))
    inner_washer=b.Pos(0,0,-s.base_thickness-1.1)*(b.Cylinder(6.,1.,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))-b.Cylinder(2.15,1.,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN)))
    nut=b.Pos(0,0,washer_z+1)*b.extrude(b.RegularPolygon(7/math.sqrt(3),6)-b.Circle(2),amount=5.)
    # Printed option retains identical representative flange/key interface but
    # replaces the metal core with a custom coarse-threaded stud and large nut.
    solid_inner=make_inner_adapter(s.radius,s.cone_slope,s.grip_stack,s.key_length,s.key_width,
        s.flange_length,s.flange_width,s.base_thickness,.01,s.capture_gap)
    # Close the placeholder near-zero drill by fusing the core through it.
    solid_inner=_clean(solid_inner+b.Pos(0,0,-s.base_thickness)*b.Cylinder(1.,s.grip_stack+s.base_thickness+s.capture_gap,
        align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN)))
    thread=b.Pos(0,0,s.grip_stack+s.capture_gap)*make_printed_thread()
    stud=_clean(solid_inner+thread)
    thread_cutter=b.Pos(0,0,s.grip_stack+s.capture_gap)*make_printed_thread(radial_clearance=.2)
    printed_nut=b.Pos(0,0,s.grip_stack+s.capture_gap)*b.extrude(b.RegularPolygon(7.,6),amount=6.)
    printed_nut=_clean(printed_nut-thread_cutter)
    shapes={'metal-inner-adapter':inner,'metal-outer-adapter':outer,
            'metal-bolt-reference':bolt,'metal-spacer-reference':sleeve,
            'metal-washer-reference':washer,'metal-inner-washer-reference':inner_washer,
            'metal-nyloc-envelope-reference':nut,
            'printed-stud-option':stud,'printed-nut-option':printed_nut}
    result=[]
    for name,shape in shapes.items():
        b.export_step(shape,out/f'{name}.step')
        b.export_stl(shape,out/f'{name}.stl',tolerance=.03,angular_tolerance=.15)
        box=shape.bounding_box()
        result.append({'name':name,'valid':shape.is_valid,'solids':len(shape.solids()),
            'volume_mm3':shape.volume,'extents_mm':[box.size.X,box.size.Y,box.size.Z]})
    data={'purpose':'Architecture comparison, not final installed connection',
      'spec':asdict(s),'known_interface':{'slot_thin_mm':8.,'slot_axial_min_mm':15.8,
        'shell_thickness_about_mm':1.,'cone_half_angle_deg':math.degrees(math.atan(s.cone_slope))},
      'uncertainties':['grip_stack representative until actual assembly recovery',
        'capture gap and printed sleeve fit untested','no complete installed collision proof',
        'metal threads simplified to envelopes','custom printed thread not anti-backoff locked',
        'printed thread and stiffness not physical capacity evidence','saddle does not reduce in-plane slot bearing by friction assumption'],
      'parts':result}
    (HERE/'comparison.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(data,indent=2))

if __name__=='__main__':main()
