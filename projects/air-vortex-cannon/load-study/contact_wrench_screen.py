"""Frictionless finite-contact static equilibrium: conditional design screen.

This LP establishes whether *a* nonnegative normal-reaction set can balance a
specified wrench inside analyst-selected nominal stress limits. It does not
predict stiffness-selected load sharing or establish physical capacity. The
normal capture faces presume the shoulder/head/nut/pad positively trap the
shell and rail after the modeled capture play has closed.
"""
from pathlib import Path
import json,math
import numpy as np
from scipy.optimize import linprog

HERE=Path(__file__).resolve().parent
P=json.loads((HERE/'results.json').read_text())['input_parameters']
ASSEMBLY=json.loads((HERE.parent/'assembly-study/core-assembly.json').read_text())
JOINTS=sorted([j for j in ASSEMBLY['joints'] if j['side']==-1],key=lambda j:j['inner_surface_center_mm'][2])

def contact_set(indices,wall_t,pad_t):
    contacts=[];normal_groups=[]
    width=P['slot_width_mm'];length=P['slot_axial_length_mm']
    bearing_w=P['key_bearing_width_mm'];bearing_l=P['key_bearing_length_mm']
    pad_w=P['adapter_circumferential_width_mm'];pad_l=P['adapter_axial_length_mm']
    stress=P['assumed_nominal_stress_screen_MPa']
    pad_area=(pad_w*pad_l-width*length)*P['effective_contact_area_fraction_assumed']
    bridge_limit=stress*2*(pad_l-P['pad_central_hole_mm'])*pad_t**2/(3*width)
    for idx in indices:
        j=JOINTS[idx]
        p=np.array(j['inner_surface_center_mm']);n=np.array(j['outward_axis']);t=np.array(j['axial_tangent']);u=np.array(j['cross_tangent'])
        normal_ids=[]
        # Separate axial and cross-key bearing faces; no tangential friction.
        for sign in [-1,1]:
            for offset in [-width/4,width/4]:
                contacts.append({'joint':idx,'kind':'axial_key_bearing','point':p+sign*length/2*t+offset*u,
                                 'normal':sign*t,'assumed_force_limit_N':stress*wall_t*bearing_w/2})
            for offset in [-length/4,length/4]:
                contacts.append({'joint':idx,'kind':'cross_key_bearing','point':p+sign*width/2*u+offset*t,
                                 'normal':sign*u,'assumed_force_limit_N':stress*wall_t*bearing_l/2})
            # Four equivalent bearing patches on each opposed capture face.
            # This is a reduced rigid-pad model, not recovered contact pressure.
            for a in [-pad_w/4,pad_w/4]:
                for b in [-pad_l/4,pad_l/4]:
                    normal_ids.append(len(contacts))
                    contacts.append({'joint':idx,'kind':'positive_normal_capture','point':p+a*u+b*t,
                                     'normal':sign*n,'assumed_force_limit_N':stress*pad_area/4})
        normal_groups.append({'joint':idx,'ids':normal_ids,'assumed_bridge_force_limit_N':bridge_limit})
    return contacts,normal_groups

def solve(indices,loads,wall_t,pad_t):
    contacts,groups=contact_set(indices,wall_t,pad_t)
    A=np.array([np.r_[c['normal'],np.cross(c['point'],c['normal'])] for c in contacts]).T
    W=sum((np.r_[f,np.cross(p,f)] for p,f in loads),start=np.zeros(6))
    # Conditioning only: moments remain Nmm in returned evidence.
    scale=np.array([1,1,1,.01,.01,.01])
    aeq=np.column_stack([A,np.zeros(6)])*scale[:,None]
    beq=-W*scale
    # Minimize the largest assumed force-limit fraction. A tiny force penalty
    # disfavours gratuitous balanced preload without changing the screen.
    n=len(contacts)
    c=np.r_[np.full(n,1e-8),1.]
    aub=np.zeros((n+len(groups),n+1));bub=np.zeros(len(aub))
    for i,contact in enumerate(contacts):
        aub[i,i]=1;aub[i,-1]=-contact['assumed_force_limit_N']
    for i,g in enumerate(groups,start=n):
        aub[i,g['ids']]=1;aub[i,-1]=-g['assumed_bridge_force_limit_N']
    opt=linprog(c,A_ub=aub,b_ub=bub,A_eq=aeq,b_eq=beq,bounds=[(0,None)]*(n+1),method='highs')
    if not opt.success:
        return {'solver_success':False,'message':opt.message}
    forces=opt.x[:-1];res=A@forces+W
    assert np.max(np.abs(res[:3]))<1e-6 and np.max(np.abs(res[3:]))<1e-4
    joint_forces={str(i):[0,0,0] for i in indices}
    used=[]
    for force,contact in zip(forces,contacts):
        joint_forces[str(contact['joint'])]=(np.array(joint_forces[str(contact['joint'])])+force*contact['normal']).tolist()
        if force>1e-5:
            used.append({'joint':contact['joint'],'kind':contact['kind'],'force_N':float(force),
                         'point_xyz_mm':contact['point'].tolist(),'normal_xyz':contact['normal'].tolist()})
    return {'solver_success':True,'minimum_possible_assumed_limit_fraction':float(opt.x[-1]),
            'meaning':'Optimistic statics feasibility; not actual load sharing, a safety factor or physical capacity',
            'force_balance_residual_N':res[:3].tolist(),'moment_balance_residual_Nmm':res[3:].tolist(),
            'joint_resultant_reactions_xyz_N':joint_forces,'used_normal_contacts':used}

weight=np.array([0,-P['body_mass_kg']*P['gravity_m_s2'],0])
com=np.array([0,*P['body_com_yz_mm']]);pull_point=np.array([0,0,P['rear_rim_z_mm']+P['normal_pull_travel_mm']])
cases=[('unit_axial',np.array([0.,0.,1.]),False),('unit_side',np.array([1.,0.,0.]),False),
       ('manual20N_plus_1g',np.array([0.,0.,20.]),True),
       ('manual20N_plus_side2N_plus_1g',np.array([2.,0.,20.]),True),
       ('transient40N_plus_side4N_plus_1g',np.array([4.,0.,40.]),True),
       ('transient40N_minus10deg_plus_side4N_plus_1g',np.array([4.,-40*math.sin(math.radians(10)),40*math.cos(math.radians(10))]),True),
       ('transient40N_plus10deg_plus_side4N_plus_1g',np.array([4.,40*math.sin(math.radians(10)),40*math.cos(math.radians(10))]),True)]
results=[]
for name,force,with_weight in cases:
    loads=[(pull_point,force)]
    if with_weight:loads.append((com,weight))
    for group,indices in P['load_groups'].items():
        for wall_t in [1.,P['selected_continuous_wall_thickness_mm']]:
            out=solve(indices,loads,wall_t,P['selected_pad_thickness_mm'])
            results.append({'case':name,'group':group.replace('_equal_stiffness','_available'),'wall_thickness_mm':wall_t,
                            'pad_thickness_mm':P['selected_pad_thickness_mm'],**out})

# Necessary torsional moment about the lower connector row for a side force.
pts=np.array([j['inner_surface_center_mm'] for j in JOINTS]);centre=pts.mean(axis=0)
_,_,vt=np.linalg.svd(pts-centre);row=vt[0]
if row[2]<0:row=-row
M=np.cross(pull_point-centre,np.array([1.,0.,0.]))
torque_per_sideN=abs(float(M@row))
summary={'status':'CONDITIONAL 3D STATIC CONTACT SCREEN — not strength proof',
         'model':'Rigid-body + frictionless signed bearing faces with analyst-selected capacities; best-balanced LP solution',
         'selected_geometry':{'wall_mm':P['selected_continuous_wall_thickness_mm'],'pad_mm':P['selected_pad_thickness_mm'],
                              'slot_mm':[P['slot_axial_length_mm'],P['slot_width_mm']],
                              'pad_mm_extent':[P['adapter_axial_length_mm'],P['adapter_circumferential_width_mm']]},
         'necessary_side_pull_torsion':{'row_axis':row.tolist(),'row_reference_point_mm':centre.tolist(),
                                        'moment_about_row_per_N_side_pull_Nmm':torque_per_sideN,
                                        'single_contact_couple_force_per_N_side_pull_at_8mm_lever_N':torque_per_sideN/8},
         'critical_limits':['Feasible equilibrium does not prove stiffness will select the displayed reaction set',
                            'Assumed nominal stress limits are not validated FDM allowables',
                            'Normal capture contacts assume final shoulder/head/nut/washer geometry positively captures the stack',
                            'Capacities do not resolve local singular stresses, plastic creep, layer adhesion, fatigue or dynamic impact',
                            'No friction or screw preload is used to resist in-plane shear'],
         'cases':results}
(HERE/'contact-wrench-results.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'side_pull_torsion':summary['necessary_side_pull_torsion'],
                  'screen_fractions':[{'case':r['case'],'group':r['group'],'wall_mm':r['wall_thickness_mm'],
                                       'fraction':r.get('minimum_possible_assumed_limit_fraction'),'success':r['solver_success']} for r in results]},indent=2))
