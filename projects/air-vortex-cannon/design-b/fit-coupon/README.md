# One-joint fit coupon

This is an exact cropped **bottom-front** shell/rail interface from the recovered assembly, with the recommended continuous collar. It allows a later fit trial without first making all three large shells. It is **not a strength or fatigue specimen**: cutting free edges changes stiffness and loads.

Use one each of:

- `reinforced-shell-coupon-print.stl`: approximately36 × 9.78 × 50 mm.
- `original-rail-coupon-print.stl`: approximately49.78 × 27.90 × 25 mm.
- `../print/keyed-adapter-quantity-6.stl`: one adapter for this trial, not six.
- One set of the actual shoulder screw, washers and locking nut specified in [the main handoff](../README.md).

The two coupons preserve the original shell/rail print-axis directions and mating surfaces. They were intersected with a 36 × 42 × 50 mm world-aligned cutting box and translated onto Z0 after applying the original print transform. Their print exports reimport as single watertight, consistently wound components. See `coupon.json` and [build_fit_coupon.py](../build_fit_coupon.py).

No print has started. Inspect the real0.4mm slice, especially the shell collar lower ledge, key/bore paths and support cleanup. Keep the intended material/orientation in the trial record.

On cleaned sound parts, check gentle insertion, actual stack/capture play, metal shoulder/washer seating, nominal thread projection versus actual locking engagement, tool access, all-orientation retention and unloaded deliberate removal. Do not force a fit or infer whole-device strength from this coupon. Compare all distinct installed sites later; this represents only one location.
