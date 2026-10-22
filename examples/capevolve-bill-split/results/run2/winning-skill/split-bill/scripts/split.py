#!/usr/bin/env python3
"""Split a restaurant bill and write the result table.

Usage:
  python3 split.py bill.json                         # print the split
  python3 split.py bill.json --out artifacts/split.md   # print AND write the table
  python3 split.py --self-check                      # run built-in tests

bill.json:
{
  "diners": ["Ana", "Ben", "Cal"],
  "items": [
    {"name": "Ana burger", "price": 12.00, "shared_by": ["Ana"]},
    {"name": "Fries",      "price": 6.00,  "shared_by": ["Ana", "Ben"]}
  ],
  "tax_percent": 8,
  "tip_percent": 18,
  "tip_on": "after_tax"            # "after_tax" or "before_tax" (required)
}

Rules the script applies:
- An item is split equally among the people in its "shared_by" list ONLY.
- Tax = tax_percent of each person's food.
- Tip base = food ("before_tax") or food + tax ("after_tax").
- Shares are rounded to cents so they add up exactly to the bill total.
"""
import json
import os
import sys
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def validate(bill):
    for key in ("diners", "items", "tax_percent", "tip_percent", "tip_on"):
        if key not in bill:
            fail(f'bill.json is missing "{key}". See the format in this script\'s docstring.')
    diners = bill["diners"]
    if not diners or len(set(diners)) != len(diners):
        fail('"diners" must be a non-empty list of unique names.')
    if bill["tip_on"] not in ("after_tax", "before_tax"):
        fail(f'"tip_on" is {bill["tip_on"]!r}; use "after_tax" or "before_tax". '
             '"tip on the total after tax" -> "after_tax"; "tip on the food / before tax" -> "before_tax".')
    for item in bill["items"]:
        people = item.get("shared_by") or []
        if not people:
            fail(f'item {item.get("name")!r} has no "shared_by"; list who pays for it.')
        unknown = [p for p in people if p not in diners]
        if unknown:
            fail(f'item {item.get("name")!r} names {unknown} who are not in "diners" {diners}.')
        if "price" not in item:
            fail(f'item {item.get("name")!r} has no "price".')


def compute(bill):
    validate(bill)
    diners = bill["diners"]
    food = {d: Decimal(0) for d in diners}
    lines = {d: [] for d in diners}
    for item in bill["items"]:
        people = item["shared_by"]
        portion = Decimal(str(item["price"])) / len(people)
        for d in people:
            food[d] += portion
            lines[d].append(f"{item['name']} {portion.quantize(CENT, ROUND_HALF_UP)}")

    tax_rate = Decimal(str(bill["tax_percent"])) / 100
    tip_rate = Decimal(str(bill["tip_percent"])) / 100
    exact, tax, tip = {}, {}, {}
    for d in diners:
        tax[d] = food[d] * tax_rate
        base = food[d] + tax[d] if bill["tip_on"] == "after_tax" else food[d]
        tip[d] = base * tip_rate
        exact[d] = food[d] + tax[d] + tip[d]

    total = sum(exact.values()).quantize(CENT, ROUND_HALF_UP)
    owes = {d: exact[d].quantize(CENT, ROUND_HALF_UP) for d in diners}
    # Nudge cents (largest rounding error first) so shares sum exactly to the total.
    diff = int((total - sum(owes.values())) / CENT)
    order = sorted(diners, key=lambda d: exact[d] - owes[d], reverse=diff > 0)
    for d in order[:abs(diff)]:
        owes[d] += CENT if diff > 0 else -CENT
    return {"diners": diners, "food": food, "tax": tax, "tip": tip,
            "owes": owes, "total": total, "lines": lines}


def to_markdown(r):
    out = ["# Bill split", "", "| Person | Food | Tax | Tip | Owes |", "| --- | --- | --- | --- | --- |"]
    for d in r["diners"]:
        out.append(f"| {d} | ${r['food'][d].quantize(CENT, ROUND_HALF_UP)} | "
                   f"${r['tax'][d].quantize(CENT, ROUND_HALF_UP)} | "
                   f"${r['tip'][d].quantize(CENT, ROUND_HALF_UP)} | ${r['owes'][d]} |")
    out += ["", f"Bill total: ${r['total']} (shares add up to ${sum(r['owes'].values())})", ""]
    return "\n".join(out)


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--self-check":
        return self_check()
    path, out = argv[0], None
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 >= len(argv):
            fail("--out needs a file path, e.g. --out artifacts/split.md")
        out = argv[i + 1]
    try:
        with open(path) as f:
            bill = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        fail(f"could not read {path}: {e}")
    r = compute(bill)
    for d in r["diners"]:
        print(f"{d}: food {r['food'][d]:.2f} ({', '.join(r['lines'][d])}), "
              f"tax {r['tax'][d]:.2f}, tip {r['tip'][d]:.2f} -> {r['owes'][d]}")
    print(f"Bill total: {r['total']}")
    print(f"Sum of shares: {sum(r['owes'].values())}")
    if out:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        with open(out, "w") as f:
            f.write(to_markdown(r))
        print(f"Wrote {out}")
    return 0


def self_check():
    # Shared item split only among its sharers; after-tax tip.
    r = compute({"diners": ["A", "B", "C"],
                 "items": [{"name": "x", "price": 15, "shared_by": ["A"]},
                           {"name": "y", "price": 4, "shared_by": ["A", "B"]},
                           {"name": "z", "price": 11, "shared_by": ["C"]}],
                 "tax_percent": 9, "tip_percent": 15, "tip_on": "after_tax"})
    assert r["food"]["A"] == 17 and r["food"]["B"] == 2 and r["food"]["C"] == 11, r["food"]
    assert sum(r["owes"].values()) == r["total"]
    # Before-tax tip uses food only.
    r = compute({"diners": ["A", "B"],
                 "items": [{"name": "x", "price": 10, "shared_by": ["A"]},
                           {"name": "y", "price": 10, "shared_by": ["B"]}],
                 "tax_percent": 10, "tip_percent": 20, "tip_on": "before_tax"})
    assert r["owes"]["A"] == Decimal("13.00"), r["owes"]
    # Rounding: three-way split of 10.00 still sums to the total.
    r = compute({"diners": ["A", "B", "C"],
                 "items": [{"name": "x", "price": 10, "shared_by": ["A", "B", "C"]}],
                 "tax_percent": 0, "tip_percent": 0, "tip_on": "after_tax"})
    assert sum(r["owes"].values()) == Decimal("10.00"), r["owes"]
    assert "| A |" in to_markdown(r)
    print("self-check ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
