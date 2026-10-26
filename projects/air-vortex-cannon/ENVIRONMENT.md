# Model and analysis environment

Native CAD/STL/JSON dimensions are millimetres; GLB scene dimensions are metres. Inspect STEP/STL/GLB outputs in a compatible CAD/model viewer without running the source programs. Metal, film and hand reference meshes are not manufactured print pieces.

The preparation environment used Python3.12.12, build123d0.11.1, Manifold3.5.4, Trimesh, NumPy, SciPy, Matplotlib and Pillow. The local washer FE study used Gmsh4.15.0 and CalculiX2.23 with explicit linear-elastic inputs. Its source script records executable paths; another machine needs its own paths. No solver or library binary is bundled.

Owning geometry and rebuild order:

1. `assembly-study/recover_core.py`: core shell/rail/clip datums and nominal assembly.
2. `ancillary-study/model_ancillary.py`, then `assembly-study/assemble.py`: complete17source-part assembly and explicitly assumed flexible-part studies.
3. `design-b/build_collars.py`, `design-b/build_recommended.py`, `design-b/fuse_shells.py`: native collar/adapter CAD, purchased-part reference geometry, all6joint poses and modified shell meshes. `fuse_shells.py` requires Manifold3.5.4.
4. `design-b/build_fit_coupon.py`: small actual-interface coupon, not a strength specimen.
5. The load and usage study README files identify analysis inputs, scripts, accepted result files and proof limits. Parameter changes require relevant export, interface, motion and load checks; old pass records do not qualify a changed design.
6. `presentation/export_models.py` and presentation rendering sources consume the designed geometry. They do not own separate design shapes.

The archive includes accepted local FE input/data files for audit as well as summarized results. Raw solver logs, unused development experiments and Python caches are excluded.

The optional self-contained HTML viewer has no CDN dependency. Its syntax and buffers were checked, but browser security policy blocked local-file UI verification and prohibited workarounds. Native3D exports and inspected static images are the qualified presentation outputs.

No actual printer state, project printer settings, print, purchase or physical material test was changed or performed.
