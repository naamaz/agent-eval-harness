# Results: cap-evolve on split-bill, run 2 (2026-10-22)

- **Run:** `.capevolve/run_20261022_153019` (curated copy in `results/run2/`)
- **Skill model:** claude-haiku-4-5. **Optimizer:** claude-code with claude-opus-5-5.
- **Settings:** 5 iterations, 1 trial per case, $10 cap, 4 workers.
- **Cost and time:** $2.03 for skill runs plus $2.55 for the optimizer, about $4.60. Took 15 minutes.
- **Result:** 1 candidate accepted (`cand_0001`), 4 rejected. Once validation hit 1.0, the remaining candidates were no-ops.

This run fixes run 1's setup bug. `eval.yaml` now allows the skill to run
`python3 …/split.py`, so the original skill really executes its buggy script.
Run 1's record is in `../capevolve-bill-split-run1/`.

## Score per case (reward 0–1)

"Why the original lost points" is read from each run's transcript and judges.

| Split | Case | Before | After | Why the original lost points |
|---|---|---|---|---|
| train | case-002 | 1.00 | 1.00 | — (everyone shared everything; the bugs don't apply) |
| train | case-003 | 0.25 | 1.00 | **script bug:** shared pizza split among all 4 diners |
| train | case-004 | 0.25 | 1.00 | **script bug:** "tip before tax" ignored |
| train | case-006 | 1.00 | 1.00 | — |
| train | case-010 | 1.00 | 1.00 | — |
| train | case-011 | 0.00 | 1.00 | wrote files under the protected `.claude/` folder, so no result file |
| train | case-012 | 1.00 | 1.00 | — (script was blocked; Haiku did the math by hand, correctly) |
| train | case-015 | 1.00 | 1.00 | — |
| val | case-005 | 0.25 | 1.00 | **script bug:** shared naan split among all 3 diners |
| val | case-008 | 1.00 | 1.00 | — |
| val | case-009 | 0.45 | 1.00 | **script bug:** salad shared by 3 split among all 5; shares don't add up |
| val | case-014 | 0.25 | 1.00 | **script bug:** onion rings and fries split among all 4 |
| **test** | case-001 | 0.00 | 1.00 | no result file (protected `.claude/` folder) |
| **test** | case-007 | 0.25 | 1.00 | **script bug:** shared roll and edamame split among all 4 |
| **test** | case-013 | 0.00 | 1.00 | no result file (protected `.claude/` folder) |
| **test** | case-016 | 0.58 | 0.67 | **script bug** before. After: one cent given to Yara instead of Xavi\* |

| Split | Before | After |
|---|---|---|
| train (8) | 0.688 | 1.000 |
| val (4) | 0.488 | 1.000 |
| **test (4, sealed, scored once)** | **0.208** | **0.917** |

**What caused the original's lost points:**
- **9 of 16 cases:** the script's math bugs, mostly the shared-dish bug, plus tip-base and rounding.
- **3 of 16 cases:** writing into the protected `.claude/` folder.
- **The rest scored 1.0 already.**

\*case-016 is a flaw in the dataset, not the skill. Xavi and Yara have
identical shares, so the leftover cent is a genuine tie. The answer key breaks
ties by name order, and nothing in the story states that rule. Fix: change one
of their prices, or accept either answer.

## What changed (seed → cand_0001)

The optimizer's diagnosis named four failure groups:
1. a shared item was split among all diners;
2. the shares didn't add up;
3. the "before tax" tip was ignored;
4. the agent did math by hand or wrote to the wrong path.

**`scripts/split.py`: the code fixes.**
- **Shared-dish bug:** `people = item["shared_by"] if len(...) == 1 else diners` became `people = item["shared_by"]`, so a shared dish is split only among its sharers.
- **Tip-base bug:** the dead `before_tax` branch was replaced by `base = food + tax if tip_on == "after_tax" else food`.
- **Rounding bug:** `math.floor` on floats was replaced by `Decimal` with round-half-up, plus a step that nudges leftover cents so the shares add up exactly to the bill total.
- **Wrong total:** the script's separate "bill total" formula was removed; the total is now the sum of the exact shares.
- **New: validation of `bill.json`**, with readable `ERROR:` messages (missing fields, unknown names, bad `tip_on`).
- **New: `--out artifacts/split.md`**, so the script writes the result table itself.
- **New: `--self-check`**, built-in tests.

**`SKILL.md`: the instruction fixes.**
- **Strict 3 steps:** write `bill.json` with the Write tool in the working directory (not inside `.claude/`), run the script with `--out`, check and report.
- **"Never do the math by hand; the script's numbers are final."**
- **Rules for reading the story:** "X and Y split fries" → only X and Y; "each had a burger" → one item per person; "X is treating Y" → X pays; and the before/after-tax tip wording.
- **A worked example** turning a story into `bill.json`.
- **A self-check step:** a shared dish should appear only for the people who shared it.

## Honesty checks

- **No leaked answers:** none of the 48 test-run transcripts touched `annotations.yaml`, `gen/reference.py` or `gen/bills.yaml`.
- **Sealed test:** the test cases (001, 007, 013, 016) were scored once, at the end. The optimizer saw only train and validation outcomes, and only as labels (`adds_up=fail`), never the judges' reasons.
- **Small numbers:** 4 validation and 4 test cases, 1 trial each. The gate needed a gain above 1 standard error (0.18 here); cand_0001 gained +0.51 on validation. Treat 0.21 → 0.92 as a strong signal on a small sample, not a precise measurement.

## Where to look

- `results/run2/dashboard.html`: open in a browser for charts, the heatmap and diffs.
- `results/run2/report.md`: cap-evolve's own summary.
- `results/run2/candidates/cand_0001/`: the winning skill, plus `DIAGNOSIS.json` and `PROCESS.md`.
- `eval/runs/split-bill/opt-*/`: one harness run per test run (transcripts, `report.html`).
