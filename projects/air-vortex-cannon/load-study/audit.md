# Independent numerical audit

Completed 2026-10-25 by a fresh read-only reviewer. No remaining material finding was reported in the final load-study.

- Independently recomputed all 14 planar load cases and their conical normal/tangent projections. Maximum wrench residual was about 8.0e-11 in the reported force/moment units. The 115.813 N normal and 30.408 N tangential peak demands agree.
- Independently reconstructed all 42 finite-contact cases from the exported contact forces. Force/moment residuals were below 2.1e-10 N and 2.1e-8 Nmm; each contact and bridge constraint met its declared assumed-limit fraction.
- Reconstructed elastic stresses at 400 integration points in each of the five accepted FE meshes from actual input geometry, displacements and material constants. Largest discrepancy was 1.5e-5 MPa/N, at solver-output rounding scale. The quadratic element ordering and stress parsing agree. Integration-point order was checked against [CalculiX source](https://raw.githubusercontent.com/Dhondtguido/CalculiX/master/src/gauss.f).
- Found and resolved one reproducibility defect: the initial script could accept pre-existing parseable `.dat` output after changing input. The current script deletes old solver outputs and always solves the newly written input. All five accepted unit-load cases were freshly replayed after that correction.

This audit checks the calculations against their stated models. It does not establish printed strength, actual stiffness-selected load sharing, nonlinear contact, real transient peaks, fatigue or whole-cannon physical capacity. Those exclusions remain explicit in the owning README.
