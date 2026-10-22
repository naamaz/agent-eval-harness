# cap-evolve demo: `split-bill`

A small, everyday benchmark for showing the cap-evolve integration (PR #255,
[`docs/capevolve-poc.md`](../../docs/capevolve-poc.md)): **cap-evolve +
agent-eval-harness improving a skill's code and instructions, not just its wording.**

The skill splits a restaurant bill. Its bundled calculator, `scripts/split.py`,
has three seeded bugs that anyone who has split a dinner bill will recognize:

| Bug | What it does wrong |
|---|---|
| Shared dish | A dish shared by 2 people is split across the whole table |
| Tip base | "Tip 18% on the food before tax" is silently tipped after tax |
| Rounding | Shares are rounded down, so they don't add up to the bill |

`SKILL.md` is also vague: it doesn't say where to write files, and it doesn't
say how to handle "Ana is treating Ben to his drink".

**Result** (Haiku 4.5 runs the skill, Opus 5.5 optimizes; about $4.60, 15 min):
on the sealed test cases, **0.21 → 0.92**. The accepted candidate fixed all
three bugs in `split.py` and turned `SKILL.md` into a strict procedure. Per-case
before/after, what changed and the caveats are in
[`results/RESULTS.md`](results/RESULTS.md). The dashboard is
[`results/run2/dashboard.html`](results/run2/dashboard.html), and the full diff
is [`results/run2/seed-to-winner.diff`](results/run2/seed-to-winner.diff).

## Layout

```
.claude/skills/split-bill/   # the skill under test (the seed: vague SKILL.md + buggy split.py)
eval.yaml                    # skill, Haiku runner, 3 deterministic judges, reward weights
eval/dataset/cases/          # 16 dinner stories (input.yaml) + gold amounts (annotations.yaml)
gen/                         # answer-key generator: correct reference calculator + bill specs
results/                     # committed record of the demo run
```

- **Cases:** 16 stories such as "Chloe and Dev shared a pizza ($22)… Ana is
  treating Ben to his drink… tip 18% before tax". cap-evolve splits them
  8 / 4 / 4 (train / val / sealed test).
- **Answer key:** `gen/build_dataset.py` computes the gold per-person amounts
  from `gen/bills.yaml` with `gen/reference.py`. The agent under test is
  denied read access to `eval/` and `gen/`. The optimizer never sees either
  of them, or the judges' reasons, only per-judge labels such as `adds_up=fail`.
- **Judges (all deterministic):**
  - `file_written`: `artifacts/split.md` exists and names everyone;
  - `adds_up`: the shares sum to the bill total, to the cent;
  - `shares_correct`: the fraction of people whose amount is exactly right. It's weighted 2×, so partial progress counts.
- **No `optimize:` block:** intake generates it into
  `.capevolve/eval.optimize.yaml` and never edits the benchmark.
- **`gen/check_seed.py`:** runs the seed script on every gold bill, to confirm which cases the bugs break (6/16 come out correct).

## Run it

From the harness repo root, once:

```bash
uv venv .eval-venv --python 3.12
uv pip install --python .eval-venv/bin/python -e '.[optimize]'
git clone https://github.com/skillberry-ai/cap-evolve.git ../cap-evolve
git -C ../cap-evolve checkout 520ecbe8b9963588eb8d53e3ae29a4ccc1f8436c   # v0.2.0, matches the pin
export PATH="$PWD/.eval-venv/bin:$PATH" CAPEVOLVE_SKILLS_DIR="$PWD/../cap-evolve/skills"
```

You also need the `claude` CLI on `PATH`, with Anthropic credentials.

```bash
cd examples/capevolve-bill-split

agent-eval-capevolve --max-usd 10 --dry-run     # intake + check + estimate, no LLM calls

CAPEVOLVE_WORKERS=4 agent-eval-capevolve --max-usd 10 --max-iterations 5 --num-trials 1 \
  --optimizer claude-code --optimizer-model claude-opus-5-5     # detached, about 15 min

agent-eval-capevolve --status                   # progress, accepted/rejected counts
cap-evolve watch .capevolve/run_*               # live, one line per gate decision
agent-eval-capevolve --apply                    # winner onto a capevolve/<run> branch
```

## Known issues

- **case-016 has a one-cent tie.** Xavi and Yara owe identical amounts, and
  the answer key breaks the tie by name order, which nothing in the story
  implies. The winning candidate gave the cent to Yara and scored 0.67 there.
  A fix is to give one of them an extra item. It's left as-is so the
  committed dataset matches the recorded run.
- **The sample is small:** 4 val and 4 test cases, 1 trial each. Present the result as a strong signal on a small sample.
- **Haiku's file paths:** Haiku sometimes resolves paths against the skill
  folder and gets blocked writing into `.claude/`. That cost the seed 3 of its
  16 cases; the optimized `SKILL.md` fixes it.
