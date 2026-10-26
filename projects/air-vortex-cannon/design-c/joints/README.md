# Revision C lower-three joint candidate

This candidate changes only the three handle attachments. The upper source rail and its original pins remain in the selected assembly. It adds one continuous inward conical collar to each source shell and uses a matching curved inner keyed adapter, a flat inner metal washer seat, and the existing D5 × 20 shoulder-bolt/M4 capture arrangement. These are unprinted, unqualified design candidates.

The source cone and the source handle receiver slots accept the 15 × 7.4 mm rounded key at all three sites. **No source slot is recut and no groove is added.** The continuous collar has a 15.6 × 7.8 mm opening, slightly smaller than the approximately 16 × 8 mm source aperture. It provides a nominal shear path into added continuous material. The nominal contact-order margin is small and may reverse with real print error; this is not a stiffness or strength result.

Loose curved saddles were considered. They can spread normal pull-through loading, but do not automatically reinforce the original 1 mm slot edge for in-plane shear without justified preload or friction. The collar therefore belongs to a replacement shell print and is not a separate loose part.

There is no extra outer printed pad. The original handle receiver and the OD12 metal washer already provide positive exterior capture, and omitting a pad keeps the assembly smaller. The washer still contacts limited portions of the actual curved/recessed receiver after the free gap closes; this is **not** a literal inner-and-outer conforming saddle pair. No broad exterior bearing area is claimed, and the previous washer finite-element results are not automatically applicable.

The conforming adapter uses the actual world cone axis, including the rear slot's −0.243576 mm tangential offset. The matching native CAD curved faces have 0.05 mm nominal normal clearance. This is an untested face-fit proposal, not a uniform exported STL gap: independent tessellation gives first outward contact at approximately 0.0138 / 0.0133 / 0.0163 mm in the exported front/middle/rear meshes, with no intersection at rest. Independent native STEP intersections confirm no overlap through 0.050 mm and positive overlap at 0.051 mm. Contact supplies no clamp-friction credit.

| Ideal CAD check | Front | Middle | Rear |
|---|---:|---:|---:|
| Adapter intersection with original shell / original handle / reinforced shell / collar | 0 / 0 / 0 / 0 mm³ | 0 / 0 / 0 / 0 mm³ | 0 / 0 / 0 / 0 mm³ |
| Minimum sampled curved adapter body thickness | 3.910 mm | 3.987 mm | 4.008 mm |
| Dominant-plane separation (not exact first-contact travel) | 0.681 mm | 0.692 mm | 0.692 mm |
| Conditional gap interval under inherited assumed stack errors | 0.181–1.431 mm | 0.192–1.442 mm | 0.192–1.442 mm |
| Maximum analytic-cone residual at 134 original-shell ray probes | 0.00295 mm | 0.00572 mm | 0.00770 mm |

The gap intervals use assumed adapter ±0.15, collar ±0.15, rail ±0.10, inner washer ±0.10 mm and shoulder length +0/0.25 mm. These are declared scenarios, not measured printer or supplier tolerances. The annular washer-footprint probes give first-contact travel about 0.750 / 0.760 / 0.742 mm; the dominant receiver plane is not the actual first-contact footprint.

The inner metal washer is ID5.3/OD15/t1.2, outer washer ID4.3/OD12/t1.6, and nut AF7/h5. The outer washer's ID is smaller than the shoulder diameter, so the nut/washer can bottom against metal rather than intentionally clamping the plastic. Nominal thread beyond the nut is 1.4 mm. The simplified reference envelopes do not prove actual undercut/chamfer clearance, thread engagement, locking or torque. All four purchased hardware reference parts per site are **DO NOT PRINT**.

The four metal hardware poses match Revision B to floating-point precision; their meshes use independent tessellation. The C adapter frame is the original inner surface frame, 2.5 mm outward of the B adapter frame. Consumers must use C's supplied matrices and head/nut face coordinates rather than transferring B's local Z numbers.

`build_lower.py` owns the editable build123d geometry. `parts/` holds native STEP and local STL for the three collars and three curved adapters, plus opening tools and simplified hardware references. The opening-tool meshes are Boolean design references, not printed parts. The original source shell is a triangle mesh, so the replacement shell is supplied as a validated mesh union; the new collar itself has native STEP. No triangulated source shell is misrepresented as a reconstructed native solid.

`lower-assembly.json` is the assembly interface. It contains exactly 15 world component meshes, three replacement-shell records and separate collar-reference ingredients. `assembled/` holds the installed world geometry. `reinforced-shells/` contains the three source-shell-plus-lower-collar unions. `validation.json` checks exported topology, source overlap, bounds and actual receiver fit. `contact-validation.json` records washer-footprint probes, hardware-pose comparison and contact-order probes against the actual exported meshes. The shell Boolean uses a 0.002 mm numerical simplification. The originally reported sub-0.001 mm³ source-difference residuals describe the **pre-simplification union**, not the final STL. Actual exported source-removed volumes are 0.731 / 0.581 / 0.370 mm³; upper-half symmetric differences are 0.907 / 0.658 / 0.504 mm³ for shells 6/8/7. All upper source vertices were independently probed against the exports: sampled maximum distances are 0.00301 / 0.00151 / 0.00099 mm. Reverse export-upper-vertex probes returned zero distance to the original source. Thus tiny source facets change in numerical export; the upper surface is not mathematically identical. The collar lies wholly below the barrel axis and there is no deliberately redesigned upper slot/collar or source aperture recut. These numbers are mesh diagnostics, not a physical manufacturing allowance. `metadata-revision.json` records the correction and unchanged hashes of all 57 STEP/STL files; geometry and poses remained frozen.

Print geometry is selective and keeps metal out of the plate:

| Print file | Quantity | Envelope, mm | Proposed orientation |
|---|---:|---|---|
| `print/lower-only-shell-6.stl` | 1 | 203.76 × 203.76 × 87.67 | Original source orientation; cone axis vertical |
| `print/lower-only-shell-8.stl` | 1 | 229.40 × 229.40 × 90.22 | Original source orientation; cone axis vertical |
| `print/lower-only-shell-7.stl` | 1 | 249.65 × 249.65 × 88.89 | Original source orientation; cone axis vertical |
| `print/bottom-front-conforming-keyed-adapter.stl` | 1 | 30 × 22 × 18 | Flat washer seat down, bore vertical |
| `print/bottom-middle-conforming-keyed-adapter.stl` | 1 | 30 × 22 × 18 | Flat washer seat down, bore vertical |
| `print/bottom-rear-conforming-keyed-adapter.stl` | 1 | 30 × 22 × 18 | Flat washer seat down, bore vertical |

All supplied STL boundaries were reloaded as closed, consistently wound single solids. Print orientations are proposals: the collar inward ledge, actual nozzle/filament/plate settings, supports and removal, bore/neck layers, and fit still need slicer inspection. There is no profile-verified 3MF and no print has started. A C-specific actual-interface coupon is supplied in `fit-coupon/` with its own source, assembled/print meshes, manifest and instructions. Use it with the front curved adapter and actual hardware for the smallest useful physical fit check; cut edges make it unsuitable as a strength specimen.

Load demands, tool and membrane movement checks live in the owning C studies. Geometry, equilibrium or an elastic proxy does not establish printed durability, fatigue, creep, comfort, safe operation, sealing or vortex performance. No stronger elastic, purchase or physical trial is included here.

Source attribution remains egordv's MakerWorld design, captured under CC BY-NC-SA 4.0; this lower-joint derivative retains that license. Original source files and Revision B were not written by these scripts.
