#!/usr/bin/env python3
"""Compare repeated stepped runs: median [min-max] across runs (standard library only).

usage: compare-runs.py DIR PREFIX N
Reads DIR/PREFIX{1..N}-raw.csv, -server.csv, and -procs.csv (as written by the run script).
"""
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import WINDOWS, analyze  # noqa: E402

d, prefix, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
runs = []
for i in range(1, n + 1):
    base = os.path.join(d, f"{prefix}{i}")
    runs.append(analyze(base + "-raw.csv", base + "-server.csv", base + "-procs.csv")[0])


def fmt(vals, digits=0):
    vals = [v for v in vals if v is not None]
    if not vals:
        return "n/a"
    f = f"{{:.{digits}f}}"
    return f"{f.format(statistics.median(vals))} [{f.format(min(vals))}-{f.format(max(vals))}]"


def fail_pct(m):
    p, f = m["checks"].get("search has items", (0, 0))
    return 100 * f / (p + f) if p + f else None


rows = [
    ("achieved iterations/s", lambda m: m["achieved"], 1),
    ("dropped iterations", lambda m: m["dropped"], 0),
    ("search p95 ms (all)", lambda m: m["tx"]["02_search"]["p95"], 0),
    ("search p95 ms (real only)", lambda m: m["search_slow_p95"], 0),
    ("checkout p95 ms", lambda m: m["tx"]["04_checkout"]["p95"], 0),
    ("'search has items' failed %", fail_pct, 1),
    ("db slots in use (avg of 8)", lambda m: m["srv"]["inuse_avg"], 1),
    ("db queue avg", lambda m: m["srv"]["queue_avg"], 0),
    ("orders/s completed", lambda m: m["srv"]["orders_per_s"], 1),
    ("k6 CPU avg % of a core", lambda m: m["cpu"]["k6_avg"], 0),
    ("k6 CPU max % of a core", lambda m: m["cpu"]["k6_max"], 0),
    ("node CPU avg % of a core", lambda m: m["cpu"]["node_avg"], 0),
    ("machine busy avg %", lambda m: m["cpu"]["machine_avg"], 0),
    ("machine busy max %", lambda m: m["cpu"]["machine_max"], 0),
]
print(f"{n} runs; each cell is median [min-max]\n")
print(f"{'metric':<30}" + "".join(f"{'step ' + str(s) + '/s':>24}" for s in WINDOWS))
for label, get, digits in rows:
    cells = []
    for s in WINDOWS:
        try:
            cells.append(fmt([get(r[s]) for r in runs], digits))
        except (KeyError, TypeError):
            cells.append("n/a")
    print(f"{label:<30}" + "".join(f"{c:>24}" for c in cells))
