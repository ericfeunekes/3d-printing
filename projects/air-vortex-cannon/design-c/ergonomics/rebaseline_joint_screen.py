"""Record a metadata-only manifest rebaseline without rewriting prior results.

No CAD, solver, mesh reconstruction or hand-position grid is rerun. The prior
screen remains byte-for-byte intact and retains its original input hash.
"""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCREEN = HERE / "final-lower-joint-demand-screen.json"
MANIFEST = ROOT / "design-c/joints/lower-assembly.json"
REVISION = ROOT / "design-c/joints/metadata-revision.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def handle_centroid_rebaseline():
    """Verify only fields consumed by the preserved handle centroid accounting."""
    result_path = HERE / "results.json"
    handle_path = ROOT / "design-c/handle/handle-validation.json"
    stock_path = HERE / "stock-geometric-centroid.json"
    original_result_hash = sha(result_path)
    result = json.loads(result_path.read_text())
    old = result["stock_centroid_comparison"]["stock_with_optional_handle_only"]
    handle = json.loads(handle_path.read_text())
    stock = json.loads(stock_path.read_text())
    assert sha(stock_path) == result["stock_centroid_comparison"]["source_json_sha256"]
    whole = next(g for g in stock["groups"] if g["name"] == "whole_stock_17_meshes")
    source = next(g for g in stock["groups"] if g["name"] == "stock_handle_only_object4")
    source_volume = source["total_additive_volume_mm3"]
    whole_volume = whole["total_additive_volume_mm3"]
    assert source_volume == handle["selected_handle"]["volume_mm3"]
    assert source["uniform_solid_centroid_xyz_mm"] == handle["selected_handle"]["centroid_mm"]
    optional = handle["optional_handle"]
    current_volume = whole_volume-source_volume+optional["volume_mm3"]
    current_centroid = [
        (whole_volume*whole["uniform_solid_centroid_xyz_mm"][i]
         - source_volume*source["uniform_solid_centroid_xyz_mm"][i]
         + optional["volume_mm3"]*optional["centroid_mm"][i])/current_volume
        for i in range(3)
    ]
    assert current_volume == old["total_volume_mm3"]
    assert current_centroid == old["centroid_xyz_mm"]
    assert current_volume*.00000128 == old["reference_mass_kg_at_1p28_g_cm3"]
    assert current_centroid[2]-result["inputs"]["baseline_grasp_xyz_mm"][2] == old["hold_balance_rear_shift_from_original_grasp_mm"]
    expected_optional = next(v for v in result["variants"] if v["name"] == "rear30_drop20_B_hardware")
    assert optional["hand_point_mm"] == expected_optional["grasp_xyz_mm"]
    assert handle["selected_handle"]["hand_point_mm"] == result["inputs"]["baseline_grasp_xyz_mm"]
    assert sha(result_path) == original_result_hash
    return {
        "original_results_sha256_preserved": original_result_hash,
        "original_handle_validation_input_sha256_preserved": old["handle_validation_sha256"],
        "accepted_current_handle_validation_sha256": sha(handle_path),
        "scope": "Producer/proof-reviewer reported added C collision, STEP-roundtrip and middle-tool service-limit metadata. Verify all consumed mass/centroid/grasp fields without changing original results.",
        "current_optional_handle_volume_mm3": optional["volume_mm3"],
        "current_optional_handle_centroid_xyz_mm": optional["centroid_mm"],
        "current_optional_grasp_xyz_mm": optional["hand_point_mm"],
        "recomputed_stock_with_optional_handle_only": {
            "total_volume_mm3": current_volume, "centroid_xyz_mm": current_centroid,
            "reference_mass_kg_at_1p28_g_cm3": old["reference_mass_kg_at_1p28_g_cm3"],
            "hold_balance_rear_shift_from_original_grasp_mm": old["hold_balance_rear_shift_from_original_grasp_mm"],
        },
        "all_consumed_accounting_results_exactly_unchanged": True,
        "original_large_results_bytes_unchanged": True,
        "new_service_limit": handle["physical_limits"][-1],
        "claim_boundary": "This checks consumed geometry accounting fields. It does not establish optional grip service access, comfort, strength or a full C assembly COM. Original grip remains selected.",
    }


def main():
    screen_hash_before = sha(SCREEN)
    screen = json.loads(SCREEN.read_text())
    manifest = json.loads(MANIFEST.read_text())
    revision = json.loads(REVISION.read_text())
    original_hash = screen["input_sha256"]["design-c/joints/lower-assembly.json"]
    final_hash = sha(MANIFEST)
    assert original_hash == revision["previous_manifest_sha256"]
    assert final_hash == revision["revised_manifest_sha256"]
    assert revision["geometry_hashes_before"] == revision["geometry_hashes_after"]
    geometry_hashes = revision["geometry_hashes_before"]
    assert len(geometry_hashes) == 57
    for path, expected in geometry_hashes.items():
        assert sha(ROOT / path) == expected, path
    assert revision["component_pose_and_paths_unchanged"]
    assert revision["joint_pose_stack_and_dimensions_unchanged"]

    # Compare the exact inputs consumed by the old section screen, using its
    # retained input snapshot rather than an assertion based only on hashes.
    old = screen["geometry_and_assumptions"]
    spec = manifest["spec"]
    scalar_checks = {
        "collar_nominal_inward_depth_mm": (old["collar_nominal_inward_depth_mm"], spec["collar_inward_depth_mm"]),
        "collar_aperture_axial_circumferential_mm": (old["collar_aperture_axial_circumferential_mm"], spec["collar_aperture_mm"]),
        "key_axial_circumferential_mm": (old["key_axial_circumferential_mm"], spec["key_mm"]),
        "normal_face_native_design_gap_mm": (old["normal_face_gap_mm"], spec["conforming_face_normal_clearance_mm"]),
        "bridge_span_mm": (old["bridge_span_mm"], spec["collar_aperture_mm"][1]),
        "adapter_axial_length_mm": (old["adapter_axial_length_mm"], spec["adapter_footprint_mm"][0]),
        "central_hole_mm": (old["central_hole_mm"], spec["bore_diameter_mm"]),
        "bridge_net_width_mm": (old["bridge_effective_net_width_mm"], spec["adapter_footprint_mm"][0]-spec["bore_diameter_mm"]),
    }
    for name, (old_value, final_value) in scalar_checks.items():
        assert old_value == final_value, name
    site_checks = []
    sites = {j["id"]: j for j in manifest["joints"]}
    for old_site in screen["datum_checks"]:
        site = sites[old_site["joint"]]
        matrix = site["adapter_local_to_assembly"]
        basis = [row[:3] for row in matrix[:3]]
        translation = [row[3] for row in matrix[:3]]
        assert old_site["point_xyz_mm"] == site["surface_center_mm"] == translation
        assert old_site["basis_axial_circumferential_outward_columns"] == basis
        assert old_site["minimum_sampled_adapter_body_thickness_mm"] == site["adapter_min_sampled_body_thickness_mm"]
        assert [row[2] for row in basis] == site["outward_axis"]
        assert matrix[3] == [0, 0, 0, 1]
        site_checks.append({
            "joint": site["id"], "point_xyz_mm": translation,
            "basis_axial_circumferential_outward_columns": basis,
            "sampled_minimum_adapter_body_thickness_mm": site["adapter_min_sampled_body_thickness_mm"],
            "all_consumed_fields_exactly_unchanged": True,
        })

    # Confirm the immutable reaction owner is still the one used by the screen,
    # and each stored row still points to the original world reaction.
    prior_path = ROOT / "load-study/results.json"
    source_path = ROOT / "assembly-study/core-assembly.json"
    assert sha(prior_path) == screen["input_sha256"]["load-study/results.json"]
    assert sha(source_path) == screen["input_sha256"]["assembly-study/core-assembly.json"]
    prior = json.loads(prior_path.read_text())
    cases = {case["name"]: case for case in prior["cases"]}
    for row in screen["demand_rows"]:
        group = next(g for g in cases[row["case"]]["groups"] if g["name"] == row["group"])
        index = group["joint_indices"].index(row["prior_joint_index"])
        assert row["world_reaction_xyz_N"] == [0., *group["reaction_yz_N"][index]]
    assert sha(SCREEN) == screen_hash_before

    result = {
        "status": "EXPLICIT METADATA-ONLY SEMANTIC REBASELINE; prior numerical screen unchanged",
        "original_screen_path": str(SCREEN.relative_to(ROOT)),
        "original_screen_sha256_preserved": screen_hash_before,
        "original_manifest_input_sha256_preserved": original_hash,
        "accepted_final_manifest_sha256": final_hash,
        "producer_metadata_revision_sha256": sha(REVISION),
        "producer_metadata_revision_reason": revision["reason"],
        "new_gap_qualification": manifest["conforming_face_gap_qualification"],
        "consumed_section_inputs_old_and_final": {name: {"original": a, "final": b, "exactly_unchanged": True}
                                                  for name, (a, b) in scalar_checks.items()},
        "per_joint_checks": site_checks,
        "handle_centroid_metadata_rebaseline": handle_centroid_rebaseline(),
        "verification": {
            "geometry_files_before_after_and_current_identical": len(geometry_hashes),
            "all_three_consumed_mount_frames_and_sampled_thicknesses_exactly_unchanged": True,
            "original_prior_reaction_owner_and_mount_owner_hashes_unchanged": True,
            "original_reaction_rows_exactly_unchanged": len(screen["demand_rows"]),
            "prior_screen_bytes_unchanged": True,
            "CAD_or_large_grid_rerun": False,
        },
        "claim_boundary": "Only provenance and gap/source-export qualifications were amended. The nominal native0.05mm face gap is not uniform exported-STL clearance. This rebaseline adds no contact, physical capacity, material, strength or sharing validation.",
    }
    output = HERE / "joint-screen-semantic-rebaseline.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"output": str(output.relative_to(ROOT)),
                      "original_screen_sha256_preserved": screen_hash_before,
                      "accepted_final_manifest_sha256": final_hash,
                      "verification": result["verification"]}, indent=2))


if __name__ == "__main__":
    main()
