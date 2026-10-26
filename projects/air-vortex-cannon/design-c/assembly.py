"""Revision C scene owner; consumes actual CAD exports, world millimetres.

Selected version retains the original handle and upper rail/pins. Collar
ingredient references are omitted because they are fused into the shells.
GLB consumers explicitly convert millimetres to metres.
"""
from pathlib import Path
import sys,json,hashlib
import trimesh

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'presentation'))
from scene_data import load_configuration,COLORS

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_selected(stroke=0.,optional_handle=False):
    record=json.loads((HERE/'joints/lower-assembly.json').read_text())
    parts,metadata=load_configuration('core',stroke=stroke)
    removed=set(record['removed_source_pin_ids'])
    shells={r['source_id']:r for r in record['replacement_shells']}
    files=[HERE/'joints/lower-assembly.json',Path(__file__).resolve()]
    output=[]
    for p in parts:
        i=p.get('source_id')
        if i in removed:continue
        if i in shells:
            path=ROOT/shells[i]['path'];files.append(path)
            p=dict(p,mesh=trimesh.load_mesh(path),key=f'c-shell-{i}',name=f'C lower-reinforced shell {i}')
        if i==4 and optional_handle:
            path=HERE/'handle/optional-handle-assembled.stl';files.append(path)
            p=dict(p,mesh=trimesh.load_mesh(path),key='optional-handle',name='Optional rear30/drop20 handle; not selected')
        output.append(p)
    active=[]
    for c in record['components']:
        if c['name']=='continuous-collar-reference':continue
        path=ROOT/c['path'];files.append(path);active.append(c)
        output.append({'key':c['joint']+'--'+c['name'],'name':c['joint']+' '+c['name'],
            'mesh':trimesh.load_mesh(path),'role':'adapter' if c['manufactured_here'] else 'metal',
            'source_id':None,'motion':0.})
    assert len(active)==15
    assert len(output)==34 # 29 rigid pieces plus film and four elastic proxies.
    metadata.update({'configuration':'C optional handle' if optional_handle else 'C selected original grip',
        'units':'mm','rigid_part_count':29,'printed_part_count':17,'metal_reference_count':12,
        'study_proxy_count':5,'selected_grasp_xyz_mm':[0.,-155.,110.4],
        'optional_grasp_xyz_mm':[0.,-175.,140.4] if optional_handle else None,
        'claim_boundary':'Conditional CAD prototype; no measured comfort, strength, fatigue or airflow gain.',
        'input_hashes':{str(p.relative_to(ROOT)):digest(p) for p in files}})
    return output,metadata

def export_scene(path,stroke=0.,optional_handle=False):
    parts,meta=load_selected(stroke,optional_handle)
    scene=trimesh.Scene()
    for p in parts:
        m=p['mesh'].copy();m.visual.face_colors=COLORS[p['role']]
        scene.add_geometry(m,node_name=p['key'])
    scene.apply_scale(.001)
    scene.export(path)
    reread=trimesh.load(path,force='scene')
    assert len(reread.geometry)==len(parts)
    meta['glb_units']='metres';meta['glb_geometry_count']=len(reread.geometry)
    meta['glb_bounds_m']=reread.bounds.tolist()
    meta['glb_sha256']=digest(path)
    return meta

def main():
    out=HERE/'presentation';out.mkdir(exist_ok=True)
    records={}
    for name,stroke,optional in [('selected-rest',0,False),('selected-pull-60mm-study',60,False),('optional-rear-grip-study',0,True)]:
        records[name]=export_scene(out/(name+'.glb'),stroke,optional)
    (out/'exports.json').write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps({k:{'rigid':v['rigid_part_count'],'GLB geometries':v['glb_geometry_count']} for k,v in records.items()}))

if __name__=='__main__':main()
