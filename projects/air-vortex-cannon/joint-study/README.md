# Joint architecture study

This is a local connection comparison for the parent's full-cannon revision. It is **not** an accepted installed assembly or a print package. All original source meshes remain unchanged. The native owner is `build_options.py`; its helper functions are importable without running the example export.

## Recommendation and alternatives

Prefer the parent's **metal shoulder-bolt connection with keyed printed adapters**, subject to actual six-site geometry and load checks. Its head and threaded nut provide capture; its shoulder supplies a defined metal clamp stop rather than relying on a loose keeper or on a printed snap arm. Retain an entirely printed threaded stud/nut only as an optional unqualified experiment.

| Approach | Useful function | Principal remaining issue |
|---|---|---|
| Original split pin | One piece, easy assembly, no hardware | Snap insertion strain, arm release, root/layer fracture, thin-shell slot damage |
| Revision A keeper | Blocks one inward arm motion | Keeper itself has escape paths; no proven loaded retention; does not reinforce shell |
| Ordinary bolt + metal sleeve + washers + printed pads | Explicit capture and metal clamp bypass | Seven components/site; custom sleeve length; washer does not solve in-plane shell bearing alone |
| Shoulder bolt + two wide washers + nut + printed pads | Combines bolt and compression stop; six components/site | Actual grip stack/tolerances, tool access, small intentional running play, shell capacity and physical print fit |
| Custom printed stud/nut | Two pieces/site; no purchased hardware | Printed thread flank strength, layer bonds, creep, fit and anti-backoff unproved |

The shoulder version is mechanically clearer, but six sites mean 36 components versus six original pins. It should earn that complexity through demonstrated retention and servicing benefit. It does not establish improved aim, ring coherence or power.

## Modeled outputs

- `parts/`: valid STEP/STL examples for an ordinary-bolt/sleeve connection and a custom printed threaded stud/nut. These use a **representative assumed 6 mm grip**, not the recovered final assembly.
- `comparison.json`: example dimensions, native solid volumes, valid-solid results and uncertainties.
- `shoulder-hardware/`: dimension-based reference solids for shoulder bolt, M5/M4 wide washers and M4 nyloc envelope. Hardware is reference geometry, **not printable replacement hardware**.
- `build_shoulder_study.py` / `shoulder-stack-study/`: a coherent representative shoulder stack and exact stack arithmetic. `stack.json` labels its assumed 6 mm grip and does not claim six-site installed clearance.
- `mesh-checks.json`: all examined exports were watertight, consistently wound and single component. Native CAD validity was separately checked during export. This establishes export integrity, not capacity.

`make_inner_adapter` defaults to X along the cone generator toward increasing radius, Y circumferential tangent, Z outward surface normal. `radius` is inner shell radius at the contact datum. The conical contact is derived from the cone itself; the interior bolt/washer seating face is planar. `axis_normal=False` gives an explicitly different radial-axis variant. `key_end_z` and outer adapter `base_z` are independent to avoid double-counting capture play.

The representative printed option contains true custom coarse helical geometry, nominal diameter 6 mm and pitch 1.5 mm, with a matching relieved nut. It is **not an ISO M6 thread**, and has no demonstrated anti-backoff provision. It must not be called fully captured under use merely because its axial thread overlap exists in CAD.

## Measured versus assumed geometry

Horizontal sections of the three stock shells at source Z20/40/60/75 mm give cone slopes 0.096168/0.096142/0.096177. Their half angles are approximately 5.493/5.492/5.494 degrees. This supports a common 5.492-degree nominal cone. Radius varies by location, so saddle radius must be set per installed site.

The original slot's thin dimension is about 8 mm; source pin depth 7.3 mm. The representative key is 14.8 or 15.0 mm long by 7.4 mm wide against the approximately 15.8 mm minimum axial slot length. Those are proposed manufacturing clearances, not proven printed fit. The actual rail slots are tapered/chamfered; a rectangular slot calculation is not full installed collision proof.

The source assembly lead recovered actual pin insertion normal tilted about 5.492 degrees, with the broad pin base inside the barrel and the barbs outside through the rail. Helpers were updated to the normal-axis frame accordingly. Final poses and grip stacks remain owned by `assembly-study/core-assembly.json` and the parent's recommended assembly, not this representative example.

## Shoulder stack reasoning

Parent-selected reference: Elesa/Ganter `5-M4-16`, shoulder diameter 5 mm, shoulder length 16 mm, M4 thread length 8 mm, head diameter 9 mm, head height 4 mm, hex socket A/F2.5/depth2.5. M5 wide washer is ID5.3/OD15/thickness1.2; M4 wide washer ID4.3/OD12/thickness1; nut envelope AF7/height5.

With inner printed base thickness B, actual normal grip G, shoulder length L, inner washer W, and desired total capture gap c:

`outer adapter thickness = L - W - B - G - c`.

For B4, W1.2, c0.25, L16, this becomes `10.55-G` mm. A minimum 2 mm outer plate therefore requires G≤8.55 mm. Added 2 mm inner shell reinforcement increases G; do not freeze a 16 mm shoulder before checking every actual stack. A 20 mm shoulder gives `14.55-G`, but moves the external washer/nut/tool envelope 4 mm outward.

The shoulder length's published +0.25 mm tolerance, actual washer thickness and printing deviations change the capture gap. The nominal gap is **not** a guarantee. Do not add a second 0.25 mm gap at the key end: let the key stop slightly recessed from the actual rail face and seat the outer pad on that face. Otherwise the design may permit double the stated movement.

The metal shoulder stop keeps tightening clamp load out of the shell/printed stack only when the metal washer genuinely seats against the shoulder and the complete tolerance stack retains positive play. The manufacturer explicitly warns that tightening torque is limited by small shoulder/transition bearing points, not class 12.9 alone. No tightening torque is prescribed here.

## Load and use limits

- Wide washers and conformal saddles spread radial pull-through or local bending. Without credited friction or bonded material, they do not automatically reduce in-plane bearing stress at the same 1 mm shell slot edge. Parent's local continuous reinforcement must be modeled as actual added shell material if credited.
- M4 socket-head diameter 7 mm is smaller than the 8 mm slot width; a head alone is not backup capture through a failed printed adapter. Wide metal washers on both ends are more defensible. The selected shoulder head diameter 9 mm is larger, but the wide washer still improves local bearing.
- A nonclamped captured joint intentionally permits some movement. D5 shoulder in a 5.4 bore gives 0.4 mm diametral allowance; 7.4 key in an 8 mm slot gives 0.6 mm total allowance. Do not credit a tighter aim or airtight seam merely from metal capture.
- Model service tool paths: 2.5 mm hex key at the interior head, 7 mm nut tool outside, plus whole bolt withdrawal and access with the film unloaded/held clear. Bare-part clearance is not tool clearance.
- Neither CAD thread geometry nor reference steel grade establishes the actual supplied fastener or printed material strength. No force, torque, life or ring-performance rating is established by this study.

## Hardware sources

- [Elesa/Ganter shoulder screw publication](https://www.elesa-ganter.hr/siteassets/PDF/EN/ISO%207379.pdf), row5-M4-16, including length tolerance and torque warning. Reference solids are newly constructed from stated dimensions; original manufacturer drawings/models were not copied.
- [Bossard wide washer publication](https://www.ruuvikeskus.fi/attachments/h7cpz.pdf), rowsM4/M5, manufacturer-authored PDF hosted by distributor.
- [Bossard nyloc publication](https://www.tme.eu/Document/b2162b4e06623b32cc382f0f3f1ca4a6/B4_BN161.pdf), M4 AF7/height5 envelope.
- [Bossard socket-head screw publication](https://docs.rs-online.com/574c/A700000011307398.pdf), M4 D7/head4 reference used for ordinary-bolt alternative.

No purchase, print or installation occurred. Original egordv source attribution and CC BY-NC-SA4.0 remain in the owning project; no separately restricted community lock geometry was used.
