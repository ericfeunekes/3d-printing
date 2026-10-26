# Full usage and service-envelope study

**Scope:** conditional CAD geometry of the recovered stock cannon and recommended Revision B, under the user-approved explicit assumptions. These calculations do not prove real printed strength, friction, fatigue, membrane behaviour, tool fit, human comfort or vortex performance.

## Authoritative final outputs

- [Recommended usage/service results](recommended-usage-results.json) — actual three fused shell meshes, retained source structure and all 30 proposed joint components; final corrected deployed sight; no hinge-point exclusion.
- [Off-axis results](offaxis-results.json) — four end positions at 60 mm axial travel and ±10.5796 mm lateral or vertical centre displacement (10° geometric pull direction).
- [Refined continuous tool/entry certificates](continuous-envelope-certificates-refined.json) — final continuous geometric bounds. Keep the [unrefined certificate](continuous-envelope-certificates.json) and [refinement record](certificate-refinement.json) as the explicit provenance of the formerly inconclusive top-rear case.
- [Slim top-rear tool option](slim-tool-option.json) — the one bounded alternative tool requirement, outside body OD no more than 11 mm, length 30 mm. No purchased tool was measured or approved.
- [Semantic input rebaseline](semantic-rebaseline.json) — preserves old/new assembly metadata hashes and checks identical geometry and service poses.
- [Hand/diaphragm proxies](proxy-results.json), [usage section](usage-envelope.png), and [six-site service section](service-envelope.png).

The initial `usage-results.json` and initial wrong-handed sight diagnostic CSV are **development diagnostics**, not the final sight or recommended-design acceptance result. They are excluded from the handoff manifest. The authoritative corrected source sight comparison is [ancillary sight-pose checks](../ancillary-study/sight-pose-checks.json); the final recommended sight table is in `recommended-usage-results.json`.

## What was modeled

The 17 source rigid pieces are reconstructed in a common millimetre frame: X horizontal/tangent, Y up, Z rearward. Revision B replaces six pins with six keyed adapters plus purchased-metal reference components, and uses the actual exported fused reinforced shells. The recommendation's source-datum revision is 2.

The moving central cap and male ring translate axially in seven assumed positions from 0 to 60 mm in 10 mm steps. The schematic carabiner lies on the axis at a display midpoint. Four elastic edges follow the observed two-front/two-rear topology; their assumed tube radius is 1.5 mm. Rest lengths, stiffness, knot geometry and the actual carabiner equilibrium position are unknown. Attachment regions are trimmed by 8 mm and the central tie region by 20 mm rather than falsely claiming those knots are contact-free.

The membrane is a zero-thickness annular conical surface with outer radius 116.8533 mm and a 20 mm rigid central-clamp radius. Its outer edge is fixed at Z=261.8896408 mm. It is a motion envelope, not a recovered bag shape or constitutive model. Film contact at the central and perimeter clamps is excluded explicitly. In the four off-axis cases, the inner edge is displaced and that displacement fades linearly to zero at the outer edge; the central rigid pieces are not tilted.

Generic hand proxies are chosen ellipsoids, not measured anthropometry. The illustrated grip-hand proxy is centred at `[0,-155,110.4]` mm, with radii `[32.5,45,32.5]` mm; the intended handle contact is excluded. Pull-hand proxies follow the central clamp. Their sampled clearances are not proof of finger articulation, comfort or suitability for any child/adult.

## Results and their limits

### Operation

Seven axial positions and four off-axis end positions found no selected rigid/film/band sample more than 0.02 mm inside the actual recommended fixed geometry. Positive clearance fields include conservative lower bounds; they are not measurements of exact minimum real-world gaps.

There is also a stronger continuous geometric result for the rigid central pieces. Using their complete mesh radial envelopes, all axial positions 0–60 mm and any XY translation with magnitude no more than 10.5796 mm remain radially separated from the fixed structure by at least:

| Rigid piece | Continuous radial separation bound |
|---|---:|
| Central male ring | 24.4189 mm |
| Central cap/pull loop | 21.0924 mm |
| Carabiner, held on the assumed axis | 47.6046 mm |

This result requires the stated rigid orientations and assumed carabiner path. It does not resolve the source central snap interface: the nominal cap/male reconstruction has approximately 0.10 mm intended/interpreted contact interference, requiring flex or pose calibration. Rear-clamp release also remains a source flex/tilt problem; the maximum coaxial bead overlap is about 1.23 mm radially. Those are not erased from the analysis.

### Sight

The corrected deployed sight pose is clear in the final full recommended check with no hinge exclusion. The original mirrored orientation was rejected after it produced about 1.51 mm penetration.

Folding is **not qualified**. Corrected sampled 15° and 30° positions intersect the source top rail by approximately 0.359 and 0.285 mm. Clear isolated 45–90° positions do not establish a traversable path. The new joint parts add no sampled fold collisions at the checked positions; the retained source cam/stop geometry is the unresolved issue. Use the deployed pose for the core and recommended presentation.

### Service

All six exact CAD head/nut datums were checked, not just one representative joint:

- 12 static tool positions: an interior R2 × 35 mm cylinder for a chosen 2.5 mm hex-key shaft envelope and an exterior R6 × 30 mm cylinder for a chosen 7 mm nut tool-body envelope.
- Six interior rear-entry corridors. The tool is translated from the rear opening into each installed position, with the membrane unloaded and out of the corridor.
- Six bolt withdrawals, sampled at 0/5/10/15/20/25/30/35 mm inward travel, after removing the nut and outer washer. The own adapter/bore remain. The inner washer has nominal contact; the largest reported apparent overlap is about 0.000007 mm, below the study's 0.02 mm reporting threshold.

No sampled penetration over 0.02 mm was found in those service cases. The continuous tool/entry certificates go further than those coarse stages:

| Envelope family | Count | Smallest certified whole-envelope CAD clearance |
|---|---:|---:|
| Interior tool, static | 6 | 2.0487 mm |
| Interior tool, complete rear entry | 6 | 1.5505 mm |
| Exterior R6 tool, static | 6 | **0.02994 mm**, top rear, after refinement |

The last number is deliberately not described as robust physical access: manufacturing/assembly error or a different tool can consume it. The separate **OD≤11 mm top-rear tool-body option** evaluates a practical narrower envelope while leaving the other five exterior sites at R6. Its whole-envelope continuous CAD clearance bound is **1.01965 mm**, from 21,376 boundary samples, a 0.183974 mm cover radius, and 2,097 refined triangle queries. This is a tool-size requirement, not a verified purchased socket or tool-wall strength rating. Actual tool size, reach and grip must still be checked.

Service state matters. A tool cannot appear inside a closed bag diaphragm. The interior route assumes the unloaded membrane is removed or held clear. This does not prove the real rear clamp can be unsnapped without damage, nor that a real hand can carry out that sequence. Purchased thread and nyloc models are envelopes, not a simulation of thread engagement or locking.

## Why the continuous certificates are stronger than point sampling

For each chosen tool cylinder, both its side and end caps are covered by a grid with a calculable maximum distance to a checked point. The exterior grid has a cover radius of about 0.2102 mm; the interior grid about 0.5371 mm. Distance to an obstacle is 1-Lipschitz, so a conservative minimum sample distance minus that cover radius bounds the entire boundary. Rear-entry translations add half the maximum 1 mm translation step. Every closed connected obstacle is shown not wholly inside the tool AABB, excluding a hidden obstacle contained entirely within a clear tool boundary.

The independent proof reviewer checked the cover formula and translation inequality, all 37 obstacle meshes' watertight/consistent/one-component conditions, and the equality of all 12 sampled cylinder AABBs with their analytical boxes for the frozen normals/grid. These certificates are specific to these axes and grids; arbitrary parameter changes need those preconditions rechecked.

Mesh-derived AABB, radial and local axial-slab bounds establish many outside points conservatively. Ambiguous points use triangle proximity and closed-mesh containment. The radial-bound implementation was checked against known box and annulus geometry in [bound-sanity.json](bound-sanity.json). Refinement replaced 1,669 insufficiently tight top-rail bounds with actual triangle queries. A replay using bidirectional X-ray containment agreed, with zero ray-disagreement fallbacks. No physical tolerance or deflection is hidden in these digital bounds.

## Input provenance and metadata-only rebaseline

The calculations preserved their original assembly JSON hash:

`5741d10d62f7e97ac4c52399aff9d07fd589e951db9800e203f2fea183246022`

The owner later added explanatory `gap_basis` text only; the current assembly JSON hash is:

`0da393cbfee8e15170a6922520c1d0588d93fee1bd9dc96c5bd5487c4e7d9e0b`

The during-run hash mismatch remains visible rather than being overwritten. `semantic-rebaseline.json` independently confirms all 33 geometry mesh hashes, other governing input hashes, and all 12 reconstructed tool origins/axes are unchanged. This qualifies that metadata mismatch for these geometry calculations, not an unrelated narrative/material-capacity claim.

## Membrane area and the next physical checks

At 60 mm axial pull, the chosen cone requires about **17.6339% more annular area** than a flat annulus. At the four 10° off-axis end positions, the triangulated warped envelope requires about **17.7089% extra area**. A bag may supply this as slack/wrinkles; it is not a prediction of elastic film strain. The assumed axial shape sweeps about 1.0299 litres geometrically, which is not actual discharged air or proof of a vortex ring.

The next physical checks remain: actual bag slack and thickness, band rest lengths/force/routing, printed interface fit and retention, controlled unloaded service, actual tools/hands, and the hardware/washer/printed-part load capacity covered separately by the load study. No print or purchase was performed by this study.
