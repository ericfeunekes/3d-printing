"""Representative shoulder-stop joint to check nominal stack arithmetic.

The grip G=6mm below is intentionally illustrative. Final parent assembly
must replace it with actual six-site recovered stacks before acceptance.
"""
from pathlib import Path
import json
import build123d as b
from build_options import make_inner_adapter, make_outer_adapter,make_shoulder_hardware_reference

HERE=Path(__file__).resolve().parent
OUT=HERE/'shoulder-stack-study';OUT.mkdir(exist_ok=True)
R=110.;K=.09616;G=6.;L=16.;BASE=4.;INNER_WASHER=1.2;GAP=.25
underhead=-BASE-INNER_WASHER
shoulder_end=underhead+L
outer_thickness=shoulder_end-GAP-G
assert outer_thickness>=2.,'Use a longer shoulder or revise stack, not a thin outer adapter.'
inner=make_inner_adapter(R,K,G,key_length=15.,key_width=7.4,flange_length=30.,flange_width=22.,
    base_thickness=BASE,hole_diameter=5.4,capture_gap=GAP,key_end_z=G-.1)
outer=make_outer_adapter(G,flange_length=30.,flange_width=22.,hole_diameter=5.4,
    capture_gap=GAP,thickness=outer_thickness,base_z=G)
h=make_shoulder_hardware_reference(L)
shapes={'inner-adapter':inner,'outer-adapter':outer,
    'shoulder-bolt-reference':b.Pos(0,0,underhead)*h['shoulder-bolt-reference'],
    'inner-M5-washer-reference':b.Pos(0,0,underhead)*h['inner-M5-wide-washer-reference'],
    'outer-M4-washer-reference':b.Pos(0,0,shoulder_end)*h['outer-M4-wide-washer-reference'],
    'M4-nyloc-envelope-reference':b.Pos(0,0,shoulder_end+1)*h['M4-nyloc-envelope-reference']}
records=[]
for name,shape in shapes.items():
    b.export_step(shape,OUT/f'{name}.step');b.export_stl(shape,OUT/f'{name}.stl',tolerance=.025)
    bb=shape.bounding_box()
    records.append({'name':name,'valid':shape.is_valid,'solids':len(shape.solids()),
        'bounds_mm':[[bb.min.X,bb.min.Y,bb.min.Z],[bb.max.X,bb.max.Y,bb.max.Z]],'volume_mm3':shape.volume})
summary={'status':'Representative local stack only, NOT final six-site assembly',
    'frame':'X=cone-generator tangent toward larger radius,Y=circumferential tangent,Z=outwardnormal; inner shell contact datumZ0',
    'grip_mm_assumed':G,'shoulder_length_mm':L,'base_mm':BASE,'inner_washer_mm':INNER_WASHER,
    'nominal_capture_gap_mm':GAP,'outer_adapter_thickness_mm':outer_thickness,
    'underhead_z_mm':underhead,'shoulder_end_z_mm':shoulder_end,
    'key_end_z_mm':G-.1,'outer_adapter_base_z_mm':G,
    'nyloc_end_z_mm':shoulder_end+1+5,'nominal_thread_tip_z_mm':shoulder_end+8,
    'nominal_thread_beyond_nut_mm':2.,
    'minimum_outer_adapter_mm_assumed':2.,
    'max_G_for_16mm_shoulder_at_min_outer_mm':L-INNER_WASHER-BASE-GAP-2.,
    'hardware_length_tolerance_plus_mm_from_datasheet':.25,
    'limits':['No shoulder tightening torque rating inferred',
        'Washer thickness/FDM deviations not supplied; actual capture clearance requires measurements',
        'Thread and nut use conservative reference envelopes, not engaged thread simulation',
        'No numeric printed strength or life conclusion',
        'No whole-cannon collision or motion proof here'],
    'parts':records}
(OUT/'stack.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='parts'},indent=2))
