"""Boolean modified shell meshes using Manifold; source evidence immutable.

Run with manifold3d installed (task preparation used3.5.4 in /tmp only).
Native collar STEP/source parameters remain the owner of new geometry.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import trimesh
if Path('/tmp/vortex-manifold').exists():sys.path.insert(0,'/tmp/vortex-manifold')
import manifold3d
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent

def boolean_part(mesh):
    return manifold3d.Manifold(manifold3d.Mesh(np.asarray(mesh.vertices,dtype=np.float32),
                                             np.asarray(mesh.faces,dtype=np.uint32)))

def mesh_part(shape):
    m=shape.to_mesh64()
    v=np.asarray(m.vert_properties)[:,:3]
    f=np.asarray(m.tri_verts).copy()
    # Follow Manifold's topological seam relations rather than approximate
    # coordinate rounding at Boolean intersection vertices.
    remap=np.arange(len(v))
    for a,c in zip(m.merge_from_vert,m.merge_to_vert):remap[a]=c
    for _ in range(5):remap=remap[remap]
    mesh=trimesh.Trimesh(v,remap[f],process=False)
    mesh.remove_unreferenced_vertices()
    return mesh

def main():
    out=HERE/'reinforced-shells';out.mkdir(exist_ok=True)
    rows=json.loads((HERE/'collars/collar-specs.json').read_text())
    meta=json.loads((ROOT/'assembly-study/core-assembly.json').read_text())
    result=[]
    for i in [6,8,7]:
        base=trimesh.load_mesh(ROOT/'assembly-study/parts'/f'assembled-{i:02d}.stl')
        assert base.is_watertight and base.is_winding_consistent
        solid=boolean_part(base)
        assert str(solid.status()).endswith('NoError'),str(solid.status())
        for r in [x for x in rows if x['shell_object']==i]:
            collar=trimesh.load_mesh(HERE/'collars'/(r['joint']+'-assembled.stl'))
            opening=trimesh.load_mesh(HERE/'collars'/(r['joint']+'-opening-assembled.stl'))
            solid=(solid+boolean_part(collar))-boolean_part(opening)
            assert str(solid.status()).endswith('NoError'),str(solid.status())
        # Collapse sub-2micrometre boolean slivers before float32 STL export.
        # Keep this numerical tolerance far below the stated FDM fit budget.
        solid=solid.simplify(.002)
        mesh=mesh_part(solid)
        pieces=mesh.split(only_watertight=False)
        empty=[p for p in pieces if abs(p.volume)<1e-7]
        material=[p for p in pieces if abs(p.volume)>=1e-7]
        # Boolean coplanar cancellations may retain closed zero-volume sheets.
        # They contain no material and are not manufactured components.
        assert len(material)==1
        mesh=material[0]
        assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1, {
          'shell':i,'watertight':mesh.is_watertight,'winding':mesh.is_winding_consistent,
          'components':len(mesh.split()),'volumes':[x.volume for x in mesh.split()],
          'manifold_status':str(solid.status())}
        assert mesh.volume>base.volume
        assert np.max(np.abs(mesh.bounds-base.bounds))<.02
        mesh.export(out/f'shell-{i}-assembled.stl')
        roundtrip=trimesh.load_mesh(out/f'shell-{i}-assembled.stl')
        before_faces=len(roundtrip.faces)
        # STL float32 serialization can collapse submicrometre slivers into
        # duplicate/degenerate faces. Validate removes those faces only; no
        # coarse vertex welding or hole filling changes mating geometry.
        roundtrip.process(validate=True)
        numerical_cap_area=0.
        if not roundtrip.is_watertight:
            before_cap=len(roundtrip.faces)
            trimesh.repair.fill_holes(roundtrip)
            numerical_cap_area=float(roundtrip.area_faces[before_cap:].sum())
            # Only close float32-degenerate triangle pinholes, not real gaps.
            assert numerical_cap_area<1e-6,numerical_cap_area
        assert roundtrip.is_watertight and roundtrip.is_winding_consistent and len(roundtrip.split())==1
        serialization_cleanup_faces=before_faces-len(roundtrip.faces)
        mesh=roundtrip
        mesh.export(out/f'shell-{i}-assembled.stl')
        confirm=trimesh.load_mesh(out/f'shell-{i}-assembled.stl')
        assert confirm.is_watertight and confirm.is_winding_consistent and len(confirm.split())==1
        # Original shell print orientation/plate positioning, mm.
        printmesh=mesh.copy();printmesh.apply_transform(np.linalg.inv(np.array(meta['source_transforms'][str(i)])))
        printmesh.export(out/f'shell-{i}-print.stl')
        print_roundtrip=trimesh.load_mesh(out/f'shell-{i}-print.stl')
        print_before_faces=len(print_roundtrip.faces)
        print_roundtrip.process(validate=True)
        assert print_roundtrip.is_watertight and print_roundtrip.is_winding_consistent and len(print_roundtrip.split())==1
        print_cleanup_faces=print_before_faces-len(print_roundtrip.faces)
        print_roundtrip.export(out/f'shell-{i}-print.stl')
        print_confirm=trimesh.load_mesh(out/f'shell-{i}-print.stl')
        assert print_confirm.is_watertight and print_confirm.is_winding_consistent and len(print_confirm.split())==1
        assert np.all(printmesh.extents < [256,256,260])
        result.append({'shell_id':i,'watertight':mesh.is_watertight,'winding_consistent':mesh.is_winding_consistent,
          'components':len(mesh.split()),'source_volume_mm3':base.volume,'new_volume_mm3':mesh.volume,
          'added_volume_mm3':mesh.volume-base.volume,'print_bounds_mm':printmesh.extents.tolist(),
          'removed_zero_volume_sheets':len(empty),
          'serialization_duplicate_or_degenerate_faces_removed':serialization_cleanup_faces,
          'serialization_numerical_pinhole_cap_area_mm2':numerical_cap_area,
          'print_serialization_duplicate_or_degenerate_faces_removed':print_cleanup_faces,
          'print_stl_roundtrip_watertight':print_confirm.is_watertight,
          'max_bound_change_mm':float(np.abs(mesh.bounds-base.bounds).max()),
          'sha256':hashlib.sha256((out/f'shell-{i}-print.stl').read_bytes()).hexdigest()})
        print('Validated/fused shell',i,flush=True)
    (out/'validation.json').write_text(json.dumps({'engine':'Manifold3.5.4','numerical_simplification_tolerance_mm':.002,'units':'mm','results':result,
      'basis':'Original closed shell +2continuous collars; recut newslotapertures; geometry checks only, not printedstrength.'},indent=2)+'\n')

if __name__=='__main__':main()
