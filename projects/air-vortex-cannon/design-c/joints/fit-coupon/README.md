# C front-lower fit coupon

This is the actual curved Revision C collar interface, cut from `lower-only-shell-6-assembled.stl`, paired with the actual unchanged source handle receiver. It replaces the earlier flat Revision B coupon for a C fit trial. Both assembled and selectively oriented print STL boundaries were reloaded as closed, consistently wound single solids.

Print one each of:

- `c-conical-collar-shell-coupon-print.stl` — 36.00 × 10.08 × 50.00 mm; original shell print axis retained.
- `original-handle-receiver-coupon-print.stl` — 49.78 × 27.90 × 25.00 mm; original handle print rotation retained.
- `../print/bottom-front-conforming-keyed-adapter.stl` — 30 × 22 × 18 mm; flat inner washer seat down, bore vertical.

Use the actual specified D5/L20/M4 shoulder bolt, ID5.3/OD15/t1.2 inner washer, ID4.3/OD12/t1.6 outer washer, and AF7/h5 M4 locking nut. The metal reference files are **DO NOT PRINT**.

The coupons derive from the actual original/C mating interfaces, with no deliberate mating-surface redesign. They undergo `simplify(.002 mm)` and STL numerical cleanup, so their final surfaces are not mathematically identical to the unsimplified cuts. Independent comparison gives shell/handle symmetric differences of 0.11568 / 0.21868 mm³ and sampled original-surface-vertex distances of at most 0.00162 / 0.00341 mm, excluding cut-plane vertices. These are numerical diagnostics, not manufacturing tolerances or physical fit proof. Check key insertion through the 15.6 × 7.8 collar opening and unchanged source slots, curved face fit, flat inner washer seat, actual shoulder stop, measured positive capture gap, hardware locking/thread projection, unloaded/inverted retention, tool operation and deliberate removal. Clean supports normally; do not scale the coupon to obtain fit.

The 0.05 mm curved-face gap and bore/slot clearances are untested proposals. Actual printer/filament/plate profiles, supports and bore/neck layer paths need slicer inspection. No print has started. These cut edges alter stiffness, so this is a fit coupon, **not a load, fatigue or whole-cannon proof specimen**. All three installed lower sites still require physical fit and access checks.

`../build_fit_coupon.py` reproduces the cuts and transforms. `coupon.json` records exact source hashes, paths, print transforms, topology checks and envelopes in millimetres.
