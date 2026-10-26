"""Conditional, unit-normalized load-path screening for a manual air-only toy.

This is not a force rating. Equilibrium is solved exactly for an explicitly
assumed planar rigid-body/point-joint model. Local stresses are nominal
screening demands, not recovered 3D contact stresses or printed capacity.
"""
from pathlib import Path
import json
import math
import os
import hashlib
os.environ.setdefault('MPLCONFIGDIR', '/tmp/vortex-load-mpl')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
P = json.loads((HERE/'parameters.json').read_text())
assembly_path=HERE.parent/'assembly-study/core-assembly.json'
if assembly_path.exists():
    assembly=json.loads(assembly_path.read_text())
    lower=sorted([j for j in assembly['joints'] if j['side']==-1],key=lambda j:j['inner_surface_center_mm'][2])
    P['joint_centres_yz_mm']=[j['inner_surface_center_mm'][1:] for j in lower]
    P['joint_geometry_status']='Recovered nominal mesh assembly; '+ '; '.join(assembly['assumptions'])
    P['cone_angle_deg']=assembly['cone_half_angle_deg']
    P['rear_rim_z_mm']=assembly['rear_shell_end_mm']
    P['assembly_source_json_sha256']=hashlib.sha256(assembly_path.read_bytes()).hexdigest()

def wrench_yz(force_yz, point_yz):
    fy,fz=force_yz
    y,z=point_yz
    return np.array([fy,fz,y*fz-z*fy],dtype=float)

def reactions(points_yz, external_wrench):
    """[Fy,Fz] per joint, minimum-norm/equal point-stiffness hypothesis."""
    points=np.asarray(points_yz,dtype=float)
    a=np.zeros((3,2*len(points)))
    for i,(y,z) in enumerate(points):
        a[0,2*i]=1
        a[1,2*i+1]=1
        a[2,2*i]=-z
        a[2,2*i+1]=y
    q=np.linalg.pinv(a) @ (-np.asarray(external_wrench))
    residual=a@q+external_wrench
    # This checks numerical equilibrium, not validity of the support model.
    assert np.max(np.abs(residual))<1e-7
    return q.reshape(-1,2),residual

def case(name,pull_N=0,gravity_factor=0,pull_angle_deg=0):
    pull_point=np.array([0,P['rear_rim_z_mm']+P['normal_pull_travel_mm']])
    # Angle is in Y/Z plane; optional sensitivity, not a measured hand path.
    angle=math.radians(pull_angle_deg)
    pull=np.array([pull_N*math.sin(angle),pull_N*math.cos(angle)])
    weight=np.array([-P['body_mass_kg']*P['gravity_m_s2']*gravity_factor,0])
    loads=[{'name':'manual_pull','force_yz_N':pull.tolist(),'point_yz_mm':pull_point.tolist()},
           {'name':'gravity','force_yz_N':weight.tolist(),'point_yz_mm':P['body_com_yz_mm']}]
    w=sum((wrench_yz(x['force_yz_N'],x['point_yz_mm']) for x in loads),start=np.zeros(3))
    hand=P['hand_grip_yz_mm']
    hand_moment=-sum(wrench_yz(x['force_yz_N'],np.array(x['point_yz_mm'])-hand)[2] for x in loads)
    groups=[]
    for key,ids in P['load_groups'].items():
        pts=np.asarray(P['joint_centres_yz_mm'])[ids]
        q,residual=reactions(pts,w)
        groups.append({'name':key,'joint_indices':ids,'reaction_yz_N':q.tolist(),
                       'resultant_N':np.linalg.norm(q,axis=1).tolist(),
                       'peak_resultant_N':float(np.linalg.norm(q,axis=1).max()),
                       'force_moment_balance_residual':residual.tolist()})
    return {'name':name,'pull_N':pull_N,'gravity_factor':gravity_factor,'pull_angle_deg':pull_angle_deg,
            'external_loads':loads,'external_wrench_Fy_Fz_Mx':w.tolist(),
            'hand_reaction_force_yz_N':(-w[:2]).tolist(),'hand_required_moment_Nmm':float(hand_moment),
            'groups':groups}

cases=[case('unit_axial_pull',1),case('hold_1g',gravity_factor=1),case('hold_2g_sensitivity',gravity_factor=2),
       case('hold_inverted_1g',gravity_factor=-1)]
cases += [case(f'manual_pull_{force:g}N_plus_1g',force,1) for force in P['manual_force_examples_N']]
cases += [case('transient_example_2x_20N_plus_1g',max(P['manual_force_examples_N'])*P['transient_multiplier_example'],1),
          case('manual_20N_10deg_offaxis_plus_1g',20,1,10),
          case('manual_20N_minus10deg_offaxis_plus_1g',20,1,-10),
          case('transient_40N_10deg_offaxis_plus_1g',40,1,10),
          case('transient_40N_minus10deg_offaxis_plus_1g',40,1,-10),
          case('manual_20N_plus_inverted_1g',20,-1),
          case('transient_40N_plus_inverted_1g',40,-1)]

demands=[]
ca=math.cos(math.radians(P['cone_angle_deg']))
sa=math.sin(math.radians(P['cone_angle_deg']))
for c in cases:
    for g in c['groups']:
        for i,(fy,fz) in zip(g['joint_indices'],g['reaction_yz_N']):
            # Bottom-cone outward normal [0,-cos(a),-sin(a)] and rearward
            # tangent [0,-sin(a),cos(a)], recovered from source shell faces.
            normal=abs(-ca*fy-sa*fz)
            axial=abs(-sa*fy+ca*fz)
            shell=[]
            for t in P['shell_thickness_sensitivity_mm']:
                bearing=axial/(t*P['key_bearing_width_mm'])
                net=axial/(t*(P['adapter_circumferential_width_mm']-P['slot_width_mm']))
                tear={str(e):axial/(2*e*t) for e in P['edge_ligament_sensitivity_mm']}
                shell.append({'effective_continuous_wall_thickness_mm':t,
                              'nominal_slot_edge_bearing_MPa':bearing,
                              'nominal_net_section_MPa':net,
                              'nominal_two_ligament_shear_out_MPa_by_edge_distance_mm':tear,
                              'bearing_over_assumed_stress_screen':bearing/P['assumed_nominal_stress_screen_MPa']})
            adapter=[]
            # One-way simply-supported bridge over the narrow slot; small-
            # deflection beam idealization, not 3D curved-pad contact FEA.
            span=P['slot_width_mm'];b=P['adapter_axial_length_mm']-P['pad_central_hole_mm']
            for t in P['adapter_thickness_sensitivity_mm']:
                sigma=3*normal*span/(2*b*t*t)
                delta={str(E):normal*span**3/(4*E*b*t**3) for E in P['elastic_modulus_sensitivity_MPa']}
                adapter.append({'pad_thickness_mm':t,'nominal_bridge_bending_MPa':sigma,
                                'elastic_deflection_mm_by_assumed_E_MPa':delta,
                                'bending_over_assumed_stress_screen':sigma/P['assumed_nominal_stress_screen_MPa']})
            contact_area=(P['adapter_axial_length_mm']*P['adapter_circumferential_width_mm']-
                          P['slot_width_mm']*P['slot_axial_length_mm'])*P['effective_contact_area_fraction_assumed']
            sigma_bolt=normal/P['bolt_tensile_stress_area_mm2']
            tau_bolt=axial/P['bolt_shear_area_mm2']
            demands.append({'case':c['name'],'group':g['name'],'joint_index':i,
                            'normal_force_demand_N':normal,'in_plane_axial_force_demand_N':axial,
                            'world_force_yz_N':[fy,fz],
                            'shell_screens':shell,'pad_screens':adapter,
                            'average_pad_pressure_MPa_assumed_contact_area':normal/contact_area,
                            'bolt_tensile_stress_demand_MPa':sigma_bolt,
                            'bolt_root_shear_stress_demand_MPa':tau_bolt,
                            'bolt_von_mises_demand_MPa':math.sqrt(sigma_bolt**2+3*tau_bolt**2)})

# Force divided by rear opening area is only a normalization. It is not a
# pressure/time prediction for a flexible membrane, nozzle or actual pulse.
area=math.pi*P['rear_internal_radius_mm']**2
normalizations=[{'manual_force_N':F,'F_over_rear_area_Pa':F/(area*1e-6)} for F in P['manual_force_examples_N']]

results={'status':'CONDITIONAL ANALYSIS — not physical proof or a load rating',
         'input_parameters':P,'cases':cases,'local_demands':demands,
         'equivalent_pressure_normalization_only':normalizations,
         'proof_scope':{'established':'Algebraic force/moment equilibrium and nominal stress demand for stated geometry, supports and loads',
                        'not_established':['Actual load sharing','Printed strength or fatigue','Bolt/nut retention and preload',
                                           'Contact pressure distribution','Full 3D contact or shell buckling',
                                           'Actual pulse pressure, ring coherence or range','Impact/drop resistance']}}
(HERE/'results.json').write_text(json.dumps(results,indent=2)+'\n')
max_normal=max(d['normal_force_demand_N'] for d in demands)
washer_beams=[]
for name,D,di,t in [('nominal',12.,4.3,1.6),('worst_dimensions',11.3,4.48,1.3),('thin_comparison',12.,4.3,1.)]:
    b=D-di;span=8.;E=200000.
    washer_beams.append({'case':name,'OD_mm':D,'ID_mm':di,'thickness_mm':t,'normal_N':max_normal,
                         'nominal_strip_bending_MPa':3*max_normal*span/(2*b*t*t),
                         'linear_strip_deflection_mm':max_normal*span**3/(4*E*b*t**3)})
(HERE/'outer-washer-beam-screen.json').write_text(json.dumps({'status':'One-way net-width strip proxy, not 3D plate contact proof',
                                                             'support_gap_mm':8,'E_MPa_assumed':200000,'cases':washer_beams},indent=2)+'\n')

# Simple physical visualizations derived from the same solved reaction cases.
fig,axes=plt.subplots(1,2,figsize=(12,4.7),facecolor='white')
colors=['#40758b','#d49845','#a64c51']
for color,(group,ids) in zip(colors,P['load_groups'].items()):
    cs=[c for c in cases if c['name'].startswith('manual_pull_')]
    x=[c['pull_N'] for c in cs]
    y=[next(g['peak_resultant_N'] for g in c['groups'] if g['name']==group) for c in cs]
    axes[0].plot(x,y,'o-',color=color,label=group.replace('lower_','').replace('_',' '))
axes[0].set_xlabel('Assumed manual force (N)');axes[0].set_ylabel('Peak joint resultant demand (N)')
axes[0].set_title('Load-sharing sensitivity · includes assumed 0.6 kg weight')
axes[0].legend(fontsize=8);axes[0].grid(alpha=.2)
worst=max(demands,key=lambda d:d['normal_force_demand_N'])
worst_axial=max(demands,key=lambda d:d['in_plane_axial_force_demand_N'])
for wall in P['shell_thickness_sensitivity_mm']:
    axial=worst_axial['in_plane_axial_force_demand_N']
    axes[1].bar(str(wall),axial/(wall*P['key_bearing_width_mm']),color='#40758b',alpha=.8)
axes[1].axhline(P['assumed_nominal_stress_screen_MPa'],ls='--',color='#a64c51',label='Assumed screening threshold (not allowable)')
axes[1].set_xlabel('Effective continuous wall thickness at slot (mm)');axes[1].set_ylabel('Nominal axial bearing demand (MPa)')
axes[1].set_title('Local section sensitivity · peak analyzed tangential load')
axes[1].legend(fontsize=7);axes[1].grid(axis='y',alpha=.2)
fig.suptitle('Conditional load study — assumptions, not measured limits',fontsize=14)
fig.tight_layout();fig.savefig(HERE/'load-sensitivity.png',dpi=160);plt.close(fig)

# Group-specific force arrows for parent CAD/viewer integration, not another
# independent geometry owner or asserted assembly registration.
arrow_case=next(c for c in cases if c['name']=='transient_example_2x_20N_plus_1g')
arrows=[]
for g in arrow_case['groups']:
    for i,(fy,fz) in zip(g['joint_indices'],g['reaction_yz_N']):
        y,z=P['joint_centres_yz_mm'][i]
        arrows.append({'group':g['name'],'joint_index':i,'point_xyz_mm':[0,y,z],
                       'reaction_xyz_N':[0,fy,fz]})
(HERE/'load-vectors.json').write_text(json.dumps({'case':arrow_case['name'],'status':'assumed statics arrows, not measured','arrows':arrows},indent=2)+'\n')
print(json.dumps({'case_peak_resultants_N':{c['name']:{g['name']:g['peak_resultant_N'] for g in c['groups']} for c in cases},
                  'worst_local_demand':{k:worst[k] for k in ['case','group','joint_index','normal_force_demand_N','in_plane_axial_force_demand_N']},
                  'pressure_normalization_only':normalizations},indent=2))
