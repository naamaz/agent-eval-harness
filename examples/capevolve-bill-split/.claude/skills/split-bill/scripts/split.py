#!/usr/bin/env python3
"""Split a restaurant bill.

Usage: python3 split.py bill.json

bill.json:
{
  "diners": ["Ana", "Ben"],
  "items": [{"name": "Pizza", "price": 22.00, "shared_by": ["Ana", "Ben"]}],
  "tax_percent": 8,
  "tip_percent": 18,
  "tip_on": "before_tax"            # or "after_tax"
}

Tax and tip are shared in proportion to what each person ordered.
"""
import json
import math
import sys


def main(path):
    with open(path) as f:
        bill = json.load(f)
    diners = bill["diners"]
    food = {d: 0.0 for d in diners}
    lines = {d: [] for d in diners}

    for item in bill["items"]:
        # A shared dish is split between the people sharing it.
        people = item["shared_by"] if len(item["shared_by"]) == 1 else diners
        portion = item["price"] / len(people)
        for d in people:
            food[d] += portion
            lines[d].append(f"{item['name']} {portion:.2f}")

    tax_rate = bill["tax_percent"] / 100
    tip_rate = bill["tip_percent"] / 100
    owes = {}
    for d in diners:
        tax = food[d] * tax_rate
        tip_base = food[d] + tax
        if bill.get("tip_on") == "before_tax":
            tip_base = food[d] + tax
        tip = tip_base * tip_rate
        owes[d] = math.floor((food[d] + tax + tip) * 100) / 100
        print(f"{d}: food {food[d]:.2f} ({', '.join(lines[d])}), tax {tax:.2f}, tip {tip:.2f} -> {owes[d]:.2f}")

    total = sum(bill["items"][i]["price"] for i in range(len(bill["items"])))
    total = total * (1 + tax_rate) + total * tip_rate * (1 + tax_rate)
    print(f"Bill total: {total:.2f}")
    print(f"Sum of shares: {sum(owes.values()):.2f}")


if __name__ == "__main__":
    main(sys.argv[1])
