"""Correct bill splitter: the gold answer every case is scored against.

Never shipped with the skill. The optimizer never sees it.
"""
from fractions import Fraction


def split(bill: dict) -> tuple[dict[str, int], int]:
    """Return ({diner: cents}, total_cents). Shares always sum to the total."""
    diners = bill["diners"]
    food = {d: Fraction(0) for d in diners}
    for item in bill["items"]:
        price = Fraction(str(item["price"]))
        if item.get("paid_by"):
            food[item["paid_by"]] += price
        else:
            for d in item["shared_by"]:
                food[d] += price / len(item["shared_by"])
    tax_rate = Fraction(str(bill["tax_percent"])) / 100
    tip_rate = Fraction(str(bill["tip_percent"])) / 100
    exact = {}
    for d in diners:
        tax = food[d] * tax_rate
        base = food[d] if bill["tip_on"] == "before_tax" else food[d] + tax
        exact[d] = (food[d] + tax + base * tip_rate) * 100  # in cents
    total = int(sum(exact.values()) + Fraction(1, 2))  # round half up
    # Largest remainder: floor everyone, hand the leftover cents out by size of remainder.
    shares = {d: int(exact[d]) for d in diners}
    leftover = total - sum(shares.values())
    for d in sorted(diners, key=lambda d: (-(exact[d] - int(exact[d])), d))[:leftover]:
        shares[d] += 1
    return shares, total
