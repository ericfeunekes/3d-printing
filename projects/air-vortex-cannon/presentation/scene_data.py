"""Shared actual-mesh scenes for core / proposed Revision B presentation.

No shapes are redrawn here. Native data mm; exported glTF metres.
"""
from pathlib import Path
import sys,json
import numpy as np
import trimesh
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'assembly-study'))
sys.path.insert(0,str(ROOT/'ancillary-study'))
from assemble import load_assembly
import model_ancillary

COLORS={'shell':[65,130,170,255],'rail':[44,142,150,255],
        'stock':[108,129,142,255],'adapter':[231,151,61,255],
        'metal':[155,164,175,255],'film':[174,194,205,95],
        'band':[155,116,72,255],'collar':[76,153,188,255]}

def load_configuration(configuration='core',stroke=0.0,final_shells=False):
    core,T,metadata=load_assembly(stroke=stroke,sight_fold_degrees=0)
    parts=[]
    for i,m in core.items():
        if configuration=='recommended' and i in range(11,17):continue
        role='shell' if i in [6,7,8] else 'rail' if i in [3,4] else 'stock'
        parts.append({'key':f'stock-{i}','name':f'Stock object {i}','mesh':m,
                      'role':role,'source_id':i,'motion':1.0 if i in [5,17] else .5 if i==9 else 0.})
    status='Recovered stock assembly; source snaps remain unvalidated'
    if configuration=='recommended':
        proposed=json.loads((ROOT/'design-b/recommended-assembly.json').read_text())
        for row in parts:
            if row['source_id'] in [6,8,7] and final_shells:
                path=ROOT/f"design-b/reinforced-shells/shell-{row['source_id']}-assembled.stl"
                if not path.exists():raise FileNotFoundError(path)
                row['mesh']=trimesh.load_mesh(path);row['key']=f"reinforced-{row['source_id']}"
                row['name']=f"Proposed reinforced shell {row['source_id']}"
        if not final_shells:
            for j in proposed['joints']:
                path=ROOT/f"design-b/collars/{j['id']}-assembled.stl"
                parts.append({'key':f"preview-collar-{j['id']}",'name':'PREVIEW un-fused collar',
                    'mesh':trimesh.load_mesh(path),'role':'collar','source_id':None,'motion':0.})
        for row in proposed['components']:
            # Their files already contain assembled coordinates.
            role='adapter' if row['manufactured_here'] else 'metal'
            parts.append({'key':row['joint']+'--'+row['name'],'name':row['joint']+' '+row['name'],
                          'mesh':trimesh.load_mesh(ROOT/row['path']),'role':role,'source_id':None,'motion':0.})
        status=('Uses the fused proposed-shell exports; validation is a separate report' if final_shells
                else 'VISUAL PREVIEW: original shells plus separate collar overlays; not final fused exports')
    rear=metadata['rear_shell_plane_mm']
    film=model_ancillary.membrane_mesh(rear_plane=rear,stroke=stroke)
    parts.append({'key':'film-study','name':'Schematic diaphragm study','mesh':film,'role':'film','source_id':None,'motion':'film'})
    graph=model_ancillary.band_graph(rear_plane=rear,stroke=stroke)
    for k,(a,b) in enumerate(graph['edges']):
        p0,p1=np.array(graph['nodes'][a]),np.array(graph['nodes'][b])
        # Cylinder only presents the observed topology; radius/straightness not physical inputs.
        cylinder=trimesh.creation.cylinder(radius=.7,segment=np.array([p0,p1]),sections=10)
        parts.append({'key':f'band-study-{k}','name':'Schematic elastic connection','mesh':cylinder,
                      'role':'band','source_id':None,'motion':'band'})
    return parts,{'configuration':configuration,'units':'mm','stroke_study_mm':stroke,
                  'geometry_status':status,'rigid_part_count':len(parts)-5,
                  'source_metadata':metadata}

def export_glb(path,configuration='core',stroke=0.,final_shells=False):
    parts,meta=load_configuration(configuration,stroke,final_shells)
    scene=trimesh.Scene()
    for p in parts:
        m=p['mesh'].copy();m.visual.face_colors=COLORS[p['role']]
        scene.add_geometry(m,node_name=p['key'])
    scene.apply_scale(.001)
    scene.export(path)
    return meta
