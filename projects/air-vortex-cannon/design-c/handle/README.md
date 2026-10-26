# Handle decision

Keep the original handle4 at its original assembly transform and retain the assumed grasp **[0, −155, 110.4] mm**. A rearward grip was investigated, but neither 15 nor 30 mm at the same height passes the existing hand-envelope check around the new middle capture joint. Lowering the rearward grip trades away its small pull-moment benefit and can obstruct nut-tool access. These are model tradeoffs, not measurements of a person's comfort.

[Before/after geometry](handle-before-after.png) and the [actual-mesh section](handle-clearance-section.png) show the selected original and one optional **[0, −175, 140.4] mm** example. The example is a review prototype, **not the recommended print**: it clears the chosen hand envelope and static parts, but blocks the assumed middle exterior tool.

## Geometry and outputs

- [build_handle.py](build_handle.py) is the only owner of the optional replacement geometry. It removes only the original hanging grip below Y = −123 mm within Z = 70–135 mm, keeps the three-receiver rail, and joins a new 25 mm wide native grip/web. Rear shift, drop, grip size, edge radius, cut and throat datums are parameters.
- [handle-validation.json](handle-validation.json) records the original source hash/pose, parameters, volumes, COM, protected receiver volumes, collision checks and print transform.
- [optional-handle-assembled.stl](optional-handle-assembled.stl) is the fused optional handle in assembly millimetres. [optional-handle-print.stl](optional-handle-print.stl) is the same single component with its broad side on the plate: **180.8355 × 114.3985 × 25 mm**. The transforms preserve scale.
- [optional-grip-native.step](optional-grip-native.step) contains the exact new native region. The original source was supplied only as STL despite `STEP` in its name; the whole revised handle is therefore a Boolean mesh, not a wholly native STEP reconstruction. The retained original rail and new native STL are intermediate exports from the same owner.

The optional whole handle is watertight, consistently wound and one connected solid after STL round trip; its volume is 110,345.2494 mm³ and its uniform-solid COM is [0.00333, −142.77445, 125.53338] mm. Its three protected receiver regions have **0 mm³ changed material** against the original. All original mounting positions and original receiver geometry remain unchanged. The new native region intersects no actual C shell, adapter, hardware or retained stock part. The whole handle retains the original small nominal mesh contacts with shells7/8; these are not new penetration introduced by the grip.

## Clearance and service

[final-proxy-clearance.json](final-proxy-clearance.json) checks the analytic ellipsoid with radii [32.5, 45, 32.5] mm against actual C shells and capture components. It scales actual obstacle triangles into ellipsoid coordinates and minimizes their distance to the origin. This checks the whole proxy against those triangle surfaces; it is stronger than the previous sparse boundary-point sampling.

| Assumed grasp XYZ / mm | Chosen hand-envelope result |
| --- | --- |
| [0, −155, 110.4], original | Clear; conservative whole-envelope lower bound 1.72579 mm |
| [0, −155, 125.4], rear15 | Middle bolt/washer/nut/adapter surface points lie inside proxy |
| [0, −155, 140.4], rear30 | Middle bolt/washer/nut/adapter surface points lie inside proxy |
| [0, −175, 140.4], rear30/down20 | Clear; conservative whole-envelope lower bound 1.50292 mm |

Only intended handle/rail contact is excluded. These ellipsoids are chosen geometric envelopes, not measured anthropometry or a knuckle/finger articulation model. A conflict does not prove a real person cannot use a grip; a positive gap does not prove a comfortable grip.

[motion-service-checks.json](motion-service-checks.json) checks the same R6 × 30 mm exterior tool example used by the prior study. The original grip intersects none of the three tool volumes. The optional grip intersects the **middle tool by 413.662 mm³**, so its service access is unresolved. Both handles remain separated from the prior taut-film/straight-band and central-clamp motion schematics over the assumed 0–60 mm axial stroke; actual bag wrinkles, elastic routing, knots and hands remain unmodeled.

## Force path and physical limits

The optional grip carries hand force through its long curved throat into the retained original rail, then through the three original receivers and new C keys/washer/bolt captures into the shells. The load distribution among these points, the native-to-retained throat section, original rail/root capacity, printed layer bonds and hardware locking are unproved. A valid solid, fillets and balanced external forces establish no strength rating.

The proposed broad-side print keeps the main Y/Z load path in the layer plane. Actual receiver bridges, support access, material, nozzle and printer profiles need slicer review. No slicing, print, purchase, stronger elastic, comfort trial or strength test was performed.

Build order, using the established environment: `build_handle.py`, `check_final_proxy.py`, `check_motion_service.py`, then `render_handle.py`. The C lower-joint outputs must exist before the final proxy check. The original/source and B packages are untouched.
