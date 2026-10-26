# Final independent review — Revision B

**Verdict: acceptable as a conditional engineering prototype.** This is not a physical load rating, print-profile qualification or vortex-performance validation.

Fresh independent geometry and proof/manufacturing perspectives reviewed the complete current core, recommendation and optional-adjustment handoff. A separate fresh numerical audit recomputed load equilibrium and FE integration-point stresses. Producer checks alone were not treated as approval.

## Accepted corrections

- The first print-oriented shell STL exports gained duplicate/degenerate faces after a rigid inverse transform and float32 serialization. Both print-coordinate and assembled-coordinate exports are now separately reloaded, cleaned within the recorded numerical scope and reloaded again. All delivered aliases are closed, consistently wound, single components and match validation hashes. Installed geometry hashes remained unchanged.
- The original datum-plane gap was not actual washer free travel. The main handoff now distinguishes datum separation, nominal/adverse footprint first contact and physical tolerances.
- Purchased threads are dimensional envelopes; nominal projection is not actual locking engagement.
- Load-point travel assumptions, clearance-study travel and idealized washer supports are explicitly distinguished.
- Source sight fore/aft pose was corrected. Intermediate folding contacts remain visible as counterexamples; folding is not promoted as proved.
- The usage calculations preserve their old metadata hash and explicitly reconcile an explanatory-only JSON change, checking unchanged mesh hashes and service poses.

## Geometry findings resolved / meaningful nulls

All six installed new joints fit the retained modeled geometry. Minimum nominal key/rail clearance is about0.178 mm at the top rear and0.300 mm elsewhere; key/collar clearance about0.400 mm. Each collar has continuous fusion with its shell and about525 mm² of flat adapter landing area. The three reinforced shells and their final print exports each have one closed material component. Print inverse transforms reproduce the assembled envelopes.

Independent geometric probes found clear continuous service corridors for the chosen unloaded tooling and 35 mm bolt withdrawal. Usage-study refined bounds cover all18 chosen tool/entry envelopes; the main OD12 top-rear tool margin is only0.02994 mm. The additional OD≤11 mm tool option is recorded separately in the usage study, with a1.01965 mm ideal-CAD bound, not a purchased-tool guarantee.

All17 original source hashes remain unchanged. The retained source nominal assembly has small inherited seam/rail overlaps, up to about0.134 mm sampled depth, plus flexible snap interfaces. The new collars did not worsen those overlaps. Consequently neither baseline nor recommendation is called a globally interference-free manufactured assembly.

## Load/proof boundary

The fresh numerical audit checked reaction equilibrium, finite-contact wrench constraints and400 FE integration-point stresses per accepted mesh. A stale solver-output cache defect was removed; all accepted unit FE solves were rerun from the written inputs. No remaining material numerical calculation finding was reported.

The washer FE support patches are stated idealizations; sharp-boundary peaks are mesh-sensitive. Nominal printed-section stress screens are demands against analyst-selected assumptions, not actual FDM allowables. Feasible contact LPs are not stiffness-selected reaction distributions or safety factors.

The remaining physical gates are actual stack/washer/shoulder seating and tightening, print layer/support quality, collar/key roots and layer bonds, unchanged handle/rails/elastic eyes/pull loop, impact/creep/fatigue, real film and bands, sealing, actual tools/hands and ring performance. The absence of those observations does not invalidate a conditional prototype; it prevents promotion to a proven manufactured toy.

## Presentation and files

Core/ours/optional reasoning, native CAD sources, STEP/STLs, whole-assembly GLBs and geometry-derived views are included. GLB uses metres; CAD/STL/JSON use millimetres. Metal and human/film proxy meshes are not print parts. The adapter selective file contains one component; quantity is six.

The optional self-contained HTML viewer's JavaScript syntax and geometry buffers were checked. Browser security policy blocked opening its local file URL and prohibited workarounds; its UI remains unverified. The native 3D exports and inspected static views are the qualified presentation outputs.
