# cap-evolve demo: `commit-msg`

A tiny benchmark for the cap-evolve optimization engine
([`docs/capevolve-poc.md`](../../docs/capevolve-poc.md), PR #255). It's small
enough to run in a few minutes for a few dollars.

- **Skill under test**: `.claude/skills/commit-msg`. It writes a commit
  message for a described change to `artifacts/COMMIT_MSG`. The seed
  `SKILL.md` is deliberately vague, so the optimizer has something to fix.
- **Dataset**: 12 cases in `eval/dataset/cases/`, each with a change
  description (`input.yaml`) and a gold Conventional Commits type and issue
  number (`annotations.yaml`). cap-evolve splits them 6 / 3 / 3
  (train / val / sealed test).
- **Judges**: four deterministic `check` judges, so judging costs nothing and
  gives the same result every time:

  | judge | passes when |
  |---|---|
  | `file_written` | `artifacts/COMMIT_MSG` exists and isn't empty |
  | `conventional_format` | subject is `type(scope)?: summary`, at most 72 chars, no trailing period |
  | `correct_type` | the type matches the gold type (`fix`, `feat`, `docs`, `refactor`, `test`, `ci`, `build`, `perf`) |
  | `issue_footer` | the last line is a `Token: #N` footer for the gold issue |

`eval.yaml` has no `optimize:` or `reward:` block on purpose. Intake proposes
both into `.capevolve/eval.optimize.yaml` (an `extends:` overlay) and doesn't
touch the benchmark. That's the "no code, no edits to onboard" story.

## What the seed skill gets wrong

On Haiku 4.5 the seed scores about **0.25**. Typical failures from a baseline
run:

- plain subjects such as `Fix crash in login handler …`, with no `fix:` prefix
  (fails `conventional_format` and `correct_type`)
- `Closes #142` in the body, followed by a `Co-Authored-By:` trailer, so the
  last line isn't the issue footer (fails `issue_footer`)
- sometimes it resolves `artifacts/` against the skill's own directory, and
  the write into `.claude/` is denied (fails everything)

The optimizer only ever sees outcome labels such as `correct_type=fail`. It
never sees judge rationale or the gold `annotations.yaml`, and still has to
work out the fixes from that.

## Setup (once)

From the harness repo root:

```bash
uv venv .eval-venv --python 3.12
uv pip install --python .eval-venv/bin/python -e '.[optimize]'
git clone https://github.com/skillberry-ai/cap-evolve.git ../cap-evolve
git -C ../cap-evolve checkout 520ecbe8b9963588eb8d53e3ae29a4ccc1f8436c   # v0.2.0, matches the pin

export PATH="$PWD/.eval-venv/bin:$PATH"
export CAPEVOLVE_SKILLS_DIR="$PWD/../cap-evolve/skills"
```

You also need the `claude` CLI on `PATH`, with Anthropic credentials.

## Demo script

```bash
cd examples/capevolve-demo

# 1. Intake + scaffold + `cap-evolve check` + cost estimate. No LLM calls.
agent-eval-capevolve --max-usd 5 --dry-run
cat .capevolve/eval.optimize.yaml        # what intake proposed
cat .capevolve/project/PROJECT.md        # every resolved/defaulted input

# 2. (Optional) plumbing check: mock optimizer, 3-case pilot, about $0.20, about 2 min.
agent-eval-capevolve --max-usd 1 --max-iterations 1 --num-trials 1 \
  --optimizer mock --pilot-case-ids case-001 case-002 case-003 --runner-budget-usd 0.5

# 3. The real campaign: claude-code proposes SKILL.md edits, gated on val.
#    Runs detached.
agent-eval-capevolve --max-usd 5 --max-iterations 4 --num-trials 1 \
  --optimizer claude-code --optimizer-model claude-sonnet-4-6

# 4. Watch it.
agent-eval-capevolve --status
cap-evolve watch .capevolve/run_*        # one line per gate decision

# 5. Show the result.
RUN=$(ls -td .capevolve/run_* | head -1)
xdg-open $RUN/dashboard.html             # or `open` on macOS
cat $RUN/report.md                       # baseline vs best val, sealed test delta
diff -ru .capevolve/project/seed_capability $RUN/candidates/$(jq -r .best_id $RUN/final.json)

# 6. Land the winner on a `capevolve/run_<ts>` branch (needs a clean tree).
agent-eval-capevolve --apply
```

Each rollout is also an ordinary harness run under
`eval/runs/commit-msg/opt-<case>-<candidate>-<seed>-<id>/`, so `report.html`
and `/eval-compare` work on them as usual.

## Talking points

- **The harness measures, cap-evolve searches.** Every rollout goes through
  the normal workspace → execute → collect → judge → `compose_reward()` path.
- **Gold never leaks.** `annotations.yaml` is never copied into the rollout
  workspace. The proposer gets labels, not rationale.
- **Honest numbers.** The test split is sealed and scored once at the end.
  With only 3 val cases, small gains come back *indecisive*. That's the gate
  working, not a bug.
- **Zero-touch onboarding.** The benchmark has no optimizer-specific config.
  Intake derives everything from `eval.yaml`.
