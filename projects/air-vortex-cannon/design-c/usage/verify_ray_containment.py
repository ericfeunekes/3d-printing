"""Bounded regression for the rejected pure-X annular-face ray degeneracy."""
from pathlib import Path
import sys, json, hashlib
import numpy as np
import trimesh
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_c_usage import load_inputs, deterministic_points, signed_oblique, original_signed, radial_bounds
from refine_service_certificate import signed_axis

def main():
    record, components, _, _, _, _ = load_inputs()
    rows = []
    for j in record['joints']:
        n = np.asarray(j['outward_axis'])
        M = np.asarray(j['adapter_local_to_assembly'])
        inverse = np.linalg.inv(M)
        bolt = components[j['id']+'--shoulder-bolt-reference']
        washer = components[j['id']+'--inner-M5-wide-washer-reference']
        base = deterministic_points(bolt, 740)
        pts = np.vstack([base-n*t for t in [0, 5, 10, 15, 20, 25, 30, 35]])
        old, _ = signed_axis(washer, pts)
        local_washer = washer.copy()
        local_washer.apply_transform(inverse)
        hole_radius_bound, _ = radial_bounds(local_washer)
        local = trimesh.transform_points(pts, inverse)
        point_radius = np.linalg.norm(local[:, :2], axis=1)
        # Every actual washer surface triangle has local radius >= this
        # bound; points strictly inside that axial cylinder are outside it.
        select = (old > .02)&(point_radius < hole_radius_bound-.02)
        q = pts[select]
        corrected, fallback = signed_oblique(washer, q)
        reference = original_signed(washer, q)
        assert len(q) and np.all(corrected < 0) and np.all(reference < 0)
        assert np.max(np.abs(corrected-reference)) < 1e-7
        rows.append({'joint': j['id'], 'analytical_actual_mesh_hole_radius_lower_bound_mm': hole_radius_bound,
                     'pure_X_false_inside_queries_strictly_in_open_hole': len(q),
                     'maximum_false_pure_X_penetration_mm': float(old[select].max()),
                     'maximum_selected_point_radius_mm': float(point_radius[select].max()),
                     'minimum_corrected_outside_distance_mm': float((-corrected).min()),
                     'corrected_vs_original_library_max_difference_mm': float(np.max(np.abs(corrected-reference))),
                     'four_oblique_ray_disagreement_fallbacks': fallback,
                     'all_selected_queries_correctly_outside': bool(np.all(corrected < 0))})
    result = {'scope': 'Method regression: rejected pure-X containment degeneracy at annular washer end-face plane',
              'truth_basis': 'Selected points lie strictly inside an infinite axial cylinder free of every actual washer surface triangle. Closed washer volume cannot fill this cylinder; it reaches unbounded exterior along its axis.',
              'current_method': 'Two independent paired oblique lines; all4rays must agree, else original-library signed-query fallback.',
              'manifest_sha256': hashlib.sha256((HERE.parent/'joints/lower-assembly.json').read_bytes()).hexdigest(),
              'cases': rows, 'passed': True}
    (HERE/'ray-containment-regression.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
