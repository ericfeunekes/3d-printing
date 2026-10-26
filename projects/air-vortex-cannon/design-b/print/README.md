# Selective manufactured meshes — Revision B

Millimetres, 100% scale. These are CAD prototype exports, not a sliced printer project.

| File | Quantity | Bounds X × Y × Z, mm |
|---|---:|---|
| `reinforced-shell-6.stl` | 1 | 203.76 × 203.76 × 87.67 |
| `reinforced-shell-8.stl` | 1 | 229.40 × 229.40 × 90.22 |
| `reinforced-shell-7.stl` | 1 | 249.65 × 249.65 × 88.89 |
| `keyed-adapter-quantity-6.stl` | **6 copies** | 30 × 22 × 18 each |

The adapter file contains one component; arrange six copies only after a useful fit trial. Its flat base is on Z0 and the bore is vertical. Shells retain their original axis/orientation; the inward collar ledges need appropriate supports and accessible cleanup, to be inspected in the intended slicer.

The receiving printer record is Bambu Lab X2D, 0.4 mm nozzle. Bare geometry fits the main-hotend 256 × 256 × 260 mm envelope; the largest shell leaves only about 3.18 mm per side before brim, skirt, supports or exclusions. No toolpaths or print estimates were generated. Use actual plate/filament profiles; do not borrow unrelated pegboard settings.

Retain original source objects **1, 2, 3, 4, 5, 9, 10 and 17** from `../../source/egordv/`. Replace original shells6/8/7 with the files here, and omit original split pins11–16. Metal reference shapes in `../parts/` are dimension-based purchased-part models, **not printable substitutes**.

For the small initial trial, see `../fit-coupon/`. Cut coupons are fit evidence only; their free cut edges change stiffness and cannot qualify whole-cannon loads. All six actual installed locations remain distinct acceptance checks.

Owning CAD, assumptions, hardware list and validation: [main handoff](../README.md).
