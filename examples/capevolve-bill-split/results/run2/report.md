# cap-evolve run report — run_20261022_153019

- Best candidate: `cand_0001`
- Baseline val: 0.4875 ± 0.1772180859844728
- Best val: 1.0 ± 0.0
- **Held-out test (optimized skills): 0.9166666666666666 ± 0.08333333333333334**  (pass^1=0.750)
- Held-out test (baseline `seed` skills): 0.20833333333333331 ± 0.13819269959814165
- **Test improvement (optimized − baseline): +0.708333**
- Val→test gap: +0.083333 — selection optimism on val; this gap IS the overfitting
- Iterations: 5
- Optimized for: claude-haiku-4-5 (tier mid)

Test was scored exactly once on the sealed split, for BOTH the baseline (`seed`) and the optimized skills — the improvement above is on held-out tasks the optimizer never saw.
