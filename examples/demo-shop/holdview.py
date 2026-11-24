#!/usr/bin/env python3
"""Per-minute view of a 'hold' run (ramp 30 s, then a constant rate): does the queue settle or keep climbing?

usage: holdview.py raw.csv server.csv [procs.csv] [bucket_seconds]
The first 30 s (the ramp) is excluded; buckets start at t=30 s.
"""
import collections
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import avg, pct  # noqa: E402

raw, srv = sys.argv[1], sys.argv[2]
rest = sys.argv[3:]
procs = rest[0] if rest and not rest[0].isdigit() else None
B = int(rest[-1]) if rest and rest[-1].isdigit() else 60
RAMP = 30

search, checkout, starts, empty, dropped = (collections.defaultdict(list) for _ in range(5))
t0 = None
rows = []
with open(raw) as f:
    for r in csv.DictReader(f):
        t = int(r["timestamp"]); t0 = t if t0 is None else min(t0, t)
        rows.append((t, r["metric_name"], r["metric_value"], r["name"], r["check"]))
for t, m, v, name, chk in rows:
    rel = t - t0
    if m == "http_req_duration" and name == "02_search": search[rel].append(float(v))
    elif m == "http_req_duration" and name == "04_checkout": checkout[rel].append(float(v))
    elif m == "http_reqs" and name == "01a_login_page": starts[rel].append(1)
    elif m == "checks" and chk == "search has items": empty[rel].append(0 if float(v) == 1.0 else 1)
    elif m == "dropped_iterations": dropped[rel].append(float(v))
S = [(float(r["ts"]) - t0, int(r["dbQueue"])) for r in csv.DictReader(open(srv))]
P = []
if procs:
    P = [(float(r["ts"]) - t0, float(r["k6_cpu_pct"])) for r in csv.DictReader(open(procs)) if r["k6_cpu_pct"]]

def gather(d, a, b):
    return [x for k in range(a, b) for x in d.get(k, [])]

end = max(max(search, default=0), max(checkout, default=0))
print(f"{'t (s)':>9}{'starts/s':>9}{'search p95':>11}{'chk p95':>9}{'empty %':>9}{'queue avg':>10}{'queue max':>10}" + (f"{'k6 cpu':>8}" if procs else ""))
a = RAMP
while a + B <= end + 1:
    b = a + B
    sv, ck, em = gather(search, a, b), gather(checkout, a, b), gather(empty, a, b)
    q = [x[1] for x in S if a <= x[0] < b]
    line = (f"{a:>4}-{b:<4}{len(gather(starts, a, b)) / B:>9.1f}"
            f"{(pct(sv, 95) if sv else float('nan')):>11.0f}{(pct(ck, 95) if ck else float('nan')):>9.0f}"
            f"{(100 * sum(em) / len(em) if em else float('nan')):>9.0f}{(avg(q) if q else float('nan')):>10.0f}{(max(q) if q else 0):>10}")
    if procs:
        c = [x[1] for x in P if a <= x[0] < b]
        line += f"{(avg(c) if c else float('nan')):>8.0f}"
    print(line)
    a = b
print(f"dropped iterations: {int(sum(sum(v) for v in dropped.values()))}")
