"""Four bounded off-axis pull-envelope cases at assumed60mm axial travel."""
from pathlib import Path
import sys,json,hashlib,math
import numpy as np,trimesh
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path[:0]=[str(HERE),str(ROOT/'ancillary-study')]
from check_usage import make_fixed,deterministic_points,sampled_clearance,line_points
from check_recommended import load_recommended
from model_ancillary import load_meshes,membrane_mesh,band_graph,make_transforms

def main():
    record,hardware=load_recommended()
    structure,_,_=make_fixed()
    shell_manifest=ROOT/'design-b/recommended-shells.json'
    used=[]
    if shell_manifest.exists():
        for row in json.loads(shell_manifest.read_text())['shells']:
            structure[f"stock-{int(row['object_id'])}"]=trimesh.load_mesh(ROOT/row['path']);used.append(row['path'])
    collars={}
    if not used:
        for p in (ROOT/'design-b/collars').glob('*-assembled.stl'):
            if '-opening-' not in p.name:collars['collar-'+p.stem]=trimesh.load_mesh(p)
    obstacles={**structure,**collars,**hardware}
    paths=[ROOT/'design-b/recommended-assembly.json',ROOT/'assembly-study/core-assembly.json',
           ROOT/'ancillary-study/model_ancillary.py',ROOT/'assembly-study/recover_core.py',HERE/'check_usage.py']
    paths += [ROOT/c['path'] for c in record['components']]+[ROOT/p for p in used]
    if shell_manifest.exists():paths.append(shell_manifest)
    start_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    stroke=60.;offset=stroke*math.tan(math.radians(10.))
    flat=membrane_mesh(stroke=0,radial_steps=36,angular_steps=192)
    records=[]
    for axis in [0,1]:
        for sign in [-1,1]:
            delta=np.zeros(3);delta[axis]=sign*offset
            moving=load_meshes(stroke=stroke)
            rigid=[]
            for name,m in moving.items():
                if name.startswith(('obj_5_','obj_17_')):
                    m.apply_translation(delta);rigid.append(deterministic_points(m,420))
                elif name.startswith('obj_9_'):
                    rigid.append(deterministic_points(m,300))
            film=membrane_mesh(stroke=stroke,radial_steps=36,angular_steps=192)
            radial=np.linalg.norm(film.vertices[:,:2],axis=1)
            t=(116.8533-radial)/(116.8533-20.)
            film.vertices=film.vertices+t[:,None]*delta
            # The same material-index radius, before warping, chooses the
            # intended-contact exclusions at centre/perimeter.
            mask=(radial>22)&(radial<114.5)
            samples=film.vertices[mask][::3]
            graph=band_graph(stroke=stroke)
            graph['nodes']['membrane_centre']=(np.asarray(graph['nodes']['membrane_centre'])+delta).tolist()
            bands=np.vstack([line_points(graph['nodes'][a],graph['nodes'][b],8,20 if b=='membrane_centre' else 8) for a,b in graph['edges']])
            name=('lateral' if axis==0 else 'vertical')+('-negative' if sign<0 else '-positive')
            film.export(HERE/f'film-{name}-60mm-study.stl')
            rigid_checks=sampled_clearance(np.vstack(rigid+[samples]),obstacles)
            band_checks=sampled_clearance(bands,obstacles,margin=1.5)
            records.append({'case':name,'axial_travel_mm':stroke,'assumed_pull_angle_deg':10.,
              'centre_offset_mm':delta.tolist(),'central_rigid_rotation_deg':0.,
              'junction_motion':'Unchanged display-axis midpoint, not solved elastic equilibrium',
              'film_area_mm2':film.area,'ratio_to_same_flat_mesh':film.area/flat.area,
              'required_extra_slack_area_percent':100*(film.area/flat.area-1),
              'rigid_and_film_checks':rigid_checks,'band_tube_checks':band_checks})
            print(name,'done',flush=True)
    f=ROOT/'design-b/recommended-assembly.json'
    result={'scope':'User-approved assumed off-axis motion; not physical film/elastic/hand validation',
      'recommended_joint_json_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),
      'replacement_shells_used':used,'input_hashes':start_hashes,
      'inputs_unchanged_during_run':start_hashes=={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
      'moving_source_poses':make_transforms(stroke=60.),
      'cases':records,'limits':['Only4endpositions; notcontinuousoffaxispathproof',
        'Centralrigidpiecestranslatewithouttilting; realfingerrotationnotmodeled',
        'Filmshapeislinearlywarpedzerothicknesscone, actualslack/wrinklesunknown',
        'Bandradius1.5mm, endpointtiezonestrimmed; actualrouting/stiffnessunknown',
        'Actualfusedrecommendedshellsusedwhenmanifestpresent; otherwiseexplicitfallbackgeometryisidentified']}
    (HERE/'offaxis-results.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Wrotefour offaxis cases',flush=True)

if __name__=='__main__':main()
