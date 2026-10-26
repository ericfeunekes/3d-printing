from pathlib import Path
import importlib.util,sys,json,math
import numpy as np,trimesh
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
spec=importlib.util.spec_from_file_location('ancillary',HERE/'model_ancillary.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
spec=importlib.util.spec_from_file_location('usage',ROOT/'usage-study/check_usage.py');u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
meshes,_,_=u.core();obstacles={'top_rail':meshes[3],'front_shell':meshes[6]}
native=trimesh.load_mesh(a.SOURCE/'obj_2_Sight2.STEP.stl')
hinge=np.array([0.,109.31366559,26.76465696]);pivot=[112.13520,126.9764,7.86755]
choices={'original_Z_reversed':[[0,1,0],[1,0,0],[0,0,-1]],'candidate_Z_forward':[[0,-1,0],[1,0,0],[0,0,1]]}
rows=[]
for name,r in choices.items():
    angles=[0] if name.startswith('original') else [0,15,30,45,60,75,90]
    for angle in angles:
        matrix=a.around_x(hinge,math.radians(angle))@a.pose(r,pivot,hinge)
        m=native.copy();m.apply_transform(matrix)
        pts=u.deterministic_points(m,1800)
        checks=u.sampled_clearance(pts,obstacles)
        row={'pose_choice':name,'fold_angle_degrees':angle,'matrix':matrix.tolist(),'checks':checks,'hinge_exclusion':'None; complete selected sight samples checked'}
        rows.append(row);print(name,angle,checks,flush=True)
(HERE/'sight-pose-checks.json').write_text(json.dumps(rows,indent=2)+'\n')
