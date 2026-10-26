# Stock ancillary assembly study

This folder owns reconstruction of the six ancillary source objects only. The full shell/rail/six-pin assembly is owned by `../assembly-study/`. Units are millimetres. Canonical axes are X horizontal, Y up, Z rearward, with outlet plane Z=0 and rear-shell end Z=259.8896408. Source STL meshes remain unchanged.

`model_ancillary.py` provides source-to-canonical matrices, posed original mesh copies, a parameterized sight hinge, central-clamp translation, and schematic film/band envelopes. `ancillary-poses.json` records basis and uncertainty per component. `check_ancillary.py` independently fits the two R2.5 mm sight-axis holes and exposes, rather than hides, candidate central snap interference. `load-sections.json` records source-derived section areas for later load calculations; these are not strength ratings or proven global minima.

## Geometry-supported interfaces

- **Rear clamp:** source axis is Z, centre XY=(435.1999817,127.9999962). Its source Z=2 shoulder is aligned with the rear-shell end; source positive Z points forward. The flange is outside and the sleeve inside. The nominal sleeve radius near source Z=2–3 is 120.484 mm versus the shell lip's 120.584 mm bore, giving approximately 0.10 mm radial clearance before film/manufacturing effects. A full sleeve-vertex scan gives maximum bead radius **121.813675 mm at source Z=5.753664**. In the seated pose it lies forward of the lip; coaxial rigid withdrawal would create approximately **1.230 mm radial overlap** at that lip. This is geometry, not elastic strain or a force prediction. Snap deformation or different removal kinematics remain to be established; no insertion force or retention rating is established.
- **Sight:** the source sight's R2.5 mm hole axis runs along source Y at source X=112.13520, Z=7.86755. Its ear faces are Y=124.8264/129.1264, giving 4.3 mm thickness. The rail fork's inner faces are source Z=10/15, giving 5.0 mm gap; nominal clearance is 0.35 mm per face. After the assembly lead's final rail correction, the canonical pivot is (0,109.31366559,26.76465696). The sight's deployed ring plane is perpendicular to the cannon axis. Its original snap axle is placed with the head shoulder outside the negative-X fork ear; physical retention remains unverified. A positive fold angle rotates the sight rearward about canonical X; the parameter is not a claim that all angles clear the full assembly.
- **Central clamp:** source male ring has a 40 mm flange, source upper flange plane Z=5, and split projections extending to Z=11.55. The cap's base plane is source Z=0 and its finger loop extends in positive Z. The nominal reconstruction sandwiches film between these flange faces, with the cap loop rearward, consistent with the assembly video. The two source pieces have snap-fit contact/interference; rigid collision-free seating and the required deformation are not established by positioning them coaxially.

The static rear-clamp check sampled 102 points and found no penetration over 0.02 mm (maximum numerical depth approximately 0.00000025 mm). A separate central snap probe used 24 actual male outer-face points moved 0.01 mm into the male; all were verified inside the male, and 10 were also inside the cap by over 0.02 mm, with maximum sampled depth 0.0997 mm. This exposes a contact/deformation boundary; it is not a complete snap simulation or a claim that the source part cannot assemble.

**Sight pose qualification:** the deployed fore/aft orientation is `sourceX -> +canonicalY`, `sourceY -> -canonicalX`, `sourceZ -> +canonicalZ`. Both fore/aft choices align the circular hinge, but the opposite choice places the native foot into the rail bridge (three sampled penetrations, maximum 1.506 mm). The corrected deployed pose had no penetration over 0.02 mm among 1,805 selected sight points, with no hinge exclusion. Positive folding poses at 15 and 30 degrees still produced sampled rail interference (maximum approximately 0.359 and 0.285 mm); 45, 60, 75 and 90 degree sampled poses were clear. The latter isolated poses do not establish a clear path through the intervening angles. Keep the core/reference sight in its deployed pose; folding is not qualified. `sight-pose-checks.json` retains both candidate pose tests and the exact matrices.

## Original-video observations

Source: [egordv's original assembly video](https://www.youtube.com/watch?v=NKO3LCNGTJY), directly inspected in the browser on 2026-10-25.

- Around 2:28 the central finger loop is on the outside of the bag diaphragm.
- Around 3:03 two bands are tied to the opposite front-annulus eyelets.
- Around 3:23 two additional bands are joined with the carabiner; around 3:48 this is connected to the front anchor loops.
- Around 4:08 the return loops pass through the central pinch-ring hole; around 4:18 they wrap around the outside central ring.
- Around 5:38 the sight is deployed above the front of the top rail, with its ring approximately perpendicular to the cannon axis.

The four-band graph therefore has two front anchors feeding a carabiner junction and two additional bands continuing to the moving membrane centre. The actual unstretched lengths, knots, elasticity, exact junction position and force sharing are unknown. The default midpoint junction is a display parameter, not a static equilibrium solution. Front anchor aperture centres are approximately (+/-72.730,0,4.050995) in canonical coordinates, with axes along Y.

## Usage envelopes and explicit assumptions

The nominal film outer edge is represented at Z=261.8896408, radius 116.8533 mm; the rigid centre clamp has radius 20 mm. The idealized annular cone translates its inner edge by a study stroke while retaining the outer edge. It has zero thickness and no constitutive law. Its exported STL is a visualization/clearance surface, **not a printable part**.

An assumed 60 mm pull requires about 17.6% more annular surface area than a flat annulus. The source bag is visibly wrinkled, but its captured slack is unmeasured. `membrane_requirements()` reports necessary geometric area and meridian-length bounds. It does not prove a bag pattern, actual strain, maximum travel, membrane forces or ring performance. Load and movement conclusions must remain conditional on stated slack and elastic assumptions.

The central cap and male ring move together rearward with `stroke`; the annular clamp stays fixed. Rubber-band line segments indicate topology only. There are no measured dynamic timings, rebound, fatigue or material properties in this reconstruction.

## Data use

Import `model_ancillary.py` without side effects to call:

- `make_transforms(rear_plane=..., stroke=..., sight_fold_degrees=..., film_gap=..., junction_z=...)`
- `load_meshes(**same_parameters)`
- `membrane_mesh(rear_plane=..., stroke=...)`
- `band_graph(rear_plane=..., stroke=..., junction_z=...)`
- `membrane_requirements(stroke=...)`

Source provenance is retained in `../source/egordv/mesh-inventory.json`; base design is egordv / MakerWorld designer profile 348811, displayed CC BY-NC-SA 4.0. No source mesh was modified, no software installed, and no print or purchase started.
