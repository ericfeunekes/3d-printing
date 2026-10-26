# 3D-printing workspace

Start with [README.md](README.md), then the owning project's README. The project README selects the current design; historical files and successful exports do not by themselves qualify a part for printing or use.

- Keep each build's CAD, source assets, manufacturing files and observations together under `projects/<name>/`. Update its entry in the root README when adding or changing a build.
- Preserve downloaded originals and attribution. Record source URLs, license, date and hashes before changing source-derived geometry. Each asset retains its own license; do not apply one project's license to future builds automatically.
- Keep one geometry owner per part. Derive exports and views from it, with units and print/assembly transforms stated. Distinguish CAD clearance, slicing, physical fit and measured strength/performance.
- Keep current instructions portable. Preserve old absolute paths inside immutable evidence, but put runnable current commands and environment assumptions in the project README. Do not silently rewrite old verification records after a change.
- Track useful native CAD and STEP/STL/3MF exports. Do not commit credentials, environments, caches, generated bundles or unrelated personal files. Keep intentional analysis logs when they are evidence.
- Adding assets does not authorize purchases, starting prints or changing printer state. Follow the user's actual instruction for those actions.

The current air-vortex project keeps its original internal paths to preserve reviewed scripts and hashes. Its README is the entrypoint; old `START-HERE` and revision READMEs are dated history. The research note in Drive is a pointer/research record; this repository owns the maintained CAD and project assets after import.
