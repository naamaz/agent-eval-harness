---
name: split-bill
description: Work out how much each person owes for a shared restaurant bill — items each person ordered, dishes shared by some of the group, tax, and tip — and write the per-person table to artifacts/split.md. Use when a meal, takeout, or bar tab has to be divided between people.
---

# Split a bill

Do these steps in order. Do the math ONLY with the script — never by hand.
The script's numbers are final: copy them, do not "correct" them.

## Step 1 — Write `bill.json` in the current working directory

Use the **Write** tool (not a Bash heredoc, which is blocked) to create
`bill.json` in the current working directory (NOT inside `.claude/`).

Filling the fields:
- `diners`: every person named, exactly as written.
- `items`: one entry per dish. `shared_by` lists ONLY the people who pay for it:
  - "X had the soup ($9)" → `"shared_by": ["X"]`
  - "Each had a burger at $13" → one burger item PER person, each `["<that person>"]`
  - "X and Y split fries ($5)" → `"shared_by": ["X", "Y"]` (only X and Y — not everyone)
  - "X is treating Y to the drink ($4)" / "X pays for Y's drink" → `"shared_by": ["X"]` (the payer)
- `tax_percent`, `tip_percent`: the numbers given (use 0 if none is mentioned).
- `tip_on`: `"after_tax"` if the tip is on the total after tax / with tax;
  `"before_tax"` if the tip is on the food / pre-tax amount / subtotal.

Example — "Ana and Ben had pizza. Ana had a salad ($8), Ben pasta ($14).
They shared garlic bread ($6). Tax 8%, tip 18% before tax." →

```json
{
  "diners": ["Ana", "Ben"],
  "items": [
    {"name": "Salad", "price": 8.00, "shared_by": ["Ana"]},
    {"name": "Pasta", "price": 14.00, "shared_by": ["Ben"]},
    {"name": "Garlic bread", "price": 6.00, "shared_by": ["Ana", "Ben"]}
  ],
  "tax_percent": 8,
  "tip_percent": 18,
  "tip_on": "before_tax"
}
```

## Step 2 — Run the script; it writes the result file

From the current working directory run exactly:

```bash
python3 .claude/skills/split-bill/scripts/split.py bill.json --out artifacts/split.md
```

It prints each person's food/tax/tip/share, the bill total, and `Wrote artifacts/split.md`.
It creates `artifacts/` itself. If it prints `ERROR: ...`, fix `bill.json` as the
message says and run it again. Do not read the script's source.

## Step 3 — Check and report

- Check each person's food line in the output matches what they ordered
  (a shared dish should appear only for the people sharing it). If not, fix
  `bill.json` and re-run Step 2.
- "Sum of shares" equals "Bill total" — the script guarantees it.
- Do not rewrite `artifacts/split.md` by hand. Reply with the per-person amounts
  exactly as the script printed them.
