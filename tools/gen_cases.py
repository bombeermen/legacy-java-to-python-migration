"""Generate test invoices (hand-picked edge cases + seeded random ones) in the legacy input format."""
import random
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "cases" / "cases.txt"


def invoice(inv_id, ctype, region, days_late, items):
    lines = [f"INVOICE {inv_id}|{ctype}|{region}|{days_late}"]
    lines += [f"ITEM {sku}|{qty}|{price}" for sku, qty, price in items]
    lines.append("END")
    return "\n".join(lines)


def edge_cases():
    cases = []
    n = 0

    def add(ctype, region, days, items):
        nonlocal n
        n += 1
        cases.append(invoice(f"E{n:03d}", ctype, region, days, items))

    for qty in (1, 9, 10, 11, 49, 50, 51, 99, 100, 101):          # volume tier boundaries
        add("RETAIL", "EU", 0, [("A", qty, "12.34")])
    for price in ("199.99", "200.00", "200.01", "184.00", "196.01"):  # free shipping boundary
        add("RETAIL", "UA", 0, [("B", 1, price)])
    for region in ("EU", "US", "UA"):                              # every type x region
        for ctype in ("RETAIL", "WHOLESALE", "GOV"):
            add(ctype, region, 0, [("C", 3, "49.99"), ("D", 12, "7.5")])
    for days in (0, 1, 29, 30, 31, 60, 61, 95, 400):               # late fee periods and cap
        add("RETAIL", "EU", days, [("E", 5, "20.00")])
    add("RETAIL", "EU", 0, [])                                     # empty invoice
    add("RETAIL", "EU", 45, [])
    add("RETAIL", "XX", 0, [("F", 1, "10.00")])                    # errors
    add("VIP", "EU", 0, [("F", 1, "10.00")])
    add("RETAIL", "EU", 0, [("F", 0, "10.00")])
    add("RETAIL", "EU", 0, [("F", -3, "10.00")])
    add("RETAIL", "EU", 0, [("G", 3, "0.335")])                    # rounding half-up on 3 decimals
    add("WHOLESALE", "US", 0, [("G", 7, "0.125"), ("H", 3, "1.005")])
    add("GOV", "UA", 30, [("I", 50, "3.333")])
    return cases


def random_cases(count, seed=42):
    rnd = random.Random(seed)
    cases = []
    for i in range(1, count + 1):
        ctype = rnd.choice(["RETAIL", "WHOLESALE", "GOV"])
        region = rnd.choice(["EU", "US", "UA"])
        days = rnd.choice([0, 0, 0, rnd.randint(1, 200)])
        items = []
        for j in range(rnd.randint(1, 6)):
            price = f"{rnd.uniform(0.5, 400):.{rnd.choice([2, 2, 3])}f}"
            items.append((f"S{j}", rnd.choice([1, 2, 5, 9, 10, 25, 49, 50, 75, 99, 100, 150]), price))
        cases.append(invoice(f"R{i:03d}", ctype, region, days, items))
    return cases


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    allc = edge_cases() + random_cases(150)
    OUT.write_text("\n".join(allc) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {len(allc)} invoices to {OUT}", file=sys.stderr)
