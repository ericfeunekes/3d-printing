# Revision C files and rebuild environment

Start with [the selected design and investigation](README.md). The selected manufactured meshes are only the six files listed in `joints/print/README.md`; the fit coupon has its own instructions. Metal, collar ingredients, film/hand proxies and the rejected optional handle study are not additional selected print parts. No printer profile, slice or physical qualification is included.

Preparation used Python3.12.12, build123d0.11.1, Manifold3.5.4, Trimesh, NumPy, SciPy, Matplotlib and Pillow. No runtime binaries are bundled. The scripts use the existing project's read-only Python environment during preparation; another machine needs its own compatible installation. Manifold can be installed normally; the preparation-only `/tmp/vortex-manifold` path is a convenience fallback.

Keep the relative folder layout when unpacking. `source/egordv/` contains untouched originals. `assembly-study/` and `ancillary-study/` contain the recovered source assembly/poses. A small number of original B/helper files and prior load records are included because C imports or audits them; they remain background inputs, not a recommendation to manufacture B. The complete earlier B package remains separate.

Run study commands from the unpacked workspace using relative script paths, as shown in their README files. Some preserved study scripts require canonical paths for their input-hash bookkeeping; do not mix aliased absolute paths such as `/tmp` and `/private/tmp` in one invocation. The C assembly consumer canonicalizes its own script path and is checked by rebuilding from an extracted package.

For geometry rebuild, recover the source assembly first if its existing outputs are missing; then run `design-c/joints/build_lower.py`. `design-c/handle/build_handle.py` rebuilds only the rejected comparison grip. Run `design-c/assembly.py` and `design-c/render_views.py` after the owning outputs exist. Each study README identifies its own audit/reproduction procedure; preserve historical numerical records and their semantic-rebaseline sidecars. Recompute into a disposable copy rather than overwriting the delivered evidence.

CAD/STL/JSON use millimetres. GLB scene coordinates use metres. The complete original source was supplied as STL despite `STEP` appearing in filenames; STEP exports represent the newly modeled CAD ingredients, not an editable conversion of every source mesh.

The package uses native GLB and inspected static views. It does not include the old unverified HTML viewer. No print, purchase, runtime installation, printer-setting change or physical test was performed for Revision C.
