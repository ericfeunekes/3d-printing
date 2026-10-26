"""Recommended-joint service paths and dynamic keep-out checks, all six sites.

Uses root's delivered canonical component meshes. Tool/hand envelopes are
explicit chosen examples; no user hand or actual tool was measured.
"""
from pathlib import Path
import sys,json,hashlib,math,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/vortex-mpl')
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(ROOT/'ancillary-study'))
from check_usage import make_fixed,deterministic_points,sampled_clearance,cylinder_points,line_points
from model_ancillary import load_meshes,membrane_mesh,band_graph

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_recommended():
    record=json.loads((ROOT/'design-b/recommended-assembly.json').read_text())
    components={}
    for c in record['components']:
        components[c['joint']+'--'+c['name']]=trimesh.load_mesh(ROOT/c['path'])
    return record,components

def main():
    record,components=load_recommended()
    source,_,_=make_fixed()
    # Root's final fused shell files supersede source shell references if
    # provided. Until then the continuous collars are checked independently.
    fused=[]
    for pattern in ['*recommended*shell*.stl','*reinforced*shell*.stl']:
        fused.extend((ROOT/'design-b').rglob(pattern))
    # Explicitly use caller-stable shell manifest when available; a guessed
    # filename is never grounds to claim that replacement geometry was used.
    shell_manifest=ROOT/'design-b/recommended-shells.json'
    used=[]
    if shell_manifest.exists():
        sm=json.loads(shell_manifest.read_text())
        rows=sm.get('shells',sm) if isinstance(sm,dict) else sm
        if isinstance(rows,list):
            for row in rows:
                obj=int(row['object_id']);path=ROOT/row['path']
                source[f'stock-{obj}']=trimesh.load_mesh(path);used.append(str(path.relative_to(ROOT)))
    collars={}
    if not used:
        for p in (ROOT/'design-b/collars').glob('*-assembled.stl'):
            if '-opening-' not in p.name:collars['collar-'+p.stem]=trimesh.load_mesh(p)
    obstacles={**source,**collars,**components}
    input_paths=[ROOT/'design-b/recommended-assembly.json',ROOT/'assembly-study/core-assembly.json',
                 ROOT/'ancillary-study/model_ancillary.py',ROOT/'assembly-study/recover_core.py',HERE/'check_usage.py']
    input_paths += [ROOT/c['path'] for c in record['components']]
    input_paths += [ROOT/p for p in used]
    if shell_manifest.exists():input_paths.append(shell_manifest)
    input_paths += list((ROOT/'design-b/collars').glob('*-assembled.stl')) if not used else []
    start_hashes={str(p.relative_to(ROOT)):digest(p) for p in input_paths}
    # Deployed source sight is part of outside service surroundings. Actual
    # stock hinge-stop contact remains a separately identified source issue.
    anc=load_meshes()
    sight=anc['obj_2_Sight2.STEP.stl']
    obstacles['deployed-sight']=sight
    results=[];extraction=[];entry=[]
    for j in record['joints']:
        M=np.asarray(j['adapter_local_to_assembly']);p=M[:3,3];n=np.asarray(j['outward_axis'])
        def point(z):return p+n*z
        neighbour={k:v for k,v in obstacles.items() if not k.startswith(j['id']+'--')}
        # Exact head/nut-face datums supplied by owning CAD, not earlier
        # approximate stock offsets.
        starts={'inside':(point(j['head_inner_face_local_z_mm']-.1),-n,2.,35.),
                'outside':(point(j['nut_outer_face_local_z_mm']+.1),n,6.,30.)}
        for side,(start,axis,radius,length) in starts.items():
            pts=cylinder_points(start,axis,radius,length,angular=16,axial=9)
            checks=sampled_clearance(pts,neighbour)
            results.append({'joint':j['id'],'side':side,'tool_origin_mm':start.tolist(),
              'tool_axis':axis.tolist(),'tool_radius_mm':radius,'tool_length_mm':length,
              'checks':checks,'scope':'Housing and neighbour clearance. Target joint hardware intentionally excluded from tool-contact check.'})
            print('recommended-tool',j['id'],side,'done',flush=True)
        # The interior hex key must reach the joint from the rear opening,
        # not magically appear inside a closed diaphragm. Model axial entry
        # with membrane removed/unloaded, retaining all rigid surroundings.
        start,axis,radius,length=starts['inside']
        travel=max(0,300.-start[2])
        envelopes=[]
        for shift in np.linspace(0,travel,max(2,math.ceil(travel/25)+1)):
            pts=cylinder_points(start+[0,0,shift],axis,radius,length,angular=12,axial=6)
            envelopes.append(pts)
        checks=sampled_clearance(np.vstack(envelopes),neighbour)
        entry.append({'joint':j['id'],'rearward_entry_translation_mm':travel,
          'state':'Unloaded, rear membrane removed or held out of entry corridor; actual rear clamp unsnapping is not rigid-clearance proven.',
          'checks':checks})
        # Tool head rotates while unthreading; R6 socket envelope already
        # covers the M4 nut's circumradius. Threads are geometric envelopes.
        boltname=j['id']+'--shoulder-bolt-reference'
        bolt=components[boltname]
        pts0=deterministic_points(bolt,460)
        allpts=np.vstack([pts0-n*travel for travel in [0,5,10,15,20,25,30,35]])
        # Nut/outer washer are removed before withdrawing the bolt. Its
        # adapter and bore remain and must clear the D5 shoulder.
        bo={k:v for k,v in obstacles.items() if k not in [boltname,j['id']+'--M4-nyloc-envelope-reference',j['id']+'--outer-M4-wide-washer-reference']}
        extraction.append({'joint':j['id'],'inward_withdrawal_samples_mm':[0,5,10,15,20,25,30,35],
          'checks':sampled_clearance(allpts,bo),
          'state':'Nut and outer washer removed first; unloaded service; inner washer may need controlled handling.'})
        print('recommended-entry/extract',j['id'],'done',flush=True)
    dynamic=[]
    added={**source,**collars,**components}
    for stroke in [0,10,20,30,40,50,60]:
        anc=load_meshes(stroke=stroke)
        pts=np.vstack([deterministic_points(m,300) for name,m in anc.items() if name.startswith(('obj_5_','obj_17_','obj_9_'))])
        film=membrane_mesh(stroke=stroke,radial_steps=12,angular_steps=36).vertices
        r=np.linalg.norm(film[:,:2],axis=1);film=film[(r>22)&(r<114.5)]
        graph=band_graph(stroke=stroke)
        bands=np.vstack([line_points(graph['nodes'][a],graph['nodes'][b],8,20 if b=='membrane_centre' else 8) for a,b in graph['edges']])
        dynamic.append({'stroke_mm':stroke,'rigid_and_film_checks':sampled_clearance(np.vstack([pts,film]),added),
                        'band_tube_checks':sampled_clearance(bands,added,margin=1.5)})
        print('recommended-pull',stroke,'done',flush=True)
    sight_rows=[]
    for angle in [0,15,30,45,60,75,90]:
        m=load_meshes(sight_fold_degrees=angle)['obj_2_Sight2.STEP.stl']
        sight_rows.append({'angle_deg':angle,'checks':sampled_clearance(deterministic_points(m,1800),added),
                           'hinge_exclusions':'None; all selected sight vertices/face-centroids checked'})
        print('recommended-sight',angle,'done',flush=True)
    end_hashes={str(p.relative_to(ROOT)):digest(p) for p in input_paths}
    data={'scope':'Conditional sampled recommended-assembly usage/service study; not physical proof',
      'source_revision':record.get('source_datum_revision'),'input_hashes':start_hashes,
      'input_hashes_after':end_hashes,'inputs_unchanged_during_run':start_hashes==end_hashes,
      'replacement_shells_used':used,'fallback':'If no replacement shell manifest, source shells + explicit continuous collars are both checked; this is not a claim that their mesh union was verified.',
      'assumptions':{'inside_tool':'R2×35mm envelope for2.5mmhexkeyshaft','outside_tool':'R6×30mm envelope for7mmnut socket',
        'service':'Unloaded, exterior nut/washer removed before bolt withdrawal; membrane out of interior entry corridor',
        'pull':'0..60mm illustrative annular conical film, central translating clamp; bandradius1.5mm and midpointjunction assumed',
        'sampling':'Rigidtools are cylinders sampled angularly/axially, not complete swept-volume boolean proof; negative clearances identify sampled intersections.'},
      'six_site_tools':results,'rear_entry':entry,'bolt_withdrawal':extraction,
      'added_parts_pull_keepout':dynamic,'added_parts_sight_sweep':sight_rows,
      'dynamic_obstacle_scope':'Despite historical field names, final checks include full actual fused replacement shells, retained source rails/rear clamp, and all recommended hardware. No hinge points excluded.',
      'not_proved':['Human finger articulation/reach/comfort','Rear clamp release deformation','Actual tool sizes and access','Thread/nyloc locking','Physical print strength/fit/deflection','Membrane constitutive or fluid dynamics']}
    (HERE/'recommended-usage-results.json').write_text(json.dumps(data,indent=2)+'\n')
    print('Wrote recommended full usage/service results',flush=True)

if __name__=='__main__':main()
