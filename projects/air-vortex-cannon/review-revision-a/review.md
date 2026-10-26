# Independent challenge review — Air Vortex Cannon Revision A

Reviewed 2026-10-25. Audience: Eric and his dad, deciding whether the small keeper prototype is worth developing and later fit testing. Artifact: the issued Revision A keeper CAD, meshes, handoff, validation and ZIP. Purpose: limit inward movement of the original split clip arms without changing the manual diaphragm/elastic system. This is an unprinted fit experiment, not a qualified whole-cannon repair.

**Verdict: retain Revision A only as a fit experiment. Findings must be resolved before promoting it to an installed repair.** The main weakness is that an insert intended to keep the original clip engaged has no established retention of its own. No confirmed isolated-part collision, export defect or FDM geometry blocker was found. There is no evidence yet of improved durability, aim, power or ring coherence.

The artifact remained unchanged during review. [Frozen file manifest](frozen-artifact.json) records 31 file hashes. The issued ZIP SHA-256 is `ea23a27f3e2642c77f258fe6b4d5389482430762a79989cf3d7051e3b533eeee`. Six independent read-only perspectives covered geometric interfaces/access, mechanical loads, FDM/fit, code/export/proof/package, science/project value, and whole-artifact/human use. All six returned judgments. Temporary probes were kept outside the design folder.

## Findings and material open decisions

### 1. The keeper is not captured against its own escape

**Consequence:** the clip can lose the added restraint during handling or operation. This is a design acceptance gap; the current handoff already admits unverified self-retention, but its trial does not identify every escape direction.

The clearance variant has 0.05 mm per-face gap even at its widest seating edge, and 0.20 mm per-face gap along its straight stem. The nominal variant reaches zero width gap only at the seating edge. Neither establishes an unloaded clamping force that can be credited for friction. The cap stops deeper insertion; it does not capture withdrawal. See [fit parameters](../revision-a/build_revision.py:24), [profile](../revision-a/build_revision.py:49), and [current handling gate](../revision-a/README.md:41).

There is also an **out-of-plane escape path**. The keeper is a constant 6.8 mm extrusion, and the source U-gap is open through the clip body's 7.3 mm depth. Their 0.50 mm depth difference is not bounded front/back play or capture. Independent sampled translations along that depth direction, from centred to 8 mm offset, found no source-pin penetration. The upward-removal arrow is therefore not the only available exit. A surrounding assembled part might constrain that movement; no verified assembly model establishes that yet.

**Smallest acceptance evidence:** on a sound loose clip, exercise every orientation and front/back movement as well as inversion; then establish what constrains each escape direction in an actual installed joint. Record retention and deliberate removal together. A part that happens to stay in one resting orientation has not passed. Do not rely on unspecified print roughness as the retention mechanism.

### 2. Arm squeeze can encourage movement along the tapered keeper

**Consequence:** a keeper that survives unloaded handling might still migrate during the intended pull/release cycle.

The upper faces widen toward the removal end: half-width rises from 4.3 mm at stock Z=10 mm to 4.45/4.50 mm at Z=12.5 mm. See [taper geometry](../revision-a/build_revision.py:49). For ideal flank contact, the arm's inward force on a right face `x=f(z)` has a removal-direction component proportional to `f'(z)`. The conditional ratios are 0.06/0.08 relative to horizontal contact force for the clearance/nominal profiles. This establishes a possible direction of action, **not a prediction that a real printed keeper necessarily ejects**. Friction, edge contact and arm deflection remain unknown.

**Smallest acceptance evidence:** after the all-orientation trial, observe the keeper during repeated unchanged intended gentle manual operation in the real joint. Progressive lifting or sideways migration fails retention. An unloaded inversion pass cannot settle this failure mode. No numeric friction coefficient, required force or life rating is inferred.

### 3. One connection does not qualify six installed positions

**Consequence:** a fit candidate could be usable in one position but inaccessible, obstructive or unremovable elsewhere.

The handoff anticipates six keepers [at line 15](../revision-a/README.md:15), while the installed trial checks one connection [at line 42](../revision-a/README.md:42). The three shells and two rails have different surrounding geometry. The drawing places a keeper inside an isolated pin; it does not locate the six pins in the assembled cannon. Source print-plate coordinates are not assembly transforms.

The quoted **6.3 mm projection is only the seated envelope**. The intended straight withdrawal needs about **10.3 mm translation** before the rounded foot clears the 12.5 mm clip tips. At that point the keeper reaches about **16.6 mm beyond the original tips**, before allowing grasp/tool room. This is an additional access requirement, not a demonstrated obstruction. A sampled staged path through the isolated pin found no interference, which does not settle surrounding clearance.

**Smallest acceptance evidence:** a keyed view of the installed clip orientations, insertion/removal swept envelope and grasp access at every distinct connection; then check any positions not demonstrated equivalent. Verify full clip seating and clearance from the diaphragm and elastic through normal motion. One successful joint may select a fit candidate; it cannot authorize whole-cannon use of all six.

### 4. Preventing release can move the failure into unchanged parts

**Consequence:** the clip may stay latched while its root, barbs, rail or thin shell slot fails. The keeper has not made the assembly stronger merely by limiting one motion.

It changes no barb bearing area, clip root, slot reinforcement or shell wall. Shear, peel, twisting, outward arm bending and layer separation remain possible. The source shells are approximately 1 mm thick. The handoff honestly acknowledges this [at line 43](../revision-a/README.md:43). Earlier maker reports distinguish clip fracture, intact release and shell cracking; they do not establish a controlled failure rate or load rating.

**Smallest acceptance evidence:** compare a sound actual rail/shell joint with and without the keeper under the same intended modest operation. Record movement, seating, keeper migration and any whitening, cracking or slot damage. Passing loose-clip fit tests is insufficient. Four unspecified rubber bands, a material name and the word “gentle” do not support a numerical capacity or fatigue conclusion.

### 5. Fit and print orientation cannot be separated from the trial result

**Consequence:** a result from one print orientation, supported surface or material may not apply to another, and choosing the tighter variant can mask a manufacturing issue.

The issued widths leave only 0.05 mm per face or zero nominal width allowance [at the final seat](../revision-a/README.md:11). This is a design convention, not a statement of printer accuracy. The side-oriented original clip raises its body about 4 mm above the bed; supports and cleanup affect broad surfaces and can alter fit. It remains an orientation experiment [as described](../revision-a/README.md:27).

**Smallest acceptance evidence:** record the exact clip file, orientation, filament and cleanup condition. Inspect the relevant sliced layers and cleaned surfaces before selecting by insertion, retention and removal together. Do not transfer a successful result to a differently printed clip, force nominal-width fit, or scale the entire assembly to adjust this interface.

### 6. Installed removal and physical variant identity need explicit handling

**Consequence:** the part might be removable in a loose clip yet awkward to service in the real joint; mixed fit candidates could invalidate the trial record.

The eye is 3.2 mm across [in the parameters](../revision-a/build_revision.py:38). It is not a fingertip hole, although the protruding eye may be pinchable. The instruction to remove “through the pull eye” does not identify the grip/tool, unloaded service state or removal sequence [in steps 2–4](../revision-a/README.md:40). No removal impossibility was demonstrated; the interaction is unresolved.

**Smallest acceptance evidence:** demonstrate installation and deliberate removal in the unloaded mounted joint without levering against the shell or disturbing the stock clip. During fit trials, keep one labelled variant on the bench at a time or use separate labelled containers. The two parts differ by only 0.1 mm and have the same overall bounds; filename records cannot identify mixed loose prints afterward. No extra CAD marking is required just to solve that handling issue.

## Challenge to project value and next scientific directions

The keeper addresses a reported reliability failure, so the experiment is defensible. It is not established as the most valuable next improvement in a sound assembly using the intended modest elastic. It adds six pieces and six assembly/removal operations. If the stock configuration does not release during intended use, the extra complexity may not earn its place. Fit success must therefore remain separate from a stock-versus-keeper benefit comparison.

The broader goals remain open: stronger useful target response, easier aim and ring coherence. The keeper leaves the airflow components unchanged [by design](../revision-a/README.md:17). It cannot be credited for those goals without corresponding tests. Establish a stock baseline before committing to additional features:

- **Repeatable diaphragm pull:** plausible, but a guide or hard stop adds friction, complexity or abrupt stopping. Observe the actual membrane before prescribing one.
- **Sealing and outlet finish:** inspect real leakage and edge consistency first. A seam is not evidence of leakage, and smoothing a flow path does not mean rounding away the intended outlet separation edge.
- **Aiming:** distinguish systematic sight offset, handheld movement and shot-to-shot spread. A calibrated sight cannot correct an inconsistent pulse. Compare a fixed support against handheld operation.
- **Ring coherence:** tissue movement measures target effect, not the flow structure itself. Do not call a larger tissue response proof of a better ring.
- **Outlet variants:** change one feature at a time against the baseline. Laboratory formation numbers are not universal household barrel/aperture/pull ratios.

The primary sources support this restraint. [Gupta, Sane & Arakeri (2024)](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0305084) used controlled drive, sealing, nozzle geometry and stopping behavior. [Limbourg & Nedić (2021)](https://www.cambridge.org/core/journals/journal-of-fluid-mechanics/article/formation-of-an-orificegenerated-vortex-ring/B9F8E5CB0B396AEB19D79D3EA509E02B) distinguishes its orifice formation number from maximum-energy stroke. [Thorne's patent](https://patents.google.com/patent/US20040255922A1/en) is aiming precedent, not independent validation of this toy. Exact laboratory dimensions, waveforms and patent performance assertions do not establish an improved household configuration.

## What survived the challenge

- All 17 original source meshes and their inventory agree with the original downloaded archive. All 31 frozen file hashes remained unchanged.
- Every ZIP entry matches the workspace. The omitted auxiliary stock-pin image is not required by the handoff.
- Temporary replay reproduced both keeper STLs, both rigidly transformed source-pin references, the review image and validation data exactly. STEP differences were generation timestamps only.
- Both new parts are single valid CAD solids and watertight, consistently wound, single-component meshes. STEP units are millimetres; the installed rotation is rigid and right-handed. The parts fit the verified X2D main-hotend envelope.
- Independent flat-section checks support no designed keeper overhang in its proposed orientation. The open vertical eye has about a 1.10 mm top ligament; actual toolpaths remain a slicer check.
- Both reported 56,992-point static contact checks reproduce zero sampled penetration. A further isolated-pin staged path probe sampled 18,632 points at 12 translations per candidate and also found none. Neither is complete continuous collision, retention, strength or installed-access proof.
- Prototype status and limits are prominent. No misleading stronger-airflow, range, aiming, strength or safety claim was found. Missing print estimates or a profile-bearing 3MF are disclosed limits of a CAD-only prototype, not an export defect.

One optional code improvement: [the contact script](../revision-a/render_revision.py:81) reports penetration without failing a threshold. Its successful exit means “report generated,” not “contact accepted.” The present zero report is valid. If it becomes an acceptance gate for later revisions, one explicit threshold assertion would be sufficient; a new test framework is unnecessary.

License/provenance statements are consistent with the captured base record: egordv / CC BY-NC-SA 4.0; no separately restricted community lock geometry was incorporated. The independent live MakerWorld retrieval failed in this review, so it supplied no new license verification.

## Disposition

Keep the frozen files as a reviewable fit candidate. Do not promote the design to a successful whole-cannon repair on static geometry or a single loose-clip test. Before a later revision is accepted for use, settle keeper capture in all directions, installed access/removal at all distinct locations, and actual benefit without shifting damage into the shell. A redesign has not been made during this review; no print or purchase has occurred.
