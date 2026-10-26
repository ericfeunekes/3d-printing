# Adding a build

Create `projects/<short-name>/README.md` and add one link to the root build table. Start with the files the project actually has; do not create empty source, export or test directories.

The project README should make these things easy to find:

1. What is being made, the selected version, and its current state: concept, CAD, sliced, printed, fit-tested or otherwise measured.
2. Original downloads, source URLs, license, author and any source hashes. Keep originals unchanged and distinguish them from derivatives.
3. Editable geometry and the command/tool/version that owns it; units, assembly placement and intentional manufacturing exports.
4. Which files and quantities to print, target printer/nozzle/material, orientation, support needs and whether settings were actually sliced or merely proposed.
5. Assembly/hardware and actual observations, including failed attempts, measured fit changes and what remains untested.

Use descriptive folders when the file count needs them. A project can use `source/`, `cad/`, `print/` and `evidence/`; an imported project may retain its existing layout when changing it would break its scripts or provenance. Its README explains the map.

Keep generated release bundles in `dist/`, not alongside their tracked source. Store large assets through LFS or releases when appropriate; GitHub [warns above 50 MiB and blocks regular Git files above 100 MiB](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github). No LFS installation or blanket tracking rule has been configured for the initial collection because its individual imported files are below 50 MiB.

Record actual print feedback with the exact revision/settings it concerns. A geometry check, successful slice or supplier material name does not establish measured fit, strength or durability. Update the selected design after reviewing that evidence; retain earlier revisions as history.
