# MA run — 2026-09-18

This directory contains the reconstructed Mastercard (MA) harness run prepared from the repository's current schemas, rubrics, valuation policy, and public primary-source inputs.

## Final state
- Core score: 78.35 / 100
- Ex-valuation score: 81.28 / 100
- Classification: Emerging Outlier
- Archetype: Compounder
- Hard Vetoes: cleared in the reconstructed decision record
- IC state: NORMAL
- Mechanical position range: 0-2%
- Macro purchase pacing: 0.50x
- Frozen price: $565.24
- Locked Bear / Base / Bull: $291.77 / $520.71 / $778.54

## Important limitation
The execution environment could inspect this GitHub repository and public filings but could not run the repository locally byte-for-byte because direct GitHub/SEC networking from the execution container was restricted. Files in this directory are therefore a functional reconstruction, not a claim that local `python harness.py ...` generated the exact bytes.

The detailed limitation is preserved in `README_EXECUTION.md`. The Stage 0 financial pack, deterministic valuation model, aggregate, digest, final verdict, EV report, and IC report are included for auditability.
