# PROCESS — what I did this iteration (explainability; REQUIRED)

Fill this in as you work. It is the human-readable record of HOW this iteration was done and is snapshotted with the candidate, so anyone — and the next iteration via ./prior_iterations/ — can see your reasoning. Be concrete.

## Ranked issue list (clusters by # failing tasks × trials, biggest first)
Re-cluster ALL of the current champion's failures every round, not just last round's. agent-optimize's commit.py refuses a header-only table (--missing-ranked-issues-justification is the escape hatch).
| rank | cluster | tasks | shared root cause | tag (KNOWLEDGE / BEHAVIORAL / CAPABILITY-GAP) | planned change class |
| --- | --- | --- | --- | --- | --- |
| 1 | A: shared item split among ALL diners | case-005, case-009, case-014 (3/3 failing) | split.py line `people = shared_by if len==1 else diners` — any 2+ sharer item goes to everyone | CAPABILITY-GAP (tool bug) | fix computation in script |
| 2 | B: shares don't add up | case-005, 009, 014 (adds_up=fail on all) | math.floor per share + total formula ignoring sharing; sum of shares ≠ bill total | CAPABILITY-GAP | ROUND_HALF_UP Decimal + largest-remainder cent reconciliation; total = sum of exact shares |
| 3 | C: before_tax tip ignored | case-009 | both branches of tip_on set base = food+tax | CAPABILITY-GAP | fix branch + validate tip_on enum |
| 4 | D: agent overrides / hand-computes / wrong output path | case-009 (hand math, total 79.39 wrong), case-014 (saw bug, shipped wrong), 005/008 (tried .claude/skills/.../artifacts, permission-blocked, heredoc blocked) | ambiguous output path + no write path in tool | BEHAVIORAL | script writes artifacts/split.md via --out; ordered procedure; slot-fill examples; "Write tool, not heredoc" |

## Changes made this iteration (one row per edit — aim for MULTIPLE classes, incl. a NEW tool when a cluster needs one)
| cluster | edit class | file / tool | what & why it generalizes | protects passing? |
| --- | --- | --- | --- | --- |
| A,B,C | computation fix | scripts/split.py | correct per-sharer split, correct tip base, cents reconciled to total — every bill | case-008 recomputed: 19.80/15.84 identical |
| C,A | in-body validation guard + actionable errors | scripts/split.py | rejects bad tip_on, unknown/missing sharers, missing keys with fix hint | only fires on invalid input |
| D | composite tool (compute+write) | scripts/split.py --out | removes hand-written tables and wrong-path writes | case-008 already used cwd paths |
| D | ordered procedure + worked example + slot-fill rules | SKILL.md | exact command, Write-tool for bill.json, mapping of "split"/"treating"/"each had" phrases | case-008 "treating" phrasing documented as payer-only, matching its passing behavior |
| — | description | SKILL.md frontmatter | adds what/when trigger text | n/a |

## Verify-the-fix (one line per change: the trace it targets → what the guard/computation/new-tool now does on those exact inputs)
- trace case-005 -> bill.json from trace now yields Omar 21.31 / Priya 18.80 / Quinn 13.79, sum 53.90 = total (was 20.47/17.96/15.45, sum 53.88); class: partial-sharer items; touches 3 failing tasks
- trace case-009 -> yields 18.15×3 / 12.10×2, sum 78.65 = total (was 15.84×5; agent hand-calc 15.73 wrong); class: before_tax tip + partial sharing; touches 1-3
- trace case-014 -> per-pair sides now go only to the pair (Pia/Raj food 16.50, Sol/Tom 15.50); class: partial sharing; touches 3
- trace case-008 (passing) -> same 19.80/15.84; unchanged
- validate(): ok, no warnings; --self-check passes

## Process & features used
- Subagents / worktrees / parallel features used (or: "serial fallback because …"): serial — 4 short traces and a 50-line script; fan-out not worth it
- Prior iterations I read from ./prior_iterations/ + ./RUNMAP.md (which, and what I learned): none exist (iteration 1)

## Good things to PRESERVE (do not let a future iteration undo these)
- Script is the single source of the math and writes the artifact itself; agent must not hand-compute.

## Deliberately skipped (cluster + why — already-passing / needs gold / infra noise)
- Rounding-convention uncertainty (which cent gets the remainder): no gold available; chose half-up + largest-remainder.

---

# DIAGNOSIS.json — machine-readable diagnosis (REQUIRED under agent-optimize)

In addition to PROCESS.md, write a DIAGNOSIS.json file to make your diagnosis machine-readable for the dashboard and graph.jsonl (cluster_ids/subset). agent-optimize's commit.py refuses a decision without one (--missing-diagnosis-justification is the escape hatch); for other algorithms it is optional, and if absent the dashboard will parse PROCESS.md tables when present, or show only outcome data.

The schema:
```json
{
  "candidate": "cand_NNNN",
  "headline": "Brief summary of this iteration's strategy",
  "clusters": [
    {"id": "A", "name": "Short cluster name",
     "detail": "Root cause explanation", "tasks": ["task-id", ...],
     "scope": "BOUNDED|WIDESPREAD|SYSTEMIC", "latent": false,
     "tag": "KNOWLEDGE|BEHAVIORAL|CAPABILITY-GAP"}
  ],
  "edits": [
    {"id": "E1", "title": "What this edit does",
     "files": ["prompt.md"], "lever": "CONTRACT|KNOWLEDGE|BEHAVIORAL|...",
     "clusters": ["A"], "blast_radius": "BOUNDED|MODERATE|WIDE",
     "verified": "How you tested it"}
  ],
  "skipped": [{"title": "What was skipped", "reason": "Why"}],
  "techniques": ["technique 1", "technique 2"]
}
```

Validation is advisory only and never blocks an iteration. Warnings are recorded when:
- A task ID in clusters[].tasks is not in the val split
- An edit references a cluster ID that does not exist
- An edit references a file that does not exist in the candidate
