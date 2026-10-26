# Revision C usage and lower-joint service geometry

This checks the actual frozen Revision C lower-three collar/adapter assembly with the original handle/grip location retained. It is conditional nominal CAD geometry, not a physical use, tool, human, strength or airflow validation.

The authoritative [full results](usage-results.json) preserve every input SHA256 before and after the run; inputs unchanged: **True**. The [compact summary](summary.json) hashes those full results. The [post-run input and pose verification](input-and-pose-verification.json) rechecks all 43 input hashes and the six exact C/B tool origins and axes. Reproduce with the existing Python environment by running [check_c_usage.py](check_c_usage.py), then [summarize_c_usage.py](summarize_c_usage.py).

## Whole fixed assembly

All 26 fixed obstacle meshes are closed, consistently wound, connected, positive-volume solids. They comprise source sight axle 1, corrected deployed sight 2, upper rail 3, original handle 4, rear clamp 10 and upper pins 11–13; three actual lower-only replacement shells 6/8/7; and 15 C lower-joint components. Lower pins 14–16 are removed. Integrated collars are included in the replacement shell meshes and not double-counted. Original source and Revision B files were read without mutation.

## Sampled motion and service

Seven axial positions 0/10/20/30/40/50/60 mm and four end positions at 60 mm with centre displacement ±10.5796 mm in X/Y check separate central rigid meshes, chosen film vertices and trimmed R1.5 mm band paths against the full fixed assembly. Central rigid pieces retain their source orientation; the carabiner stays on its assumed axial display midpoint.

All three lower joints have an inside R2 × 35 mm cylinder and outside R6 × 30 mm cylinder at the supplied exact head/nut datums, a rear-entry corridor, and bolt withdrawal at 0/5/10/15/20/25/30/35 mm. Own target hardware is excluded only for intentional tool contact. Withdrawal retains the own adapter/bore, shell and inner washer, after removing the outer nut/washer. These cylinders are chosen tool envelopes, not measured tools. Interior entry requires an unloaded membrane removed or held clear.

| Check family | Minimum reported clearance mm | Maximum sampled penetration mm | Limiting obstacle |
|---|---:|---:|---|
| axial motion | 0.155502 | 0 | stock-6 |
| offaxis end positions | 0.218434 | 0 | stock-6 |
| lower three static tools | 2.590490 | 0 | stock-8 |
| lower three rear entry | 2.590490 | 0 | stock-8 |
| lower three bolt withdrawal | -0.000007 | 6.52227e-06 | bottom-middle--inner-M5-wide-washer-reference |
| deployed sight | 0.000071 | 0 | stock-3 |

No sample exceeds the 0.02 mm penetration reporting threshold. Positive clearance values can be conservative geometry lower bounds rather than exact nearest distances. Any small negative withdrawal value is explicitly retained in the JSON; it is not rounded into an exact no-contact assertion. Bolt withdrawal is sampled, not continuously certified.

The deployed sight table excludes intentional source axle/hole contact, with no sight points excluded. Folding remains unqualified because of the retained source cam/stop issue already identified in the original study.

## Continuous bounds with explicit preconditions

Tool cylinder sides and endcaps are covered by a grid with a known radius. Distance to a closed obstacle is 1-Lipschitz, so the minimum conservative point distance minus the cover radius bounds the complete cylinder boundary. Rear entry adds half the maximum 1 mm translation step. Every connected obstacle has a point outside the complete swept tool AABB, excluding hidden whole-obstacle containment. Analytical and sampled cylinder AABBs agree to the recorded numerical tolerance. Low bounds are refined with actual triangle distance when necessary. Containment requires agreement from four oblique rays along two independent lines, with the original library query used on disagreement.

| Tool family | Count | Minimum continuous CAD clearance lower bound mm | Limiting joint |
|---|---:|---:|---|
| inside-tool-static | 3 | 2.053347 | bottom-middle |
| outside-tool-static | 3 | 3.239628 | bottom-front |
| inside-tool-rear-entry | 3 | 1.554948 | bottom-middle |

These are recalculated C lower-three results. The old all-six B checks do not automatically establish C. No manufacturing/assembly/deflection tolerance is credited by the nominal numbers.

Complete moving-mesh radial bounds certify all axial positions 0–60 mm and any XY centre translation magnitude ≤10.5796 mm, under the retained rigid orientations and on-axis carabiner assumption:

| Rigid source piece | Continuous radial separation lower bound mm |
|---|---:|
| obj_17_PinchRing3.STEP.stl | 24.418856 |
| obj_5_PinchRingCap3.STEP.stl | 21.092427 |
| obj_9_RubberBandCarabiner01.STEP.stl | 47.604602 |

## Chosen hand, film and elastic envelopes

The grip-hand ellipsoid stays at [0,-155,110.4] mm with radii [32.5,45,32.5] mm; intended source handle 4 contact is excluded. Seven pull-hand ellipsoids have radii [35,37.5,40] mm and follow the chosen axial clamp path. Exact closest obstacle triangle queries in each ellipsoid's scaled frame bound the whole chosen ellipsoid, with centre containment checked. All chosen hand ellipsoids clear their checked fixed obstacles: **True**. The smallest lower bound is **1.725793 mm**, for the grip proxy against bottom-middle--M4-nyloc-envelope-reference. This does not model actual fingers, reach, grip force, articulation or comfort.

The film is a zero-thickness annular cone warped linearly for the four off-axis cases; actual bag thickness/slack/wrinkles are unknown. Central/perimeter clamp contact zones are excluded explicitly. The 60 mm axial cone requires 17.6339% more available annular area than the chosen flat annulus. This is a slack/geometry requirement, not film strain or expelled-air evidence. Band radius, rest shape, routing and midpoint are chosen; no elastic force equilibrium is solved.

Source central snap contact and rear-clamp release deformation remain unresolved source issues. These calculations provide no FDM strength/fatigue/creep, hardware locking, real tool/hand suitability, sealing or vortex-performance proof. No print, purchase or physical test was performed.

## Rejected containment diagnostic

The pure ±X containment shortcut was rejected after both rays misclassified points in the inner washer's open hole when they lay almost in its end-face plane. The [ray regression](ray-containment-regression.json) checks 215 such queries across all three washers against a triangle-derived empty axial-cylinder bound and the original library signed query; the corrected oblique-ray method agrees exactly and all 215 queries lie outside. The earlier `usage-results-axis-ray-diagnostic.json` and its matching `input-lower-assembly-axis-ray-diagnostic.json` are development diagnostics, excluded from acceptance. Their apparent 0.65 mm washer overlap is a rejected numerical artifact. The final full run above was rerun after the metadata freeze and preserves identical before/after hashes.
