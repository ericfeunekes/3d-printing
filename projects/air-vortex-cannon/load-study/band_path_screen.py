"""Unit-load statics for the observed two-front/two-rear elastic topology.

No rubber-band spring constant, rest length or actual force is inferred.
Junction positions are sensitivity assumptions, not equilibrium predictions.
"""
from pathlib import Path
import json,math

HERE=Path(__file__).resolve().parent
half_spacing=72.730
front_z=4.050995
separations=[60.,100.,160.,240.]
manual_forces=[1.,5.,10.,20.,40.]
rows=[]
for d in separations:
    length=math.hypot(half_spacing,d)
    cos=d/length
    for F in manual_forces:
        front_tension=F/(2*cos)
        rows.append({'front_plane_to_junction_mm_assumed':d,'axial_resultant_N_assumed':F,
                     'front_branch_tension_N':front_tension,
                     'front_anchor_axial_component_N_each':F/2,
                     'front_anchor_inward_radial_component_N_each':F*half_spacing/(2*d),
                     'rear_parallel_band_tension_N_each':F/2,
                     'front_ligament_area_required_at_assumed_4MPa_mm2':front_tension/4,
                     'central_loop_area_required_at_assumed_4MPa_mm2':F/4})
r={'status':'Conditional branch-force geometry, not rubber-band force or capacity prediction',
   'observed_topology':'Two opposite front annulus anchors to a central junction, then two parallel bands to moving rear cap',
   'evidence':{'url':'https://www.youtube.com/watch?v=NKO3LCNGTJY',
               'video_stages':'3:03 front anchors; 3:23 second pair joined by carabiner; 3:48 junction; 4:08-4:18 central cap routing',
               'front_anchor_points_xyz_mm':[[half_spacing,0,front_z],[-half_spacing,0,front_z]],
               'source':'ancillary_motion mesh/video reconstruction'},
   'assumptions':['Symmetric anchors and centered massless junction',
                  'Rear pair locally axial and equally loaded',
                  'F is the axial elastic resultant, conservatively set equal to the entire manual-force scenario',
                  'Film tension may share manual force; no sharing benefit is credited',
                  'Junction distance and band rest lengths/stiffness are not measured',
                  '4 MPa is an analyst-selected nominal screening stress, not a printed-part allowable'],
   'formulas':{'front_tension':'F * sqrt(a^2+d^2) / (2*d)',
               'front_radial_component':'F*a/(2*d)','rear_parallel_each':'F/2'},
   'cases':rows}
(HERE/'band-path-results.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps([x for x in rows if x['axial_resultant_N_assumed']==40],indent=2))
