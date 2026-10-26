# Core, proposed revision and optional adjustments

These views use the actual reconstructed source meshes and proposed CAD exports. They are presentation consumers of the owning models, not a second source of geometry. The core uses the corrected deployed sight orientation. The proposed scene uses the three final fused reinforced shell exports and all 30 new joint components.

## Inspect the design

- **`core-vs-proposed.png`** — complete 3-D comparison. The source body/outlet/manual diaphragm concept stays the same; the six structural connections change.
- **`proposed-cutaway.png`** — labelled whole-assembly cutaway exposing the internal connections and schematic diaphragm/elastic topology.
- **`proposed-joint-detail.png`** — close view cropped from the actual assembly meshes.
- **`proposed-joint-section.png`** — centre section from delivered mesh geometry showing the shoulder, washers, adapter, reinforcement and dominant datum-plane separation. This is not exact first-contact travel or free play.
- **`inspection-viewer.html`** — optional self-contained WebGL viewer. Core/proposed switch, orbit/zoom, shell cutaway and an assumed pull-travel slider. It uses no CDN or network requests.

The native scene files are `core-rest.glb`, `core-pull-60mm-study.glb`, `recommended-rest.glb` and `recommended-pull-60mm-study.glb`. GLB coordinates are **metres**; native CAD, mesh studies and parameter JSON use **millimetres**. These are scene files, not slicer projects. Their round-trip bounds, mesh counts and hashes are recorded in `export-roundtrip.json`.

The core contains 17 rigid source pieces. The proposed scene removes six stock pins, retains eight other original pieces, substitutes three locally reinforced shells, and adds six printed adapters plus 24 metal hardware references: **41 rigid modeled pieces**. Both scenes additionally contain a membrane surface and four elastic-line proxies. Metal reference models are not files to print.

## Reasoning along the way

| Layer | Choice | Reason / condition |
|---|---|---|
| Core design | Preserve the chamber, outlet and modest manual diaphragm mechanism as the baseline. | Provides a common comparison. Changing structure and airflow at once would obscure the cause of any observed improvement. |
| Proposed design | Replace split clips and their loose keeper idea with keyed adapters and shoulder-bolt/washer/nut capture. | Establishes a geometric capture path rather than relying on an insert's friction. Hardware selection, locking and real fit still need physical verification. |
| Proposed design | Integrate reinforcement locally around the shell slots. | Addresses the thin shell in the load path rather than only preventing clip release. Model geometry is not proof of printed capacity. |
| Proposed design | Use a shoulder and washer spacing stop, distinguishing datum-plane separation from actual washer contact. | Avoids claiming that tightening friction safely clamps an unknown FDM wall. Nominal OD12 washer first-contact travel is about 0.74–0.76 mm across six sites; dimensional assumptions expand the possible range. See the design report rather than treating the 0.68–0.69 mm plane separation as free play. |
| Optional adjustment | A repeatable pull reference or guide. | Only after observing actual asymmetric or variable motion; a guide adds friction and complexity. No geometry or performance gain is asserted here. |
| Optional adjustment | Sight calibration and a better supported hand position. | Can separate systematic offset from handling variation. A sight cannot fix an inconsistent pulse. |
| Optional adjustment | Interchangeable outlet comparisons. | A later one-variable experiment against the baseline, not a prescribed stronger nozzle. Ring coherence needs appropriate evidence beyond target movement. |

## What the movement means

The 0–60 mm range is an **assumed study envelope**, not a measured operating stroke or recommended maximum. The central pull parts translate; the illustrative film surface and band junction follow the schematic model. Actual film slack, elastic equilibrium, membrane velocity, contact deformation and airflow are not solved by this viewer. Deployed sight pose is shown; folding travel is not qualified.

The static image renderer uses orthographic triangle projection with painter shading. It does not determine collisions. The scene exports and viewer retain actual model vertices; the cutaway merely hides the near shell half. Use the owning [usage studies](../usage-study/usage-results.json), [recommended usage studies](../usage-study/recommended-usage-results.json), [load analysis](../load-study/README.md) and [proposed CAD record](../design-b/README.md) to assess the evidence and assumptions.

## Verification and limitations

The four GLB exports were reloaded and checked for the expected geometry counts and metre-scale envelopes. Viewer binary buffer sizes and configuration references were checked, and its JavaScript passes `node --check` after substituting the generated data object. The PNG views were visually inspected against the assembly.

**Browser verification blocker:** Browser Use rejected opening the local `file:` viewer URL under its URL security policy, which allows only `http:` and `https:` and explicitly forbids workarounds for that rejection. No alternate browser route or local-server workaround was attempted. The optional HTML viewer is therefore **not UI-verified in this session**. Native GLBs and inspected static views remain available.

Actual printed strength, fatigue, friction, nut locking, manufacturing tolerance, snap behavior, film dynamics, aim and ring coherence are not established by the presentation. No print, purchase, public upload or publication was performed.

## Regenerate

Use the existing read-only toolkit environment documented by the project, with `PYTHONDONTWRITEBYTECODE=1` and a writable temporary Matplotlib configuration folder.

```sh
python presentation/export_models.py --final-shells
python presentation/render_views.py --final-shells
python presentation/render_joint_section.py
python presentation/build_viewer.py --final-shells
```

`scene_data.load_configuration('core'|'recommended', stroke=0, final_shells=True)` returns world-millimetre meshes plus role and movement metadata. The assembled hardware STL paths already include their poses; their metadata matrices must not be applied again.
