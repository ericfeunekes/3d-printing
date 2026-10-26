# Independent statics check

A separate read-only reviewer independently recomputed all 1,944 hand-position sensitivity rows with the closed-form signed Cx equation, including hand force, relocation delta, absolute-couple reduction and fixed-root wrench. Maximum discrepancy was 1.33×10⁻¹⁵ N·m. All 648 fixed-stock-centroid comparison vectors also agreed with direct cross products. No material sign, model or result finding remained.

The review also checked the old scripts without running them in place. Neither the planar reaction solver nor the 3D contact solver uses the hand point. All fourteen old hand moments agreed exactly with independent cross products. The stored planar joint force/moment residual was at most about 8×10⁻¹¹ in the respective units.

The final C lower-joint screen separately verifies retained mount datums and frames, exact reuse of prior demand cases, and final-basis projections. It is a nominal demand calculation with sampled thickness and assumed support/contact models; it is not independent evidence of actual load sharing, curved contact, printed strength, comfort or capacity.

## Metadata-only final-manifest rebaseline

The original numerical screen SHA256 remains `2d1b8edafa7af5be1dec0220523da2ba15ae809cfbcb5486428f7b4c60746146`; its original manifest input hash remains `3895b3e3f76c2d354093fa6d8dbbb7478eb5b70f8d1991daba48f4becdf9940f`. The final manifest is `a929c43cb72985358db654601949dcae3e858ff9305faa5b6aebcae9e5b92949` after metadata qualification of source-export differences and native versus STL gap.

`rebaseline_joint_screen.py` records the transition in `joint-screen-semantic-rebaseline.json`. It verifies the producer's before/after hashes against all 57 current geometry files, compares every consumed aperture/key/bridge dimension and all three consumed mount frames/sampled thicknesses exactly with the original screen snapshot, and checks all 98 original world-reaction rows against the unchanged prior reaction owner. The prior numerical screen is not rewritten. No CAD solve or large unchanged scenario grid is repeated. This provenance acceptance adds no physical validation.

A second block in the same rebaseline addresses handle-validation metadata. The original results SHA256 remains `7c12c53663195190373cdd19b4a040f20e2c66e359ff15ce00ee204b39a775be`; the original handle-validation input hash `d853f24c282cb408816562948f3e9702e90b29e3ddeb2acb945861a569cebc8c` is retained. Current handle metadata hash `a8b2b08bc3abdf7c117a8c700e451d0964bcb3a0a75da08495774d65039cc708` is accepted after recomputing current optional volume/centroid/grasp accounting and obtaining exact equality with all preserved handle-only stock-accounting results. No hand-position grid is rerun or rewritten. Added middle-tool access limitations remain explicit; the optional handle is not promoted to the selected design.

The reproduction instructions distinguish preserved-history inspection from fresh numerical recomputation. Only the semantic-rebaseline command belongs in this historical bundle's verification recipe. Numerical producer scripts overwrite their outputs by design and must run in a separate workspace copy; their fresh current-input records are not inputs to the historical rebaseline.
