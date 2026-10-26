"""Bounded hand-wrench comparisons; reads but never reruns the old load study.

No force/comfort/printed-strength rating follows. Millimetres are converted to
metres only at the output moment boundary. Forces are forces ON the cannon.
"""
from pathlib import Path
import hashlib
import json
import math
import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/vortex-mpl")
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P = json.loads((HERE / "parameters.json").read_text())
PRIOR = ROOT / "load-study"
READ_ONLY_INPUTS = [
    PRIOR / name for name in [
        "parameters.json", "results.json", "analyze_loads.py", "README.md",
        "audit.md", "contact_wrench_screen.py", "contact-wrench-results.json",
    ]
] + [ROOT / "assembly-study/core-assembly.json"]


def hashes():
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in READ_ONLY_INPUTS}


def external_loads(load_case, mass, com_z, gravity_factor):
    theta = math.radians(load_case["angle_deg"])
    force = load_case["force_N"]
    point = np.array([0., 0., P["rear_plane_z_mm"] + P["load_point_offset_behind_rear_plane_mm"]])
    com = np.array([0., P["nominal_body_com_xyz_mm"][1], com_z])
    pull = np.array([0., force * math.sin(theta), force * math.cos(theta)])
    weight = np.array([0., -mass * P["gravity_m_s2"] * gravity_factor, 0.])
    return [(point, pull), (com, weight)]


def external_wrench(loads):
    return sum((np.r_[f, np.cross(r, f)] for r, f in loads), start=np.zeros(6))


def hand_wrench(grasp, loads):
    force = -sum((f for _, f in loads), start=np.zeros(3))
    couple = -sum((np.cross(r - grasp, f) for r, f in loads), start=np.zeros(3))
    return force, couple


def solve_planar_mounts(points, wrench):
    """Same explicit minimum-norm point-stiffness hypothesis as prior study."""
    matrix = np.zeros((3, 2 * len(points)))
    for i, (_, y, z) in enumerate(points):
        matrix[:, 2*i] = [1, 0, -z]
        matrix[:, 2*i+1] = [0, 1, y]
    planar = wrench[[1, 2, 3]]
    reactions = np.linalg.pinv(matrix) @ -planar
    residual = matrix @ reactions + planar
    assert np.max(np.abs(residual)) < 1e-7
    return reactions.reshape(-1, 2), residual


def replay_prior(prior):
    """Audit exported numbers using full 3D cross products, without imports."""
    grasp = np.array([0., *prior["input_parameters"]["hand_grip_yz_mm"]])
    hand_error = wrench_error = equilibrium_error = 0.
    for case in prior["cases"]:
        loads = [(np.array([0., *load["point_yz_mm"]]), np.array([0., *load["force_yz_N"]]))
                 for load in case["external_loads"]]
        _, couple = hand_wrench(grasp, loads)
        wrench = external_wrench(loads)
        hand_error = max(hand_error, abs(couple[0] - case["hand_required_moment_Nmm"]))
        wrench_error = max(wrench_error, float(np.max(np.abs(
            wrench[[1, 2, 3]] - case["external_wrench_Fy_Fz_Mx"]))))
        for group in case["groups"]:
            reactions = group["reaction_yz_N"]
            points = [prior["input_parameters"]["joint_centres_yz_mm"][i]
                      for i in group["joint_indices"]]
            residual = wrench[[1, 2, 3]].copy()
            for (fy, fz), (y, z) in zip(reactions, points):
                residual += [fy, fz, y*fz-z*fy]
            equilibrium_error = max(equilibrium_error, float(np.max(np.abs(residual))))
    assert hand_error < 1e-8 and wrench_error < 1e-8 and equilibrium_error < 1e-7
    return {"cases": len(prior["cases"]), "max_hand_moment_difference_Nmm": hand_error,
            "max_external_wrench_difference_mixed_N_Nmm": wrench_error,
            "max_stored_mount_equilibrium_residual_mixed_N_Nmm": equilibrium_error,
            "scope": "Algebraic replay only; prior scripts and files are unchanged"}


def make_variants():
    base = np.array(P["baseline_grasp_xyz_mm"], dtype=float)
    variants = []
    for family in ["same_height", "cone_slope"]:
        for shift in P["rearward_shifts_mm"]:
            drop = shift * math.tan(math.radians(P["cone_half_angle_deg"])) if family == "cone_slope" else 0.
            variants.append({"name": f"{family}_{shift:g}", "family": family,
                             "rearward_mm": shift, "down_mm": drop,
                             "grasp_xyz_mm": (base + [0, -drop, shift]).tolist()})
    for case in P["clearance_drop_sensitivities"]:
        variants.append({**case, "family": "clearance_drop",
                         "grasp_xyz_mm": (base + [0, -case["down_mm"], case["rearward_mm"]]).tolist()})
    if P["selected_geometry"]:
        selected = P["selected_geometry"]
        grasp = np.array(selected["grasp_xyz_mm"])
        delta = grasp - base
        existing = next((v for v in variants if v["name"] == selected["name"]), None)
        if existing:
            assert np.array_equal(existing["grasp_xyz_mm"], grasp)
            existing["selected"] = True
        else:
            variants.append({**selected, "family": "selected_geometry", "selected": True,
                             "rearward_mm": float(delta[2]), "down_mm": float(-delta[1])})
    return variants


def centroid_comparison(variants):
    """Keep source solid-geometry proxy distinct from assumed operating inputs."""
    path = HERE / "stock-geometric-centroid.json"
    geometric = json.loads(path.read_text())
    whole = next(g for g in geometric["groups"] if g["name"] == "whole_stock_17_meshes")
    proxy = whole["uniform_solid_centroid_xyz_mm"]
    mass = P["nominal_body_mass_kg"]
    references = [
        {"name": "published_assumed_COM", "mass_kg": mass, "com_xyz_mm": P["nominal_body_com_xyz_mm"]},
        {"name": "stock_centroid_at_assumed_total_mass", "mass_kg": mass, "com_xyz_mm": proxy},
        {"name": "stock_uniform_solid_full_density_reference", "mass_kg": whole["full_density_mass_g_at_reference_1p28_g_cm3"]/1000,
         "com_xyz_mm": proxy},
    ]
    rows = []
    for reference in references:
        for load_case in P["load_cases"]:
            for factor in P["gravity_factors"]:
                loads = external_loads(load_case, reference["mass_kg"], reference["com_xyz_mm"][2], factor)
                # Preserve the tiny transverse source centroid components here.
                loads[1] = (np.array(reference["com_xyz_mm"]), loads[1][1])
                _, original = hand_wrench(np.array(P["baseline_grasp_xyz_mm"]), loads)
                for variant in variants:
                    force, couple = hand_wrench(np.array(variant["grasp_xyz_mm"]), loads)
                    rows.append({"reference": reference["name"], "variant": variant["name"],
                                 "load_case": load_case["name"], "gravity_factor": factor,
                                 "hand_force_xyz_N": force.tolist(), "signed_hand_couple_xyz_Nm": (couple/1000).tolist(),
                                 "signed_hand_Cx_Nm": float(couple[0]/1000),
                                 "absolute_couple_reduction_Nm": float((abs(original[0])-abs(couple[0]))/1000)})
    optional = None
    handle_path = HERE.parent / "handle/handle-validation.json"
    if handle_path.exists():
        handle = json.loads(handle_path.read_text())
        original = handle["selected_handle"]
        changed = handle["optional_handle"]
        new_volume = whole["total_additive_volume_mm3"]-original["volume_mm3"]+changed["volume_mm3"]
        new_com = (whole["total_additive_volume_mm3"]*np.array(proxy)
                   - original["volume_mm3"]*np.array(original["centroid_mm"])
                   + changed["volume_mm3"]*np.array(changed["centroid_mm"]))/new_volume
        optional = {"handle_validation_sha256": hashlib.sha256(handle_path.read_bytes()).hexdigest(),
                    "scope": "Stock17 geometry with handle4 replaced only. Excludes B/C shell/hardware changes and slice effects; uniform additive solid proxy.",
                    "total_volume_mm3": new_volume, "centroid_xyz_mm": new_com.tolist(),
                    "reference_mass_kg_at_1p28_g_cm3": new_volume*.00000128,
                    "hold_balance_rear_shift_from_original_grasp_mm": float(new_com[2]-P["baseline_grasp_xyz_mm"][2])}
    return {"source_json_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "references": references,
            "method": "Exact source volume-centroid proxy is held fixed while comparing hand points.0.6kg reference isolates COM effect; full-density reference is separately labelled. A redesigned handle changes its own COM, so these are not updated DesignC mass properties.",
            "assumed_hold_balance_rear_shift_mm": P["nominal_body_com_xyz_mm"][2]-P["baseline_grasp_xyz_mm"][2],
            "fixed_stock_proxy_hold_balance_rear_shift_mm": proxy[2]-P["baseline_grasp_xyz_mm"][2],
            "stock_with_optional_handle_only": optional,
            "cases": rows}


def main():
    before = hashes()
    prior = json.loads((PRIOR / "results.json").read_text())
    assembly = json.loads((ROOT / "assembly-study/core-assembly.json").read_text())
    lower = sorted((j for j in assembly["joints"] if j["side"] == -1),
                   key=lambda j: j["inner_surface_center_mm"][2])
    mounts = np.array([j["inner_surface_center_mm"] for j in lower])
    root = mounts.mean(axis=0)
    base = np.array(P["baseline_grasp_xyz_mm"], dtype=float)
    variants = make_variants()
    rows = []
    root_error = moment_identity_error = mount_error = 0.
    mount_cases = []
    for load_case in P["load_cases"]:
        for gravity_factor in P["gravity_factors"]:
            for mass in P["body_mass_sensitivity_kg"]:
                for com_z in P["body_com_z_sensitivity_mm"]:
                    loads = external_loads(load_case, mass, com_z, gravity_factor)
                    wrench = external_wrench(loads)
                    force_base, couple_base = hand_wrench(base, loads)
                    base_root_couple = couple_base + np.cross(base-root, force_base)
                    reference_root = -wrench[3:] + np.cross(root, wrench[:3])
                    root_error = max(root_error, float(np.max(np.abs(base_root_couple-reference_root))))
                    reactions, residual = solve_planar_mounts(mounts, wrench)
                    if mass == P["nominal_body_mass_kg"] and com_z == P["nominal_body_com_xyz_mm"][2]:
                        mount_cases.append({"load_case": load_case["name"], "gravity_factor": gravity_factor,
                                            "external_wrench_Fxyz_N_Mxyz_Nmm": wrench.tolist(),
                                            "mount_reaction_yz_N": reactions.tolist(),
                                            "peak_mount_resultant_N": float(np.linalg.norm(reactions, axis=1).max()),
                                            "equilibrium_residual_N_N_Nmm": residual.tolist()})
                    for variant in variants:
                        grasp = np.array(variant["grasp_xyz_mm"])
                        hand_force, couple = hand_wrench(grasp, loads)
                        root_couple = couple + np.cross(grasp-root, hand_force)
                        identity_delta = np.cross(grasp-base, wrench[:3])
                        moment_identity_error = max(moment_identity_error, float(np.max(np.abs(
                            couple-couple_base-identity_delta))))
                        root_error = max(root_error, float(np.max(np.abs(root_couple-base_root_couple))))
                        # Use an independently shifted hand representation to recover the
                        # wrench at the origin. It must give the SAME mount reactions.
                        hand_wrench_at_origin = np.r_[hand_force, couple+np.cross(grasp, hand_force)]
                        relocated_reactions, _ = solve_planar_mounts(mounts, -hand_wrench_at_origin)
                        mount_error = max(mount_error, float(np.max(np.abs(relocated_reactions-reactions))))
                        rows.append({"variant": variant["name"], "load_case": load_case["name"],
                                     "gravity_factor": gravity_factor, "mass_kg": mass, "com_z_mm": com_z,
                                     "hand_force_xyz_N": hand_force.tolist(),
                                     "signed_hand_Cx_Nm": float(couple[0]/1000),
                                     "abs_hand_Cx_Nm": float(abs(couple[0])/1000),
                                     "signed_delta_Cx_Nm": float((couple[0]-couple_base[0])/1000),
                                     "absolute_couple_reduction_Nm": float((abs(couple_base[0])-abs(couple[0]))/1000),
                                     "fixed_root_Cx_Nm": float(root_couple[0]/1000)})
    assert root_error < 1e-8 and moment_identity_error < 1e-8 and mount_error < 1e-8
    nominal = [row for row in rows if row["mass_kg"] == P["nominal_body_mass_kg"]
               and row["com_z_mm"] == P["nominal_body_com_xyz_mm"][2]]
    result = {
        "status": "Conditional hand-wrench study; not a physical strength, comfort, aim or performance rating",
        "inputs": P, "variants": variants, "retained_mounts_xyz_mm": mounts.tolist(),
        "fixed_root_reference_xyz_mm": root.tolist(),
        "equations": {
            "external": "F = sum(F_i); M_0 = sum(r_i cross F_i)",
            "hand": "F_h=-F; C_h(H)=-sum((r_i-H) cross F_i)=-M_0+H cross F",
            "relocation": "delta C_h = delta H cross F",
            "signed_planar_Nmm": "Cx = Yh*Fz + (Zpull-Zh)*Fy - (Zcom-Zh)*mass*g*gravity_factor",
            "same_height_delta_Nmm": "delta Cx = delta Z*(mass*g*gravity_factor-Fy)",
            "cone_delta_Nmm": "delta Cx = delta Z*(mass*g*gravity_factor-Fy-tan(alpha)*Fz)",
            "fixed_root": "C_h+(H-J) cross F_h = -M_0+J cross F, independent of H",
            "mounts": "A*q=-W_external; H is absent. Same point-stiffness hypothesis retains identical q.",
        },
        "prior_replay": replay_prior(prior),
        "verification": {
            "sensitivity_rows": len(rows), "max_relocation_identity_error_Nmm": moment_identity_error,
            "max_fixed_root_invariance_error_Nmm": root_error,
            "max_retained_mount_reaction_change_N": mount_error,
        },
        "nominal_cases": nominal,
        "stock_centroid_comparison": centroid_comparison(variants),
        "nominal_retained_mount_cases": mount_cases,
        "sensitivity_cases": rows,
        "interpretation_limits": [
            "Mass, COM and forces are chosen assumptions, not measured ranges or probabilities.",
            "A lower hand couple does not by itself reduce the wrench at a fixed handle root or the retained mount group.",
            "Redesigned section geometry, stiffness, clearance or contact can alter actual mount load sharing and local stresses.",
            "Prior equal-point-stiffness reactions are a hypothesis, not a bound on actual sharing.",
            "The inherited model assigns assumed body weight to the barrel-side free body; a refined split-body model must separate handle self-weight.",
            "No grip orientation, contact pressure, finger articulation, strength, fatigue or comfort is established.",
            "The 80mm force application offset is retained solely for continuity with prior load analysis; separate usage study covers0..60mm motion.",
            "Geometry clearance must choose the actual grasp. Higher grips remain conditional algebra only until clearance is established.",
        ],
        "read_only_provenance_sha256": before,
    }
    after = hashes()
    assert before == after, "Published read-only input changed during this run"
    result["verification"]["published_inputs_unchanged_during_run"] = True
    (HERE / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    plot(nominal, variants)
    summary = {
        "verification": result["verification"], "prior_replay": result["prior_replay"],
        "nominal20N": [r for r in nominal if r["load_case"] == "axial20"],
    }
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"variants": len(variants), **result["verification"]}, indent=2))


def plot(nominal, variants):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.4), facecolor="white")
    colors = {1: "#26715e", 0: "#69778a", -1: "#a45b3f"}
    shift = P["rearward_shifts_mm"]
    lookup = {(r["variant"], r["load_case"], r["gravity_factor"]): r for r in nominal}
    for factor, gravity_label in [(1, "upright 1g"), (0, "0g"), (-1, "inverted 1g")]:
        for family, style in [("same_height", "-"), ("cone_slope", "--")]:
            values = [lookup[(f"{family}_{s:g}", "axial20", factor)]["signed_hand_Cx_Nm"] for s in shift]
            axes[0].plot(shift, values, style, marker="o", color=colors[factor], lw=2,
                         label=f"{gravity_label}, {'same Y' if family == 'same_height' else 'cone slope'}")
    axes[0].set_title("20 N axial: signed hand couple")
    axes[0].set_ylabel("Required Cx (N·m); negative is the counter-couple")
    axes[0].legend(fontsize=8, loc="lower left")
    direction_colors = {"up10deg20": "#8363a1", "axial20": "#26715e", "down10deg20": "#b47629"}
    for case, label in [("up10deg20", "+10° (upward Fy)"), ("axial20", "axial"), ("down10deg20", "−10° (downward Fy)")]:
        for family, style in [("same_height", "-"), ("cone_slope", "--")]:
            values = [lookup[(f"{family}_{s:g}", case, 1)]["absolute_couple_reduction_Nm"] for s in shift]
            axes[1].plot(shift, values, style, marker="o", color=direction_colors[case], lw=2,
                         label=f"{label}, {'same Y' if family == 'same_height' else 'cone slope'}")
        for name in ["rear15_drop1p5", "rear30_drop3"]:
            v = next(v for v in variants if v["name"] == name)
            axes[1].plot(v["rearward_mm"], lookup[(name, case, 1)]["absolute_couple_reduction_Nm"],
                         marker="x", ms=9, mew=2, color=direction_colors[case])
    axes[1].set_title("20 N, upright 1g: effect of pull direction")
    axes[1].set_ylabel("Reduction in |Cx| from original (N·m)")
    hardware_case = lookup[("rear30_drop20_B_hardware", "axial20", 1)]
    axes[1].plot(30, hardware_case["absolute_couple_reduction_Nm"], marker="D", ms=8,
                 color="#243342", label="30 rear / 20 down, axial")
    axes[1].axhline(0, color="#69778a", lw=.8)
    axes[1].legend(fontsize=8, loc="upper left")
    for ax in axes:
        ax.set_xlabel("Rearward grasp shift (mm)")
        ax.set_xticks(shift)
        ax.grid(alpha=.2)
    fig.suptitle("Handle relocation · assumed 0.60 kg, COM Z=140 mm", fontsize=15)
    fig.text(.5, .025, "Solid = same height; dashed = follows 5.4923° cone; × = explicit 15/1.5 and 30/3 mm shift/drop.\n"
             "Retained mount equilibrium and fixed-root wrench stay unchanged. Geometry, material strength and comfort remain separate.",
             ha="center", fontsize=9, color="#374151")
    fig.tight_layout(rect=[0, .09, 1, .94])
    fig.savefig(HERE / "handle-position-comparison.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
