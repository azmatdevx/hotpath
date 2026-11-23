#!/usr/bin/env python3
"""Analyze a stepped k6 run from raw CSV output plus server-side samples (standard library only).

usage: analyze.py steps-raw.csv server-metrics.csv
Windows are relative to the first request and match the 'steps' scenario in checkout.k6.js:
the first 5 s of each 50 s hold is skipped as settling time.
"""
import csv, sys, collections

raw, srv = sys.argv[1], sys.argv[2]
WINDOWS = {20: (15, 60), 40: (70, 115), 60: (125, 170), 80: (180, 225)}
TX = ["01a_login_page", "01b_login", "02_search", "03_cart", "04_checkout"]

def pct(v, p):
    v = sorted(v); k = (len(v) - 1) * p / 100; f = int(k); c = min(f + 1, len(v) - 1)
    return v[f] + (v[c] - v[f]) * (k - f)

dur = collections.defaultdict(list)       # (step, name) -> [ms]
http_err = collections.Counter()          # (step, name) -> count of status>=400
checks = collections.defaultdict(lambda: [0, 0])   # (step, check) -> [pass, fail]
dropped = collections.Counter()
starts = collections.Counter()            # (step) -> iteration starts
fail_series = collections.defaultdict(lambda: [0, 0])  # 5 s bucket -> [pass, fail] for 'search has items'
t0 = None
rows = []
with open(raw) as f:
    for r in csv.DictReader(f):
        t = int(r["timestamp"]); t0 = t if t0 is None else min(t0, t)
        rows.append((t, r["metric_name"], r["metric_value"], r["name"], r["status"], r["check"]))
step_of = lambda t: next((s for s, (a, b) in WINDOWS.items() if a <= t - t0 < b), None)
for t, m, val, name, status, chk in rows:
    s = step_of(t)
    if m == "http_req_duration" and s and name in TX:
        dur[(s, name)].append(float(val))
        if status and int(status) >= 400: http_err[(s, name)] += 1
    elif m == "http_reqs" and s and name == "01a_login_page":
        starts[s] += 1
    elif m == "checks" and chk:
        ok = float(val) == 1.0
        if s: checks[(s, chk)][0 if ok else 1] += 1
        if chk == "search has items": fail_series[(t - t0) // 5 * 5][0 if ok else 1] += 1
    elif m == "dropped_iterations" and s:
        dropped[s] += int(float(val))

print("== Per step, per transaction (steady-state window, successful and failed requests together) ==")
print(f"{'step':>5} {'transaction':<15}{'n':>6}{'req/s':>7}{'p50':>8}{'p90':>8}{'p95':>8}{'p99':>8}{'max':>8}  http>=400")
for s, (a, b) in WINDOWS.items():
    for n in TX:
        v = dur[(s, n)]
        if v:
            print(f"{s:>5} {n:<15}{len(v):>6}{len(v)/(b-a):>7.1f}{pct(v,50):>8.0f}{pct(v,90):>8.0f}{pct(v,95):>8.0f}{pct(v,99):>8.0f}{max(v):>8.0f}  {http_err[(s,n)]}")
    print()

print("== Achieved iteration start rate, dropped iterations, check failures ==")
for s, (a, b) in WINDOWS.items():
    cf = {c: v for (st, c), v in checks.items() if st == s}
    bad = {c: f"{v[1]}/{v[0]+v[1]}" for c, v in cf.items() if v[1]}
    print(f"target {s:>2}/s  achieved {starts[s]/(b-a):5.1f}/s  dropped {dropped[s]:>4}  failed checks: {bad or 'none'}")

print("\n== 'search has items' failure rate by 5 s bucket (seconds from start) ==")
first = None
for k in sorted(fail_series):
    p, f = fail_series[k]
    if f and first is None: first = k
print("first failing bucket:", first, "s" if first is not None else "(none)")

print("\n== Server-side (sampled each second) ==")
S = [(float(r["ts"]), int(r["dbInUse"]), int(r["dbQueue"]), int(r["orders"])) for r in csv.DictReader(open(srv))]
ts0 = S[0][0]
print(f"{'step':>5}{'dbInUse avg':>13}{'dbQueue avg':>13}{'dbQueue max':>13}{'orders/s':>10}")
for s, (a, b) in WINDOWS.items():
    w = [x for x in S if a <= x[0] - t0 < b]
    if w:
        print(f"{s:>5}{sum(x[1] for x in w)/len(w):>13.1f}{sum(x[2] for x in w)/len(w):>13.1f}{max(x[2] for x in w):>13}{(w[-1][3]-w[0][3])/max(1, w[-1][0]-w[0][0]):>10.1f}")
print("\nfirst second with queue > 200 (degraded search trigger):",
      next((f"{x[0]-t0:.0f}s" for x in S if x[2] > 200), "never"))
