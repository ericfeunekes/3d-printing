"""Revision C whole-assembly conditional usage and lower-joint service checks.

This owns only design-c/usage. All source and Revision B inputs are read-only.
Geometry is nominal; tools, hands, film and elastic paths are chosen envelopes.
"""
from pathlib import Path
import sys, json, math, hashlib, os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/vortex-mpl')
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT/'assembly-study'), str(ROOT/'ancillary-study'), str(ROOT/'usage-study')]
from assemble import load_assembly
from recover_core import FILES
from model_ancillary import load_meshes, membrane_mesh, band_graph, membrane_requirements
import check_usage
from check_usage import deterministic_points, sampled_clearance, cylinder_points, line_points, radial_bounds, local_slab_bounds
from certify_envelopes import cylinder_boundary, whole_obstacle_not_contained
from refine_service_certificate import signed as original_signed

MANIFEST = ROOT/'design-c/joints/lower-assembly.json'
MOVING_IDS = [5, 9, 17]
REMOVED_IDS = [14, 15, 16]
STROKES = [0, 10, 20, 30, 40, 50, 60]
OFFSET = 60*math.tan(math.radians(10))
SIGNED_QUERY_STATS = {'points': 0, 'four_ray_disagreement_fallbacks': 0}

def signed_oblique(mesh, points):
    """Two paired non-axial rays avoid coplanar annular-face degeneracy.

    Pure X rays were rejected: queries in the open washer hole, almost in
    its end-face plane, sometimes yielded odd counts in both X directions.
    Four independent agreement checks use two oblique X-dominant lines;
    disagreement falls back to the library's original signed-distance path.
    """
    _, distance, _ = trimesh.proximity.closest_point(mesh, points)
    counts = []
    for vector in [[1., .173, .371], [1., -.319, .271]]:
        direction = np.asarray(vector)
        direction /= np.linalg.norm(direction)
        for sign in [1., -1.]:
            _, ray_index, _ = mesh.ray.intersects_location(points, np.tile(sign*direction, (len(points), 1)), multiple_hits=True)
            counts.append(np.bincount(ray_index, minlength=len(points)) % 2 == 1)
    agree = np.all(np.asarray(counts) == counts[0], axis=0)
    values = np.where(counts[0], distance, -distance)
    values[distance < 1e-8] = 0.
    ambiguous = (~agree)&(distance >= 1e-8)
    if np.any(ambiguous):
        values[ambiguous] = original_signed(mesh, points[ambiguous], chunk=64)
    return values, int(ambiguous.sum())

def fast_signed(mesh, points, chunk=384):
    """Exact distance with four-ray containment agreement, in bounded chunks."""
    values = []
    for part in np.array_split(points, max(1, math.ceil(len(points)/chunk))):
        result, ambiguous = signed_oblique(mesh, part)
        values.append(result)
        SIGNED_QUERY_STATS['points'] += len(part)
        SIGNED_QUERY_STATS['four_ray_disagreement_fallbacks'] += ambiguous
    return np.concatenate(values)

# Keep all original conservative broad-phase bounds; improve exact-query
# containment directions and retain the original signed fallback on import.
check_usage.signed = fast_signed

def hashes(paths):
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}

def load_inputs():
    record = json.loads(MANIFEST.read_text())
    assert len(record['components']) == 15 and len(record['replacement_shells']) == 3
    assert record['removed_source_pin_ids'] == REMOVED_IDS
    original, _, metadata = load_assembly()
    fixed = {f'stock-{i}': m for i, m in original.items() if i not in MOVING_IDS + REMOVED_IDS}
    for row in record['replacement_shells']:
        fixed[f"stock-{row['source_id']}"] = trimesh.load_mesh(ROOT/row['path'])
    components = {c['joint']+'--'+c['name']: trimesh.load_mesh(ROOT/c['path']) for c in record['components']}
    obstacles = {**fixed, **components}
    assert len(obstacles) == 26
    files = [MANIFEST, Path(__file__), ROOT/'assembly-study/assemble.py', ROOT/'assembly-study/recover_core.py',
             ROOT/'ancillary-study/model_ancillary.py', ROOT/'usage-study/check_usage.py',
             ROOT/'usage-study/certify_envelopes.py', ROOT/'usage-study/refine_service_certificate.py']
    files += list(FILES.values())
    files += [ROOT/c['path'] for c in record['components']]
    files += [ROOT/c['path'] for c in record['replacement_shells']]
    return record, components, obstacles, original, metadata, files

def mesh_preconditions(obstacles):
    rows = []
    for name, m in obstacles.items():
        pieces = m.split(only_watertight=False)
        rows.append({'obstacle': name, 'vertices': len(m.vertices), 'faces': len(m.faces),
                     'watertight': bool(m.is_watertight), 'winding_consistent': bool(m.is_winding_consistent),
                     'connected_components': len(pieces), 'positive_volume': bool(m.volume > 0),
                     'bounds_mm': m.bounds.tolist()})
    return rows

def summary(rows):
    minimum = min(rows, key=lambda q: q['minimum_sampled_clearance_mm'])
    maximum = max(rows, key=lambda q: q['maximum_sampled_penetration_mm'])
    return {'minimum_reported_clearance_mm': minimum['minimum_sampled_clearance_mm'],
            'limiting_obstacle': minimum['obstacle'],
            'maximum_sampled_penetration_mm': maximum['maximum_sampled_penetration_mm'],
            'points_over_0_02mm_penetration': sum(q['points_over_0_02mm_penetration'] for q in rows)}

def motion_case(stroke, delta, obstacles, label):
    anc = load_meshes(stroke=stroke)
    rigid = {}
    for name, m in anc.items():
        if name.startswith(('obj_5_', 'obj_17_')):
            m.apply_translation(delta)
        if name.startswith(('obj_5_', 'obj_9_', 'obj_17_')):
            checks = sampled_clearance(deterministic_points(m, 620), obstacles)
            rigid[name] = {'checks': checks, 'summary': summary(checks)}
    film = membrane_mesh(stroke=stroke, radial_steps=24, angular_steps=96)
    material_r = np.linalg.norm(film.vertices[:, :2], axis=1)
    weight = (116.8533-material_r)/(116.8533-20.)
    film.vertices += weight[:, None]*delta
    film_points = film.vertices[(material_r > 22)&(material_r < 114.5)]
    film_checks = sampled_clearance(film_points, obstacles)
    graph = band_graph(stroke=stroke)
    graph['nodes']['membrane_centre'] = (np.asarray(graph['nodes']['membrane_centre'])+delta).tolist()
    bands = {}
    for i, (a, b) in enumerate(graph['edges']):
        pts = line_points(graph['nodes'][a], graph['nodes'][b], 8, 20 if b == 'membrane_centre' else 8, spacing=3)
        checks = sampled_clearance(pts, obstacles, margin=1.5)
        bands[f'{i}-{a}-to-{b}'] = {'checks': checks, 'summary': summary(checks)}
    print('motion', label, 'done', flush=True)
    return {'case': label, 'stroke_mm': stroke, 'centre_XY_translation_mm': delta.tolist(),
            'central_rigid_rotation_deg': 0, 'rigid': rigid,
            'film': {'checks': film_checks, 'summary': summary(film_checks), 'mesh_area_mm2': float(film.area),
                     'excluded_contact': 'Material-index R<=22mm central clamp and R>=114.5mm perimeter clamp.'},
            'bands': bands,
            'assumptions': 'Zero-thickness warped annular cone; inner displacement fades linearly to zero at perimeter. Carabiner stays at axial display midpoint. R1.5 bands;8mm endpoint/20mm centre tie zones excluded.'}

def refine_low_bounds(points, obstacles, rows, target):
    changes = []
    for q in rows:
        if q['minimum_sampled_clearance_mm'] > target:
            continue
        m = obstacles[q['obstacle']]
        lo, hi = m.bounds
        box = np.linalg.norm(np.maximum(np.maximum(lo-points, points-hi), 0), axis=1)
        a, b = radial_bounds(m)
        r = np.linalg.norm(points[:, :2], axis=1)
        bound = np.maximum(np.maximum(box, np.maximum(np.maximum(a-r, r-b), 0)), local_slab_bounds(m, points))
        near = bound <= target
        values, ambiguous = signed_oblique(m, points[near])
        distances = bound.copy()
        distances[near] = -values
        changes.append({'obstacle': q['obstacle'], 'prior_minimum_bound_mm': q['minimum_sampled_clearance_mm'],
                        'exact_refined_samples': int(near.sum()), 'ray_disagreement_fallbacks': ambiguous})
        q['minimum_sampled_clearance_mm'] = float(distances.min())
        q['maximum_sampled_penetration_mm'] = float(max(0, -distances.min()))
        q['points_over_0_02mm_penetration'] = int((distances < -.02).sum())
        q['refinement'] = 'Every geometry-bound sample within certificate cover+.025mm replaced with exact signed triangle distance.'
    return changes

def certificate(joint, envelope, points, cover, obstacles, closed, motion_cover=0):
    rows = sampled_clearance(points, obstacles)
    changes = refine_low_bounds(points, obstacles, rows, cover+motion_cover+.025)
    d = min(q['minimum_sampled_clearance_mm'] for q in rows)
    not_contained = whole_obstacle_not_contained(obstacles, np.array([points.min(0), points.max(0)]))
    preconditions = closed and all(not_contained.values())
    return {'joint': joint, 'envelope': envelope, 'boundary_sample_count': len(points),
            'surface_cover_radius_mm': cover, 'motion_cover_radius_mm': motion_cover,
            'minimum_sample_bound_mm': d, 'continuous_boundary_clearance_lower_bound_mm': d-cover-motion_cover,
            'closed_consistent_connected_obstacles': closed,
            'no_obstacle_wholly_inside_swept_tool_AABB': all(not_contained.values()),
            'conditional_geometric_clear': bool(d > cover+motion_cover and preconditions),
            'checks': rows, 'refinement': changes}

def service(record, components, obstacles, closed):
    static, entry, withdrawal, certificates = [], [], [], []
    for j in record['joints']:
        p = np.asarray(j['adapter_local_to_assembly'])[:3, 3]
        n = np.asarray(j['outward_axis'])
        neighbour = {k: v for k, v in obstacles.items() if not k.startswith(j['id']+'--')}
        for side, radius, length, z, axis in [
            ('inside', 2., 35., j['head_inner_face_local_z_mm']-.1, -n),
            ('outside', 6., 30., j['nut_outer_face_local_z_mm']+.1, n)]:
            origin = p+n*z
            points = cylinder_points(origin, axis, radius, length, angular=24, axial=13)
            rows = sampled_clearance(points, neighbour)
            static.append({'joint': j['id'], 'side': side, 'origin_mm': origin.tolist(), 'axis': axis.tolist(),
                           'radius_mm': radius, 'length_mm': length, 'checks': rows, 'summary': summary(rows),
                           'excluded': 'Own target adapter/hardware only; intentional tool contact not analyzed.'})
            if side == 'inside':
                angular, astep, rstep = 32, 1., .5
            else:
                angular, astep, rstep = 128, .3, .3
            boundary, cover = cylinder_boundary(origin, axis, radius, length, angular, astep, rstep)
            exact_lo = np.minimum(origin, origin+axis*length)-radius*np.sqrt(np.maximum(0, 1-axis*axis))
            exact_hi = np.maximum(origin, origin+axis*length)+radius*np.sqrt(np.maximum(0, 1-axis*axis))
            aabb_error = float(np.abs(np.array([boundary.min(0), boundary.max(0)])-np.array([exact_lo, exact_hi])).max())
            cert = certificate(j['id'], side+'-tool-static', boundary, cover, neighbour, closed)
            cert['analytical_vs_sampled_cylinder_AABB_max_error_mm'] = aabb_error
            cert['conditional_geometric_clear'] &= aabb_error < 1e-7
            certificates.append(cert)
            if side == 'inside':
                travel = max(0., 300.-origin[2])
                shifts = np.linspace(0, travel, max(2, math.ceil(travel/25)+1))
                points = np.vstack([points+[0, 0, shift] for shift in shifts])
                rows = sampled_clearance(points, neighbour)
                entry.append({'joint': j['id'], 'rearward_entry_translation_mm': travel,
                              'sampled_translation_values_mm': shifts.tolist(), 'checks': rows, 'summary': summary(rows),
                              'required_state': 'Unloaded; membrane removed or held clear of corridor. Rear-clamp release deformation remains unproved.'})
                dense = np.linspace(0, travel, math.ceil(travel/1.)+1)
                boundary = np.vstack([boundary+[0, 0, shift] for shift in dense])
                motion_cover = float(np.diff(dense).max()/2)
                cert = certificate(j['id'], 'inside-tool-rear-entry', boundary, cover, neighbour, closed, motion_cover)
                cert['translation_samples'] = len(dense)
                cert['translation_mm'] = travel
                certificates.append(cert)
            print('service tool', j['id'], side, 'done', flush=True)
        boltname = j['id']+'--shoulder-bolt-reference'
        points = deterministic_points(components[boltname], 740)
        travels = [0, 5, 10, 15, 20, 25, 30, 35]
        points = np.vstack([points-n*t for t in travels])
        excluded = [boltname, j['id']+'--M4-nyloc-envelope-reference', j['id']+'--outer-M4-wide-washer-reference']
        rows = sampled_clearance(points, {k: v for k, v in obstacles.items() if k not in excluded})
        withdrawal.append({'joint': j['id'], 'inward_translation_samples_mm': travels, 'checks': rows, 'summary': summary(rows),
                           'required_state': 'Nut and outer washer removed; unloaded. Own adapter/bore, shell, inner washer and all other fixed parts retained. Inner washer needs controlled handling.',
                           'scope': 'Selected complete-bolt vertices/face centroids at8positions; no continuous withdrawal certificate.'})
        print('withdrawal', j['id'], 'done', flush=True)
    return static, entry, withdrawal, certificates

def rigid_radial(obstacles):
    limits = {name: radial_bounds(m)[0] for name, m in obstacles.items()}
    limiting = min(limits, key=limits.get)
    minimum = limits[limiting]
    rows = []
    for name, m in load_meshes().items():
        if not name.startswith(('obj_5_', 'obj_9_', 'obj_17_')):
            continue
        radius = float(np.linalg.norm(m.vertices[:, :2], axis=1).max())
        shift = 0. if name.startswith('obj_9_') else OFFSET
        rows.append({'component': name, 'complete_rigid_mesh_maximum_radius_mm': radius,
                     'assumed_max_XY_translation_mm': shift, 'minimum_fixed_surface_radius_mm': minimum,
                     'limiting_fixed_obstacle': limiting, 'continuous_radial_separation_lower_bound_mm': minimum-radius-shift,
                     'conditional_geometric_clear': bool(minimum > radius+shift),
                     'scope': 'All0..60mm axial positions and any XY translation magnitude<=10.5796mm; source rigid orientation retained. Carabiner stays on axis.'})
    return rows

def hand_proxies(obstacles):
    cases = [('grip', None, np.array([0., -155., 110.4]), np.array([32.5, 45., 32.5]))]
    cases += [('pull', stroke, np.array([0., 10., 261.8896408+stroke+60]), np.array([35., 37.5, 40.])) for stroke in STROKES]
    results = []
    for kind, stroke, center, radii in cases:
        checks = []
        for name, m in obstacles.items():
            if kind == 'grip' and name == 'stock-4':
                continue
            scaled = m.copy()
            scaled.vertices = (m.vertices-center)/radii
            _, distance, _ = trimesh.proximity.closest_point(scaled, np.zeros((1, 3)))
            d = float(distance[0])
            # AABB exclusion establishes the center outside for these cases;
            # ambiguous boxes use the closed-solid signed query.
            center_box_outside = bool(np.any(center < m.bounds[0]) or np.any(center > m.bounds[1]))
            if center_box_outside:
                center_outside = True
            else:
                value, _ = signed_oblique(scaled, np.zeros((1, 3)))
                center_outside = bool(value[0] <= 0)
            lower = (d-1)*float(radii.min()) if center_outside else -float(radii.min())
            checks.append({'obstacle': name, 'normalized_surface_distance': d, 'center_outside_obstacle': center_outside,
                           'ellipsoid_separation_lower_bound_mm': lower,
                           'conditional_envelope_clear': bool(d > 1 and center_outside)})
        minimum = min(checks, key=lambda q: q['ellipsoid_separation_lower_bound_mm'])
        results.append({'proxy': kind, 'stroke_mm': stroke, 'center_mm': center.tolist(), 'radii_mm': radii.tolist(),
                        'checks': checks, 'minimum_separation_lower_bound_mm': minimum['ellipsoid_separation_lower_bound_mm'],
                        'limiting_obstacle': minimum['obstacle'],
                        'scope': 'Chosen solid ellipsoid; exact nearest actual obstacle triangle in scaled frame. Bound=minradius*(normalized distance-1). Grip excludes intended sourcehandle4 contact; moving central grasp components are absent from fixed obstacles. No finger/reach/comfort model.'})
        print('hand proxy', kind, stroke, 'done', flush=True)
    return results

def main():
    manifest_snapshot = MANIFEST.read_bytes()
    record, components, obstacles, original, metadata, files = load_inputs()
    before = hashes(files)
    assert hashlib.sha256(manifest_snapshot).hexdigest() == before[str(MANIFEST.relative_to(ROOT))]
    (HERE/'input-lower-assembly.json').write_bytes(manifest_snapshot)
    preconditions = mesh_preconditions(obstacles)
    closed = all(q['watertight'] and q['winding_consistent'] and q['connected_components'] == 1 and q['positive_volume'] for q in preconditions)
    assert closed, 'Closed-solid precondition failed; do not issue signed-distance certificates.'
    axial = [motion_case(s, np.zeros(3), obstacles, f'axial-{s}') for s in STROKES]
    offaxis = []
    for axis in [0, 1]:
        for sign in [-1, 1]:
            delta = np.zeros(3)
            delta[axis] = sign*OFFSET
            label = ('lateral' if axis == 0 else 'vertical')+('-negative' if sign < 0 else '-positive')
            offaxis.append(motion_case(60, delta, obstacles, label))
    static, entry, withdrawal, certificates = service(record, components, obstacles, closed)
    radial = rigid_radial(obstacles)
    hands = hand_proxies(obstacles)
    # Recheck the deployed sight itself against replacement shells, retained
    # rail and C joints; its intentional stock axle/hole contact is excluded.
    sight_obstacles = {k: v for k, v in obstacles.items() if k not in ['stock-1', 'stock-2']}
    sight_rows = sampled_clearance(deterministic_points(original[2], 2400), sight_obstacles)
    after = hashes(files)
    data = {'scope': 'Revision C whole-assembly conditional CAD usage and lower-three service geometry; not physical validation',
            'units': 'mm', 'source_datum_revision': record['source_datum_revision'],
            'input_hashes_before': before, 'input_hashes_after': after, 'inputs_unchanged_during_run': before == after,
            'frozen_manifest_snapshot': 'design-c/usage/input-lower-assembly.json', 'signed_triangle_query_statistics': SIGNED_QUERY_STATS,
            'fixed_source_ids_retained': [1, 2, 3, 4, 10, 11, 12, 13], 'replacement_shell_source_ids': [6, 8, 7],
            'removed_lower_pin_ids': REMOVED_IDS, 'C_joint_component_count': len(components), 'fixed_obstacle_count': len(obstacles),
            'obstacle_closed_solid_preconditions': preconditions,
            'obstacle_scope': 'Every original fixed rigid piece retained, including original handle4, original upper rail3/pins11..13, corrected deployed sight2/axle1 and rearclamp10; only three shell meshes replaced and lowerpins14..16 removed. C collars are integrated in replacement shells and not double-counted.',
            'axial_motion': axial, 'offaxis_end_positions': offaxis,
            'lower_three_static_tools': static, 'lower_three_rear_entry': entry, 'lower_three_bolt_withdrawal': withdrawal,
            'continuous_tool_and_entry_certificates': certificates, 'continuous_rigid_radial_bounds': radial,
            'hand_proxies': hands, 'deployed_sight': {'checks': sight_rows, 'summary': summary(sight_rows), 'excluded_intentional_contact': 'Source axle1 with sight hole; no sight points excluded.'},
            'membrane_geometry_60mm': membrane_requirements(60),
            'certificate_method': 'Distance to closed solid is1-Lipschitz. Dense cylinder sides+caps have known surface cover radius; rear-entry adds half maximum1mm translation step. Each connected obstacle has a point outside the complete swept tool AABB, ruling out hidden whole-obstacle containment. Low conservative bounds within cover+.025mm refined using actual triangle distance. Containment uses agreement of four oblique rays along two independent X-dominant lines, falling back to original library signed query on disagreement. Pure X-only rays rejected due coplanar washer-hole degeneracy. Cylinder sampled AABBs independently checked against analytical boxes.',
            'tolerance_statement': 'Coordinates and tessellated geometry treated as exact inputs; no manufacturing/assembly/hardware/tool/deflection tolerance credited.',
            'assumptions': {'motion': '0..60mm chosen axial stroke; four60mm end poses offset±10.5796mm inX/Y. No central-piece tilt.',
                            'film': 'Chosen zero-thickness cone; material clamp zones excluded. Actual bag thickness/slack/wrinkles unmeasured.',
                            'elastic': 'Four schematic trimmed line edges with1.5mm radius and display-midpoint carabiner; no force equilibrium or routing/stiffness validation.',
                            'tools': 'Chosen R2×35mm interior and R6×30mm exterior rigid cylinders at supplied C head/nut datums; no real tool measured.',
                            'service': 'Unloaded; membrane held clear/removed for interior entry; nut/outerwasher removed for boltwithdrawal.',
                            'hands': 'Chosen ellipsoids; originalgrip center[0,-155,110.4]mm. No anthropometry/finger articulation/reach/comfort proof.'},
            'limitations': ['Sampled film/band/deployed-sight and bolt-withdrawal checks do not certify complete continuous surfaces or paths.',
                            'Continuous tool certificates apply only to stated ideal cylinders and entry translation; target joint hardware intentionally excluded.',
                            'Continuous radial certificate applies to complete rigid moving meshes with fixed orientation, chosen XY displacement and on-axis carabiner.',
                            'Source cap/male intended snap interference and rearclamp release deformation remain unresolved source assembly/contact issues.',
                            'Only deployed sight qualified here; retained source folding cam/stop remains previously unresolved.',
                            'Existing B load/FEA and all-six B service results do not automatically qualify C. This run recalculates C lower-three geometry.',
                            'No FDM strength/fatigue/creep, bolt locking, actual tool/hand fit, bag/elastic dynamics, sealing or airflow/vortex proof.']}
    (HERE/'usage-results.json').write_text(json.dumps(data, indent=2)+'\n')
    print('C usage complete; inputs unchanged:', before == after, flush=True)

if __name__ == '__main__':
    main()
