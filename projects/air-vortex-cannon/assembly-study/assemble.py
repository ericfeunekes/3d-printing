"""Full 17-piece nominal stock assembly plus explicit flexible-part studies.

Rigid source meshes are placed by recovered mating datums. Film/bands are
schematics and travel inputs are assumed study values, never proof of rating.
"""
from pathlib import Path
import sys,json
import numpy as np
import trimesh
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(ROOT/'ancillary-study'))
from recover_core import core,FILES
import model_ancillary as ancillary

def load_assembly(stroke=0.0,sight_fold_degrees=0.0):
    meshes,transforms,joints=core()
    rear_plane=meshes[7].bounds[1,2]
    poses=ancillary.make_transforms(rear_plane=rear_plane,stroke=stroke,sight_fold_degrees=sight_fold_degrees)
    # Respect the recovered top-rail hinge rather than any rounded old pose.
    hinge=(transforms[3]@np.array([353.56305,166.541115,12.5,1]))[:3]
    # model_ancillary exports its currently chosen hinge; recover its actual
    # rigid pivot from the transformed original datum before translating it.
    sight_pose=np.array(poses['obj_2_Sight2.STEP.stl']['matrix'])
    actual_hinge=(sight_pose@np.array([112.13520,126.9764,7.86755,1]))[:3]
    adjustment=np.eye(4);adjustment[:3,3]=hinge-actual_hinge
    for name,row in poses.items():
        i=int(name.split('_')[1]);M=np.array(row['matrix'])
        if i in [1,2]:M=adjustment@M
        row['matrix']=M.tolist()
        m=trimesh.load_mesh(ROOT/'source/egordv'/name);m.apply_transform(M)
        meshes[i]=m;transforms[i]=M
    assert set(meshes)==set(range(1,18))
    assert all(abs(np.linalg.det(M[:3,:3])-1)<1e-9 for M in transforms.values())
    metadata={'units':'mm','rigid_source_part_count':17,'stroke_study_mm':stroke,
              'sight_fold_study_deg':sight_fold_degrees,'rear_shell_plane_mm':rear_plane,
              'source_to_assembly':{str(i):M.tolist() for i,M in transforms.items()},
              'joints':joints,'ancillary_evidence':poses,
              'hinge_world_mm':hinge.tolist(),'elastic_graph':ancillary.band_graph(rear_plane=rear_plane,stroke=stroke),
              'claim_boundary':'Nominal recovered assembly; flexible snaps, film/elastic behavior, printed fit and actual strength unverified'}
    return meshes,transforms,metadata

def export_scene(stroke=0,sight_fold_degrees=0):
    meshes,T,meta=load_assembly(stroke,sight_fold_degrees)
    scene=trimesh.Scene()
    for i,m in meshes.items():
        m=m.copy()
        m.visual.face_colors=([45,111,168,255] if i in [6,7,8] else
                              [53,175,184,255] if i in [3,4] else [125,144,157,255])
        scene.add_geometry(m,node_name=FILES[i].name)
    film=ancillary.membrane_mesh(rear_plane=meta['rear_shell_plane_mm'],stroke=stroke)
    film.visual.face_colors=[160,190,205,100]
    scene.add_geometry(film,node_name='film-study-not-manufactured-part')
    # glTF expects metre dimensions; native mesh/CAD/JSON remain mm.
    scene.apply_scale(.001)
    return scene,meta

def main():
    scene,meta=export_scene()
    (HERE/'full-stock-assembly.json').write_text(json.dumps(meta,indent=2)+'\n')
    scene.export(HERE/'full-stock-rest.glb')
    pulled,_=export_scene(stroke=60)
    pulled.export(HERE/'full-stock-pull-60mm-study.glb')
    print('Full stock17mesh assembly exported. GLBmetres; JSON/CADmm; 60mm isassumedstudytravel.')

if __name__=='__main__':main()
