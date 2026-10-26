"""Uniform-solid volume centroid proxy of the recovered stock 17-part assembly.

Reads original STL files and calls assembly-study/assemble.load_assembly(); never
runs its export main() or mutates source. Outputs only in this script directory.
This is additive component volume, not a Boolean union, slice or measured mass.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ASSEMBLER = ROOT / 'assembly-study' / 'assemble.py'
spec = importlib.util.spec_from_file_location('stock_assembler_for_centroid', ASSEMBLER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
meshes, transforms, meta = module.load_assembly(stroke=0.0, sight_fold_degrees=0.0)
saved = json.loads((ROOT / 'assembly-study' / 'full-stock-assembly.json').read_text())
files = {int(p.name.split('_')[1]): p for p in (ROOT / 'source' / 'egordv').glob('*.stl')}
rows = []
for i, mesh in sorted(meshes.items()):
    matrix = np.asarray(transforms[i], dtype=float)
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.is_volume
    assert mesh.volume > 0 and abs(np.linalg.det(matrix[:3, :3]) - 1) < 1e-9
    rows.append({
        'object': i,
        'source_file': str(files[i].relative_to(ROOT)),
        'source_sha256': hashlib.sha256(files[i].read_bytes()).hexdigest(),
        'volume_mm3': float(mesh.volume),
        'volume_centroid_xyz_mm': mesh.center_mass.tolist(),
        'bounds_xyz_mm': mesh.bounds.tolist(),
        'watertight': bool(mesh.is_watertight),
        'winding_consistent': bool(mesh.is_winding_consistent),
        'is_positive_valid_volume': bool(mesh.is_volume),
        'source_to_assembly': matrix.tolist(),
    })

def group(name, objects):
    selected = [r for r in rows if r['object'] in objects]
    volume = sum(r['volume_mm3'] for r in selected)
    centroid = sum((r['volume_mm3'] * np.asarray(r['volume_centroid_xyz_mm']) for r in selected), start=np.zeros(3)) / volume
    return {'name': name, 'objects': sorted(objects), 'total_additive_volume_mm3': volume,
            'uniform_solid_centroid_xyz_mm': centroid.tolist(),
            'full_density_mass_g_at_reference_1p28_g_cm3': volume * .00128}

groups = [
    group('whole_stock_17_meshes', set(range(1, 18))),
    group('stock_handle_only_object4', {4}),
    group('whole_stock_except_handle4', set(range(1, 18)) - {4}),
    group('whole_stock_except_handle4_and_its_three_lower_clips', set(range(1, 18)) - {4, 14, 15, 16}),
]
source_inputs = [ASSEMBLER, ROOT/'assembly-study/recover_core.py', ROOT/'ancillary-study/model_ancillary.py', ROOT/'assembly-study/full-stock-assembly.json']
result = {
    'status': 'UNIFORM-SOLID GEOMETRIC CENTROID PROXY; not sliced, measured, or a physical COM estimate',
    'coordinate_system': 'mm; X horizontal, Y up, Z rearward; outlet Z0',
    'pose': {'stroke_mm': 0, 'sight_fold_deg': 0, 'source': 'assemble.load_assembly(stroke=0, sight_fold_degrees=0)'},
    'saved_assembly_max_transform_difference': float(max(np.max(np.abs(np.asarray(saved['source_to_assembly'][str(i)]) - transforms[i])) for i in meshes)),
    'input_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_inputs},
    'method': 'Each processed watertight positive-winding STL volume and volume center_mass after the exact rigid assembly transforms; C = sum(V_i C_i) / sum(V_i). No Boolean union; interpart overlap is counted additively.',
    'reference_density_g_cm3': 1.28,
    'groups': groups,
    'parts': rows,
    'limitations': [
        'Uniform density across every solid source component is an explicit geometric proxy. Real perimeter/infill choices, print orientation, voids, hardware, film and bands alter both mass and COM.',
        'Mass at reference density is a full-density reference only and must not replace the separately assumed 0.6 kg operating scenario.',
        'Stock only. Does not include Design B/C hardware, collars, adapters, changed handle, or revised shells.',
        'Nominal recovered rigid rest pose; source seating uncertainty and small interpart penetrations remain. The cap and junction move during actuation.',
        'Excluding handle4 is an accounting sensitivity, not a fully resolved free-body partition of lower clip/hardware masses. The separate group excluding its three clips makes that choice inspectable.',
        'Geometric checks establish closed positive-volume input surfaces, not printing feasibility, fit, strength or uniform physical density.'
    ],
}
(HERE / 'stock-geometric-centroid.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'groups': groups, 'saved_assembly_max_transform_difference': result['saved_assembly_max_transform_difference'], 'all17_positive_watertight_consistent': all(r['watertight'] and r['winding_consistent'] and r['is_positive_valid_volume'] for r in rows)}, indent=2))
