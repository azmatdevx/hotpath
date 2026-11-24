#!/usr/bin/env python3
"""Time-bucketed view of a stepped k6 run, and a first-half versus second-half drift check per step.

usage: timeseries.py raw.csv server.csv [procs.csv] [bucket_seconds]
Set STEPS (for example STEPS=60,65,70,75) to match the scenario, as for analyze.py.
"""
import collections
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import WINDOWS, avg, pct  # noqa: E402

raw, srv = sys.argv[1], sys.argv[2]
rest = sys.argv[3:]
procs = rest[0] if rest and not rest[0].isdigit() else None
B = int(rest[-1]) if rest and rest[-1].isdigit() else 10

rows, t0 = [], None
with open(raw) as f:
    for r in csv.DictReader(f):
        t = int(r["timestamp"]); t0 = t if t0 is None else min(t0, t)
        rows.append((t, r["metric_name"], r["metric_value"], r["name"], r["check"]))
S = [(float(r["ts"]) - t0, int(r["dbQueue"])) for r in csv.DictReader(open(srv))]
P = []
if procs:
    P = [(float(r["ts"]) - t0, float(r["k6_cpu_pct"])) for r in csv.DictReader(open(procs)) if r["k6_cpu_pct"]]

search, checkout, starts, empty = (collections.defaultdict(list) for _ in range(4))
for t, m, v, name, chk in rows:
    rel = t - t0
    if m == "http_req_duration" and name == "02_search": search[rel].append(float(v))
    elif m == "http_req_duration" and name == "04_checkout": checkout[rel].append(float(v))
    elif m == "http_reqs" and name == "01a_login_page": starts[rel].append(1)
    elif m == "checks" and chk == "search has items": empty[rel].append(0 if float(v) == 1.0 else 1)

def gather(d, a, b):
    return [x for k in range(a, b) for x in d.get(k, [])]

def label(a):
    for s, (wa, wb) in WINDOWS.items():
        if wa <= a < wb: return f"{s}/s"
    return "ramp"

print(f"{'t (s)':>9}{'phase':>7}{'starts/s':>9}{'search p95':>11}{'chk p95':>9}{'empty %':>9}{'queue avg':>10}{'queue max':>10}" + (f"{'k6 cpu':>8}" if procs else ""))
end = max(max(search, default=0), max(checkout, default=0)) + 1
for a in range(0, end, B):
    b = a + B
    sv, ck = gather(search, a, b), gather(checkout, a, b)
    em = gather(empty, a, b)
    q = [x[1] for x in S if a <= x[0] < b]
    line = (f"{a:>4}-{b:<4}{label(a):>7}{len(gather(starts, a, b)) / B:>9.1f}"
            f"{(pct(sv, 95) if sv else float('nan')):>11.0f}{(pct(ck, 95) if ck else float('nan')):>9.0f}"
            f"{(100 * sum(em) / len(em) if em else float('nan')):>9.0f}{(avg(q) if q else float('nan')):>10.0f}{(max(q) if q else 0):>10}")
    if procs:
        c = [x[1] for x in P if a <= x[0] < b]
        line += f"{(avg(c) if c else float('nan')):>8.0f}"
    print(line)

print("\nDrift check: first half -> second half of each 45 s window (checkout p95 ms | search p95 ms | queue avg)")
for s, (wa, wb) in WINDOWS.items():
    mid = (wa + wb) // 2
    def stats(a, b):
        ck, sv = gather(checkout, a, b), gather(search, a, b)
        q = [x[1] for x in S if a <= x[0] < b]
        return pct(ck, 95), pct(sv, 95), avg(q)
    c1, s1, q1 = stats(wa, mid); c2, s2, q2 = stats(mid, wb)
    flag = "  <- drifting" if (c2 > 1.15 * c1 + 20 or q2 > 1.5 * q1 + 20) else ""
    print(f"{s:>4}/s: {c1:>5.0f} -> {c2:>5.0f} | {s1:>4.0f} -> {s2:>4.0f} | {q1:>5.0f} -> {q2:>5.0f}{flag}")
