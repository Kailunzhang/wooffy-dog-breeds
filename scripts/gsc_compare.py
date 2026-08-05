"""Closed-loop measurement: compare two GSC "Queries.csv" exports.

The nutrition-page plan (2026-07-15) is a before/after experiment. Export
Search Console -> Performance -> Queries as CSV now (baseline) and again in
4-8 weeks (after), then:

    py scripts/gsc_compare.py baseline_Queries.csv after_Queries.csv

Reports, per query and overall: change in average Position (down = better),
Clicks, CTR, Impressions. Highlights the priority nutrition queries so you can
see whether the intervention actually moved them toward page 1.

GSC CSV columns: "Top queries", Clicks, Impressions, CTR, Position.
"""
from __future__ import annotations

import csv
import io
import sys

# the plan's priority queries — flagged in the report
PRIORITY = {
    "can dogs eat quinoa", "can dogs have quinoa",
    "can dogs eat sunflower seeds", "can dogs have sunflower seeds",
    "are sunflower seeds bad for dogs",
    "can dogs eat eggplant", "can dogs eat butternut squash",
    "can dogs have almond butter", "modern dog house",
}


def load(path: str) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            q = (r.get("Top queries") or r.get("Query") or "").strip()
            if not q:
                continue
            try:
                out[q.lower()] = {
                    "clk": int(r["Clicks"]),
                    "imp": int(r["Impressions"]),
                    "ctr": float(str(r["CTR"]).rstrip("%")),
                    "pos": float(r["Position"]),
                }
            except (KeyError, ValueError):
                continue
    return out


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if len(sys.argv) != 3:
        sys.exit("usage: py scripts/gsc_compare.py <baseline_Queries.csv> <after_Queries.csv>")
    a, b = load(sys.argv[1]), load(sys.argv[2])

    def totals(d):
        clk = sum(x["clk"] for x in d.values())
        imp = sum(x["imp"] for x in d.values())
        return clk, imp, (100 * clk / imp if imp else 0)

    a_clk, a_imp, a_ctr = totals(a)
    b_clk, b_imp, b_ctr = totals(b)
    print("=== OVERALL ===")
    print(f"  clicks     {a_clk:>7} -> {b_clk:>7}  ({b_clk - a_clk:+d})")
    print(f"  impressions{a_imp:>7} -> {b_imp:>7}  ({b_imp - a_imp:+d})")
    print(f"  CTR        {a_ctr:>6.2f}% -> {b_ctr:>6.2f}%  ({b_ctr - a_ctr:+.2f} pts)")

    common = set(a) & set(b)
    moved = []
    for q in common:
        dpos = b[q]["pos"] - a[q]["pos"]  # negative = improved
        moved.append((q, a[q]["pos"], b[q]["pos"], dpos, b[q]["clk"] - a[q]["clk"]))

    print("\n=== PRIORITY QUERIES (plan targets) ===")
    print(f"  {'pos before':>10} {'pos after':>9} {'dPos':>6} {'dClk':>5}  query")
    for q in sorted(PRIORITY):
        if q in common:
            row = next(m for m in moved if m[0] == q)
            arrow = "UP" if row[3] < -0.3 else ("down" if row[3] > 0.3 else "flat")
            print(f"  {row[1]:>10.1f} {row[2]:>9.1f} {row[3]:>+6.1f} {row[4]:>+5d}  {q}  [{arrow}]")
        elif q in b and q not in a:
            print(f"  {'-':>10} {b[q]['pos']:>9.1f} {'NEW':>6} {b[q]['clk']:>+5d}  {q}  [new]")

    print("\n=== BIGGEST POSITION GAINS (improved >=1.0, impr>=100) ===")
    for q, pa, pb, dp, dc in sorted(moved, key=lambda x: x[3])[:12]:
        if dp <= -1.0 and b[q]["imp"] >= 100:
            print(f"  {pa:>5.1f} -> {pb:>5.1f}  ({dp:+.1f})  clk {dc:+d}  {q}")

    print("\n=== BIGGEST DROPS (worse >=1.0, impr>=100) ===")
    for q, pa, pb, dp, dc in sorted(moved, key=lambda x: -x[3])[:8]:
        if dp >= 1.0 and b[q]["imp"] >= 100:
            print(f"  {pa:>5.1f} -> {pb:>5.1f}  ({dp:+.1f})  {q}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
