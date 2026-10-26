"""Demand-only screen for frozen Revision C lower-joint geometry.

Reads the prior study's fourteen stored planar reaction cases, never imports or
runs old solvers, and writes only beside this file. The source reaction sharing
is an explicit hypothesis, not a load-sharing bound or physical capacity.
"""
from pathlib import Path
import hashlib
import json
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = {
    "final_lower_assembly": ROOT / "design-c/joints/lower-assembly.json",
    "prior_results": ROOT / "load-study/results.json",
    "source_mount_datums": ROOT / "assembly-study/core-assembly.json",
}
CREDITED_COLLAR_THICKNESS_MM = 2.0
ELASTIC_MODULUS_EXAMPLES_MPA = [500.0, 1000.0, 1500.0]


def hashes():
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in INPUTS.values()}


def main():
    before = hashes()
    final = json.loads(INPUTS["final_lower_assembly"].read_text())
    prior = json.loads(INPUTS["prior_results"].read_text())
    source = json.loads(INPUTS["source_mount_datums"].read_text())
    spec = final["spec"]
    joints = sorted(final["joints"], key=lambda j: j["surface_center_mm"][2])
    originals = {j["id"]: j for j in source["joints"] if j["side"] == -1}
    assert len(joints) == 3 and len(prior["cases"]) == 14
    span = float(spec["collar_aperture_mm"][1])
    axial_length = float(spec["adapter_footprint_mm"][0])
    hole = float(spec["bore_diameter_mm"])
    net_width = axial_length - hole
    bearing_width = float(spec["key_mm"][1])
    assert span == 7.8 and axial_length == 30 and hole == 5.4
    assert net_width > 0 and bearing_width == 7.4
    datum_checks = []
    for i, joint in enumerate(joints):
        matrix = np.asarray(joint["adapter_local_to_assembly"], dtype=float)
        basis = matrix[:3, :3]
        original = originals[joint["id"]]
        point = np.asarray(joint["surface_center_mm"], dtype=float)
        position_error = float(np.max(np.abs(point - original["inner_surface_center_mm"])))
        old_yz_error = float(np.max(np.abs(point[1:] - prior["input_parameters"]["joint_centres_yz_mm"][i])))
        frame_position_error = float(np.max(np.abs(point - matrix[:3, 3])))
        basis_error = float(np.max(np.abs(basis.T @ basis - np.eye(3))))
        normal_error = float(np.max(np.abs(basis[:, 2] - joint["outward_axis"])))
        axial_error = float(np.max(np.abs(basis[:, 0] - original["axial_tangent"])))
        assert max(position_error, old_yz_error, frame_position_error, basis_error,
                   normal_error, axial_error, abs(np.linalg.det(basis) - 1)) < 1e-12
        datum_checks.append({"joint": joint["id"], "point_xyz_mm": point.tolist(),
                             "source_point_max_abs_change_mm": position_error,
                             "prior_planar_point_max_abs_change_mm": old_yz_error,
                             "frame_translation_error_mm": frame_position_error,
                             "basis_orthonormality_error": basis_error,
                             "normal_axis_error": normal_error,
                             "axial_axis_error": axial_error,
                             "basis_axial_circumferential_outward_columns": basis.tolist(),
                             "minimum_sampled_adapter_body_thickness_mm": joint["adapter_min_sampled_body_thickness_mm"]})

    rows = []
    max_equilibrium_residual = 0.0
    max_projection_difference_from_prior_N = 0.0
    old_demands = {(d["case"], d["group"], d["joint_index"]): d
                   for d in prior["local_demands"]}
    for case in prior["cases"]:
        for group in case["groups"]:
            residual = np.array(case["external_wrench_Fy_Fz_Mx"], dtype=float)
            for i, (fy, fz) in zip(group["joint_indices"], group["reaction_yz_N"]):
                joint = joints[i]
                force = np.array([0.0, fy, fz])
                point = np.asarray(joint["surface_center_mm"])
                basis = np.asarray(joint["adapter_local_to_assembly"])[:3, :3]
                axial, circumferential, normal = basis.T @ force
                normal_demand, tangent_demand = abs(float(normal)), abs(float(axial))
                residual += [fy, fz, point[1] * fz - point[2] * fy]
                old = old_demands[(case["name"], group["name"], i)]
                max_projection_difference_from_prior_N = max(
                    max_projection_difference_from_prior_N,
                    abs(normal_demand - old["normal_force_demand_N"]),
                    abs(tangent_demand - old["in_plane_axial_force_demand_N"]))
                thickness = float(joint["adapter_min_sampled_body_thickness_mm"])
                sigma = 3 * normal_demand * span / (2 * net_width * thickness**2)
                deflections = {str(E): normal_demand * span**3 / (4 * E * net_width * thickness**3)
                               for E in ELASTIC_MODULUS_EXAMPLES_MPA}
                rows.append({
                    "case": case["name"], "group": group["name"], "joint": joint["id"],
                    "prior_joint_index": i, "world_reaction_xyz_N": force.tolist(),
                    "signed_local_reaction_axial_circumferential_outward_N": [float(axial), float(circumferential), float(normal)],
                    "normal_force_magnitude_N": normal_demand,
                    "axial_tangent_force_magnitude_N": tangent_demand,
                    "nominal_axial_key_bearing_MPa_at_2mm_credit": tangent_demand / (CREDITED_COLLAR_THICKNESS_MM * bearing_width),
                    "minimum_sampled_adapter_thickness_mm": thickness,
                    "one_way_bridge_nominal_bending_MPa": sigma,
                    "one_way_bridge_deflection_mm_by_assumed_E_MPa": deflections,
                })
            max_equilibrium_residual = max(max_equilibrium_residual, float(np.max(np.abs(residual))))
    assert len(rows) == 98
    assert max_equilibrium_residual < 1e-7 and max_projection_difference_from_prior_N < 1e-10

    def peak(field):
        row = max(rows, key=lambda r: r[field])
        return {"value": row[field], "case": row["case"], "group": row["group"], "joint": row["joint"]}

    per_joint = []
    for joint in joints:
        site = [r for r in rows if r["joint"] == joint["id"]]
        worst = max(site, key=lambda r: r["one_way_bridge_nominal_bending_MPa"])
        per_joint.append({"joint": joint["id"],
                          "minimum_sampled_adapter_thickness_mm": worst["minimum_sampled_adapter_thickness_mm"],
                          "peak_normal_force_magnitude_N": max(r["normal_force_magnitude_N"] for r in site),
                          "peak_axial_tangent_force_magnitude_N": max(r["axial_tangent_force_magnitude_N"] for r in site),
                          "peak_nominal_axial_key_bearing_MPa_at_2mm_credit": max(r["nominal_axial_key_bearing_MPa_at_2mm_credit"] for r in site),
                          "peak_one_way_bridge_nominal_bending_MPa": worst["one_way_bridge_nominal_bending_MPa"],
                          "peak_bridge_deflection_mm_by_assumed_E_MPa": worst["one_way_bridge_deflection_mm_by_assumed_E_MPa"],
                          "bridge_peak_case": worst["case"], "bridge_peak_group": worst["group"]})
    result = {
        "status": "DEMAND-ONLY NOMINAL SECTION SCREEN; not strength, stiffness-selected sharing, capacity or a force rating",
        "input_sha256": before,
        "geometry_freeze": "Producer confirmed final lower-assembly.json freeze; exact version identified by SHA256",
        "method": "Reuse all fourteen prior stored planar reaction cases as assumed demands; no old script is run and no prior result is overwritten. Project each world reaction with the final adapter basis.",
        "geometry_and_assumptions": {
            "collar_nominal_inward_depth_mm": spec["collar_inward_depth_mm"],
            "collar_credited_continuous_bearing_thickness_mm": CREDITED_COLLAR_THICKNESS_MM,
            "bearing_credit_basis": "Explicit conservative 2mm credit only; do not add original source shell or claim the full nominal 2.5mm inward offset as validated continuous bearing section.",
            "collar_aperture_axial_circumferential_mm": spec["collar_aperture_mm"],
            "key_axial_circumferential_mm": spec["key_mm"],
            "normal_face_gap_mm": spec["conforming_face_normal_clearance_mm"],
            "bridge_span_mm": span, "adapter_axial_length_mm": axial_length,
            "central_hole_mm": hole, "bridge_effective_net_width_mm": net_width,
            "bridge_thickness_basis": "Use each site's producer-exported minimum SAMPLED body thickness uniformly in a one-way rectangular strip proxy. Sampling does not certify a global minimum or the physical load path.",
            "assumed_elastic_modulus_examples_MPa": ELASTIC_MODULUS_EXAMPLES_MPA,
            "equations": {"axial_bearing_MPa": "abs(F_axial)/(2.0*7.4)",
                          "bridge_bending_MPa": "3*abs(F_normal)*span/(2*net_width*t**2)",
                          "bridge_deflection_mm": "abs(F_normal)*span**3/(4*E*net_width*t**3)"},
        },
        "verification": {"prior_load_cases": len(prior["cases"]), "demand_rows": len(rows),
                         "all_three_mount_datums_and_frames_retained": True,
                         "max_prior_planar_equilibrium_residual_mixed_N_Nmm": max_equilibrium_residual,
                         "max_normal_or_axial_projection_difference_from_prior_N": max_projection_difference_from_prior_N},
        "datum_checks": datum_checks,
        "peaks": {"normal_force_N": peak("normal_force_magnitude_N"),
                  "axial_tangent_force_N": peak("axial_tangent_force_magnitude_N"),
                  "nominal_axial_key_bearing_MPa_at_2mm_credit": peak("nominal_axial_key_bearing_MPa_at_2mm_credit"),
                  "one_way_bridge_nominal_bending_MPa": peak("one_way_bridge_nominal_bending_MPa")},
        "per_joint_summary": per_joint,
        "limits": [
            "Prior 5/10/20N, 40N transient example, off-axis and gravity scenarios are assumptions; no measured operating envelope or probabilistic interpretation is added.",
            "Reaction sharing is inherited from minimum-norm equal point-joint stiffness and pair-participation sensitivities. Pair cases do not authorize loose or missing joints.",
            "This screen reuses planar Y/Z forces and Mx equilibrium only; tiny source X offsets and arbitrary side forces are not a newly solved six-component contact model.",
            "Mount locations and external assumed wrench are retained; new compliance, collar contact and capture play can change actual per-joint sharing.",
            "The prior planar free body puts all assumed body mass on the barrel side. Refined accounting must separate handle self-weight and changed hardware mass.",
            "Conforming faces have a nominal 0.05mm normal gap; actual contact develops through clearance closure and deformation. No distributed pressure, contact stiffness, impact at gap closure or curved-shell stability is solved.",
            "The simple flat, simply-supported one-way strip is not a curved conical-contact FE model and does not validate the inferred conical face, notch stresses, key-root strength, collar transition, bore bearing, creep, layer adhesion, fatigue or whole-assembly strength.",
            "The minimum sampled CAD thickness is not a metrology result or a proven global minimum after printing. No strength allowable, factor of safety, pass/fail or physical capacity is computed.",
            "No automatic transfer of the prior Design B steel-washer finite-element results or finite-contact capacities to Revision C is made. Changed geometry/contact must be assessed separately.",
            "Signs are retained for traceability; absolute reaction components are demand magnitudes and do not resolve load contact direction or preload.",
        ],
        "demand_rows": rows,
    }
    assert hashes() == before, "Frozen inputs changed during run"
    result["verification"]["all_read_only_inputs_unchanged_during_run"] = True
    (HERE / "final-lower-joint-demand-screen.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"verification": result["verification"], "peaks": result["peaks"],
                      "per_joint_summary": per_joint}, indent=2))


if __name__ == "__main__":
    main()
