"""Recommended joint CAD and all-six installed hardware poses, mm.

Original parts remain separate evidence. This is a conditional engineering
prototype, not a tested toy. Purchased threads are dimensional envelopes.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import trimesh
import build123d as b
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'joint-study'))
from build_options import _clean,make_shoulder_hardware_reference

SPEC={'adapter_base_mm':[30.,22.,4.6],'key_mm':[15.,7.4,13.4],
      'bore_diameter_mm':5.4,'collar_inner_depth_mm':2.5,
      'shoulder_diameter_mm':5.,'shoulder_length_mm':20.,
      'inner_washer_mm':[5.3,15.,1.2],'outer_washer_mm':[4.3,12.,1.6],
      'nut_mm':{'across_flats':7.,'height':5.},
      'study_assumed_adapter_thickness_error_mm':.15,
      'study_assumed_collar_position_error_mm':.15,
      'study_assumed_rail_stack_error_mm':.10,
      'study_assumed_inner_washer_thickness_error_mm':.10,
      'manufacturer_shoulder_length_tolerance_mm':[0,.25]}

def make_adapter(base_thickness=None):
    if base_thickness is None:base_thickness=SPEC['adapter_base_mm'][2]
    base=b.Pos(0,0,-base_thickness)*b.extrude(b.RectangleRounded(30.,22.,4.),amount=base_thickness)
    key=b.Pos(0,0,-.1)*b.extrude(b.RectangleRounded(15.,7.4,3.5),amount=13.5)
    hole=b.Pos(0,0,-base_thickness-1)*b.Cylinder(2.7,base_thickness+15.4,
      align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))
    return _clean(base+key-hole)

def export(shape,path):
    b.export_step(shape,path.with_suffix('.step'))
    b.export_stl(shape,path.with_suffix('.stl'),tolerance=.025,angular_tolerance=.12)
    mesh=trimesh.load_mesh(path.with_suffix('.stl'))
    assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1
    return mesh

def main():
    out=HERE/'parts';out.mkdir(exist_ok=True)
    base_t=SPEC['adapter_base_mm'][2]
    adapter=make_adapter(base_t)
    a=export(adapter,out/'keyed-adapter-local')
    # Selective print geometry: flat base on bed, bore vertical, 18mm totalheight.
    printshape=b.Pos(15.,11.,base_t)*adapter
    export(printshape,out/'keyed-adapter-print')
    hardware=make_shoulder_hardware_reference(20.)
    # DIN7349 heavy washer replaces the 1mm wide-washer study reference.
    hardware['outer-M4-wide-washer-reference']=_clean(
      b.Cylinder(6.,1.6,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))-
      b.Cylinder(2.15,1.6,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN)))
    refs={name:export(shape,out/name) for name,shape in hardware.items()}
    core=json.loads((ROOT/'assembly-study/core-assembly.json').read_text())
    posed=HERE/'assembled-joints';posed.mkdir(exist_ok=True)
    joints=[];components=[]
    for j in core['joints']:
        normal=np.array(j['outward_axis']);center=np.array(j['inner_surface_center_mm'])
        M=np.eye(4);M[:3,:3]=np.column_stack([j['axial_tangent'],j['cross_tangent'],normal])
        M[:3,3]=center-2.5*normal # New flat landing on continuous collar.
        G=float(j['nominal_grip_stack_mm'])+2.5
        H=-base_t-SPEC['inner_washer_mm'][2] # bolt under-head plane in adapter frame
        shoulder_end=H+20.
        gap=shoulder_end-G
        assumed_error=.15+.15+.10+.10
        bounds=[gap-assumed_error,gap+assumed_error+.25]
        assert gap>0 and bounds[0]>0
        assert 13.4<G and G-13.4<.25
        placements={'keyed-adapter-local':(a,0.),
          'shoulder-bolt-reference':(refs['shoulder-bolt-reference'],H),
          'inner-M5-wide-washer-reference':(refs['inner-M5-wide-washer-reference'],H),
          'outer-M4-wide-washer-reference':(refs['outer-M4-wide-washer-reference'],shoulder_end),
          'M4-nyloc-envelope-reference':(refs['M4-nyloc-envelope-reference'],shoulder_end+1.6)}
        for name,(mesh,localz) in placements.items():
            T=M.copy();T[:3,3]+=normal*localz
            p=mesh.copy();p.apply_transform(T)
            filename=j['id']+'--'+name+'.stl';p.export(posed/filename)
            components.append({'joint':j['id'],'name':name,'path':str((posed/filename).relative_to(ROOT)),
              'matrix_local_to_assembly':T.tolist(),'material':'printed PETG candidate' if name.startswith('keyed') else 'purchased metal reference',
              'manufactured_here':name.startswith('keyed')})
        joints.append({'id':j['id'],'surface_center_mm':center.tolist(),'adapter_local_to_assembly':M.tolist(),
          'outward_axis':normal.tolist(),'stock_grip_mm':j['nominal_grip_stack_mm'],'reinforced_grip_mm':G,
          'bolt_underhead_local_z_mm':H,'head_inner_face_local_z_mm':H-4,
          'outer_washer_local_z_mm':shoulder_end,'nut_outer_face_local_z_mm':shoulder_end+1.6+5,
          'nominal_capture_gap_mm':gap,'conditional_capture_gap_bounds_mm':bounds,
          'gap_basis':'Dominant outer-rail datum-plane separation, not actual washer-footprint first-contact travel. Independent footprint probes add about .05..13mm depending on washer OD; see capture-contact-review.json.',
          'key_recess_at_outer_rail_mm':G-13.4,
          'thread_beyond_nut_nominal_mm':8-1.6-5,
          'capture_basis':'Head/M5washer and M4washer/nut are wider than openings; outerM4washerID4.3 is smaller than5mmshoulder, providing metalstop. No clamp-friction credit.',
          'limits':'Hardware undercuts/chamfers, tolerance/torque, FDM fit and actualnutlocking require physical verification.'})
    record={'name':'Recommended Revision B conditional prototype','units':'mm','spec':SPEC,
      'source_datum_revision':core.get('datum_revision'),'joints':joints,'components':components,
      'printed_adapter_quantity':6,'unique_adapter_geometry_count':1,
      'removed_source_pin_ids':[11,12,13,14,15,16],
      'modified_shell_ids':[6,8,7],
      'unmodified_source_ids':[1,2,3,4,5,9,10,17],
      'sources':{'shoulder_bolt':'https://www.elesa-ganter.hr/siteassets/PDF/EN/ISO%207379.pdf',
        'outer_washer':'https://www.accu.co.uk/metric-flat-washers/63172-HDTW-M4-A2',
        'inner_washer':'https://www.ruuvikeskus.fi/attachments/h7cpz.pdf',
        'nyloc':'https://www.tme.eu/Document/b2162b4e06623b32cc382f0f3f1ca4a6/B4_BN161.pdf'},
      'claim_boundary':'Geometric capture under stated dimensional assumptions; not proof of actual printed strength, fatigue, friction, nutlocking, seal or airflow performance.',
      'metal_reference_meshes_not_to_print':list(hardware)}
    (HERE/'recommended-assembly.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'adapters':6,'metal_references':24,'joint_gaps':[(x['id'],x['nominal_capture_gap_mm']) for x in joints]},indent=2))

if __name__=='__main__':main()
