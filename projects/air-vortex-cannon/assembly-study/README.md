# Recovered stock assembly

This is a nominal reconstruction of all 17 downloaded source objects in [egordv's original model](https://makerworld.com/en/models/442826-air-vortex-cannon#profileId-348811). The source STLs are unchanged. The editable assembly owner is the Python placement model, not newly recovered parametric CAD for the source shapes. Base content remains CC BY-NC-SA 4.0.

## Coordinates and outputs

Native meshes, transform JSON and CAD coordinates use **millimetres**. X is horizontal/tangential, Y is up, and Z points rearward along the cannon axis. The front outlet plane is Z=0. The GLB files are exported in **metres** for glTF consumers.

- `recover_core.py`: shell, rail and six pin poses; `core()` returns meshes, raw-source transforms and joint datums.
- `core-assembly.json`: corrected datum revision 2, six complete pin-local matrices, inner/outer shell tangent planes and nominal grip stacks.
- `assemble.py`: `load_assembly(stroke=0, sight_fold_degrees=0)` integrates all 17 original meshes and ancillary evidence; `export_scene()` adds a schematic membrane.
- `full-stock-assembly.json`: all 17 transforms, observation/assumption tags, hand contact and band topology.
- `full-stock-rest.glb`, `full-stock-pull-60mm-study.glb`: complete rest and assumed 60 mm pull study views. The latter is **not** a measured travel or recommended maximum.
- `grip_sections.py`, `grip-sections.json`: source-derived normal sections/rays and closed shell-hole outlines in each joint frame.
- `full-stock-sections.png`: assembled centre-plane section and top-front joint detail.

## Source-supported reconstruction

All three shells share their print Z axis and XY centre (128,128). The nominal axial placements are front 0 mm, middle +84 mm and rear +171 mm, producing rear end Z=259.88964 mm. These offsets follow the actual lip profiles: about 0.022 mm minimum radial clearance at the front/middle overlap and near-contact within approximately 0.003 mm at the middle/rear overlap in the inspected side section. They are a model interpretation, not a physical assembled measurement.

The conical wall slope is 1/10.4, or a 5.4923 degree half-angle. Clip axes are cone normals rather than exactly radial:

- Top outward normal `[0, 0.995409, -0.095712]`.
- Bottom outward normal `[0, -0.995409, -0.095712]`.

The rails are located by their three repeated slots and matching curved contact surfaces. Source axial slot residuals remain in the model rather than being erased: top -0.102/+0.136/-0.034 mm; bottom -0.074/+0.038/+0.036 mm. A 0.244 mm rear tangential source mismatch is likewise retained. Nominal pin centres use the shared interval midpoint where appropriate.

The pin head's broad face is inside the barrel, with split ends pointing outward. This direction was directly inspected in the [designer's assembly video at 4:38 and 4:43](https://www.youtube.com/watch?v=NKO3LCNGTJY&t=278s): the builder reaches inside the barrel and pushes blue clips outward, while the cyan rail remains outside.

The first tangent-plane estimate used the shell slot's side faces at tangential ±4 mm and was biased inward by about 0.07–0.08 mm. **Datum revision 2 corrects this** using the circular shell profile away from the slots. The rail poses then include a 0.10 mm outward normal refinement to avoid the initial small receiver overlap in the inspected sections. These are explicit nominal assembly clearances, not printer tolerance claims.

## Joint interface data

The joint frame origin is the original pin's base centre, with local Z pointing outward. Its broad head upper face lies at local Z=2 mm; the nominal inner cone tangent plane is therefore local Z=2, and the outer shell is approximately Z=3 mm.

The nominal grip stack from the inner shell tangent plane to the rail's dominant external bearing plane is approximately 11.01–11.02 mm at all six positions. The receiver is **not a simple flat 11 mm plate**: local near-hole chamfers and recesses are lower. `grip-sections.json` retains the actual local ray intersections and closed shell opening contours at Z=2.25/2.5/2.75 mm. These holes are approximately 16 × 8 mm with rounded corners; their small positional differences matter when constructing conformal interfaces.

The stock clip pose assumes its broad head face sits against the inner cone. Snap flexure, latch contact, clamp force and printed fit are not established by that rigid pose. Source snap joints can intentionally interfere during insertion; do not convert a rendered assembly into a strength or service claim.

`audit_sections.py` checks exact polygon overlap in the selected pin-local Y=0 centre section. It finds small undeformed source-clip overlaps with the rail: approximately 0.205–0.223 square millimetres around local normal Z=6.78–7.73 mm near the barbs. Source clip/shell section overlap is at most approximately 0.015 square millimetres. These are explicit source snap-contact/pose uncertainties; the stock reconstruction is **not claimed to be a rigid collision-free assembly**. The proposed replacement joint must be assessed separately. A selected 2-D section does not prove complete 3-D collision freedom or deformation behavior.

The transformed handle spans approximately Y=-187.68 to -93.62 mm. Grip sections support an illustrative hand-contact point `[0,-155,110.4]`; this is an explicit assumed grasp, not an observed user's hand pose.

## Flexible and moving components

Ancillary poses come from `../ancillary-study/model_ancillary.py`, whose evidence/status tags are carried into the full assembly JSON. Rear clamp geometry, sight pivot and axis have source-supported datums. Central snap seating and the elastic junction remain explicit nominal/schematic placements.

The membrane model is an annular surface from the rear clamp to the central pull part. It does not model shopping-bag slack, wrinkles, tearing, constitutive behavior or aerodynamic coupling. The band graph preserves the observed four-band topology, but its junction position and line segments do not solve elastic equilibrium. Travel and sight angles are study inputs only.

## What this model establishes

It supplies complete, inspectable rigid-part placement and consistent datums for usage, movement, joint and load studies. It establishes which mesh features support those placements and which positions remain assumptions. It does **not** establish actual printed strength, frictional retention, fatigue, snap insertion forces, a certified operating load, realistic membrane velocity, ring coherence or range. Subsequent analysis must retain these proof boundaries.
