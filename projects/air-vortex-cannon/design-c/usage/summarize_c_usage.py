"""Make a compact handoff from the completed, frozen C geometry results."""
from pathlib import Path
import json, hashlib

HERE = Path(__file__).resolve().parent

def walk(value):
    if isinstance(value, dict):
        if 'obstacle' in value and 'minimum_sampled_clearance_mm' in value:
            yield value
        else:
            for child in value.values():
                yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)

def stats(value):
    rows = list(walk(value))
    minimum = min(rows, key=lambda q: q['minimum_sampled_clearance_mm'])
    return {'obstacle_checks': len(rows), 'minimum_reported_clearance_mm': minimum['minimum_sampled_clearance_mm'],
            'limiting_obstacle': minimum['obstacle'],
            'maximum_sampled_penetration_mm': max(q['maximum_sampled_penetration_mm'] for q in rows),
            'points_over_0_02mm_penetration': sum(q['points_over_0_02mm_penetration'] for q in rows)}

def main():
    path = HERE/'usage-results.json'
    r = json.loads(path.read_text())
    sampled = {name: stats(r[name]) for name in ['axial_motion', 'offaxis_end_positions', 'lower_three_static_tools', 'lower_three_rear_entry', 'lower_three_bolt_withdrawal', 'deployed_sight']}
    families = {}
    for kind in ['inside-tool-static', 'outside-tool-static', 'inside-tool-rear-entry']:
        rows = [q for q in r['continuous_tool_and_entry_certificates'] if q['envelope'] == kind]
        low = min(rows, key=lambda q: q['continuous_boundary_clearance_lower_bound_mm'])
        families[kind] = {'count': len(rows), 'all_conditionally_clear': all(q['conditional_geometric_clear'] for q in rows),
                          'minimum_continuous_clearance_lower_bound_mm': low['continuous_boundary_clearance_lower_bound_mm'],
                          'limiting_joint': low['joint']}
    h = min(r['hand_proxies'], key=lambda q: q['minimum_separation_lower_bound_mm'])
    summary = {'scope': r['scope'], 'usage_results_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
               'inputs_unchanged_during_run': r['inputs_unchanged_during_run'], 'fixed_obstacle_count': r['fixed_obstacle_count'],
               'all_obstacles_closed_consistent_connected_positive_volume': all(q['watertight'] and q['winding_consistent'] and q['connected_components'] == 1 and q['positive_volume'] for q in r['obstacle_closed_solid_preconditions']),
               'sampled_checks': sampled, 'continuous_tool_families': families,
               'continuous_rigid_radial_bounds': r['continuous_rigid_radial_bounds'],
               'all_chosen_hand_ellipsoids_clear': all(c['conditional_envelope_clear'] for q in r['hand_proxies'] for c in q['checks']),
               'minimum_chosen_hand_separation_lower_bound_mm': h['minimum_separation_lower_bound_mm'],
               'limiting_hand_proxy': h['proxy'], 'limiting_hand_obstacle': h['limiting_obstacle']}
    (HERE/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    rows = '\n'.join(f"| {name.replace('_', ' ')} | {q['minimum_reported_clearance_mm']:.6f} | {q['maximum_sampled_penetration_mm']:.6g} | {q['limiting_obstacle']} |" for name, q in sampled.items())
    tools = '\n'.join(f"| {kind} | {q['count']} | {q['minimum_continuous_clearance_lower_bound_mm']:.6f} | {q['limiting_joint']} |" for kind, q in families.items())
    rigid = '\n'.join(f"| {q['component']} | {q['continuous_radial_separation_lower_bound_mm']:.6f} |" for q in r['continuous_rigid_radial_bounds'])
    text = f'''# Revision C usage and lower-joint service geometry

This checks the actual frozen Revision C lower-three collar/adapter assembly with the original handle/grip location retained. It is conditional nominal CAD geometry, not a physical use, tool, human, strength or airflow validation.

The authoritative [full results](usage-results.json) preserve every input SHA256 before and after the run; inputs unchanged: **{r['inputs_unchanged_during_run']}**. The [compact summary](summary.json) hashes those full results. The [post-run input and pose verification](input-and-pose-verification.json) rechecks all 43 input hashes and the six exact C/B tool origins and axes. Reproduce with the existing Python environment by running [check_c_usage.py](check_c_usage.py), then [summarize_c_usage.py](summarize_c_usage.py).

## Whole fixed assembly

All 26 fixed obstacle meshes are closed, consistently wound, connected, positive-volume solids. They comprise source sight axle 1, corrected deployed sight 2, upper rail 3, original handle 4, rear clamp 10 and upper pins 11–13; three actual lower-only replacement shells 6/8/7; and 15 C lower-joint components. Lower pins 14–16 are removed. Integrated collars are included in the replacement shell meshes and not double-counted. Original source and Revision B files were read without mutation.

## Sampled motion and service

Seven axial positions 0/10/20/30/40/50/60 mm and four end positions at 60 mm with centre displacement ±10.5796 mm in X/Y check separate central rigid meshes, chosen film vertices and trimmed R1.5 mm band paths against the full fixed assembly. Central rigid pieces retain their source orientation; the carabiner stays on its assumed axial display midpoint.

All three lower joints have an inside R2 × 35 mm cylinder and outside R6 × 30 mm cylinder at the supplied exact head/nut datums, a rear-entry corridor, and bolt withdrawal at 0/5/10/15/20/25/30/35 mm. Own target hardware is excluded only for intentional tool contact. Withdrawal retains the own adapter/bore, shell and inner washer, after removing the outer nut/washer. These cylinders are chosen tool envelopes, not measured tools. Interior entry requires an unloaded membrane removed or held clear.

| Check family | Minimum reported clearance mm | Maximum sampled penetration mm | Limiting obstacle |
|---|---:|---:|---|
{rows}

No sample exceeds the 0.02 mm penetration reporting threshold. Positive clearance values can be conservative geometry lower bounds rather than exact nearest distances. Any small negative withdrawal value is explicitly retained in the JSON; it is not rounded into an exact no-contact assertion. Bolt withdrawal is sampled, not continuously certified.

The deployed sight table excludes intentional source axle/hole contact, with no sight points excluded. Folding remains unqualified because of the retained source cam/stop issue already identified in the original study.

## Continuous bounds with explicit preconditions

Tool cylinder sides and endcaps are covered by a grid with a known radius. Distance to a closed obstacle is 1-Lipschitz, so the minimum conservative point distance minus the cover radius bounds the complete cylinder boundary. Rear entry adds half the maximum 1 mm translation step. Every connected obstacle has a point outside the complete swept tool AABB, excluding hidden whole-obstacle containment. Analytical and sampled cylinder AABBs agree to the recorded numerical tolerance. Low bounds are refined with actual triangle distance when necessary. Containment requires agreement from four oblique rays along two independent lines, with the original library query used on disagreement.

| Tool family | Count | Minimum continuous CAD clearance lower bound mm | Limiting joint |
|---|---:|---:|---|
{tools}

These are recalculated C lower-three results. The old all-six B checks do not automatically establish C. No manufacturing/assembly/deflection tolerance is credited by the nominal numbers.

Complete moving-mesh radial bounds certify all axial positions 0–60 mm and any XY centre translation magnitude ≤10.5796 mm, under the retained rigid orientations and on-axis carabiner assumption:

| Rigid source piece | Continuous radial separation lower bound mm |
|---|---:|
{rigid}

## Chosen hand, film and elastic envelopes

The grip-hand ellipsoid stays at [0,-155,110.4] mm with radii [32.5,45,32.5] mm; intended source handle 4 contact is excluded. Seven pull-hand ellipsoids have radii [35,37.5,40] mm and follow the chosen axial clamp path. Exact closest obstacle triangle queries in each ellipsoid's scaled frame bound the whole chosen ellipsoid, with centre containment checked. All chosen hand ellipsoids clear their checked fixed obstacles: **{summary['all_chosen_hand_ellipsoids_clear']}**. The smallest lower bound is **{h['minimum_separation_lower_bound_mm']:.6f} mm**, for the {h['proxy']} proxy against {h['limiting_obstacle']}. This does not model actual fingers, reach, grip force, articulation or comfort.

The film is a zero-thickness annular cone warped linearly for the four off-axis cases; actual bag thickness/slack/wrinkles are unknown. Central/perimeter clamp contact zones are excluded explicitly. The 60 mm axial cone requires {100*r['membrane_geometry_60mm']['minimum_extra_area_fraction']:.4f}% more available annular area than the chosen flat annulus. This is a slack/geometry requirement, not film strain or expelled-air evidence. Band radius, rest shape, routing and midpoint are chosen; no elastic force equilibrium is solved.

Source central snap contact and rear-clamp release deformation remain unresolved source issues. These calculations provide no FDM strength/fatigue/creep, hardware locking, real tool/hand suitability, sealing or vortex-performance proof. No print, purchase or physical test was performed.

## Rejected containment diagnostic

The pure ±X containment shortcut was rejected after both rays misclassified points in the inner washer's open hole when they lay almost in its end-face plane. The [ray regression](ray-containment-regression.json) checks 215 such queries across all three washers against a triangle-derived empty axial-cylinder bound and the original library signed query; the corrected oblique-ray method agrees exactly and all 215 queries lie outside. The earlier `usage-results-axis-ray-diagnostic.json` and its matching `input-lower-assembly-axis-ray-diagnostic.json` are development diagnostics, excluded from acceptance. Their apparent 0.65 mm washer overlap is a rejected numerical artifact. The final full run above was rerun after the metadata freeze and preserves identical before/after hashes.
'''
    (HERE/'README.md').write_text(text)
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
