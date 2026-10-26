# 3D Printing

Eric's workspace for printable designs, CAD sources, build experiments and the evidence needed to reproduce or improve them.

## Builds

| Project | Current state |
|---|---|
| [Air-vortex cannon](projects/air-vortex-cannon/README.md) | Revision C conditional prototype, with [five-plate Bambu 3MF and separate fit coupon](projects/air-vortex-cannon/design-c/manufacturing/README.md). Not physically printed or qualified. |

Each build has one folder under `projects/` and an owning README that identifies its current design, source attribution, files to manufacture and actual print/test status. Earlier versions stay clearly identified as history.

## Add another build

Follow [Adding a build](docs/adding-a-build.md). Create folders when they hold real files; start with a project README rather than an empty template tree. Put shared printer or material guidance at repository level only after it is useful to multiple builds.

CAD sources and intentional STEP/STL/3MF exports belong in Git. Keep caches, installed environments and duplicate release ZIPs out. Use [Git LFS or release assets for large binaries](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github) before adding oversized assets to history.

Licenses apply per project and source asset: see [Licenses and attribution](LICENSES.md). Repository visibility does not change a downloaded design's terms.

[Contributor/agent context](AGENTS.md) describes the repository's ownership and evidence conventions.
