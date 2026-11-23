#!/usr/bin/env python3
"""Analyze a stepped k6 run from raw CSV output plus server-side samples (standard library only).

usage: analyze.py steps-raw.csv server-metrics.csv [procs.csv]

Windows are relative to the first request and match the 'steps' scenario in checkout.k6.js:
the first 5 s of each 50 s hold is skipped as settling time.
"""
import collections
import csv
import sys

WINDOWS = {20: (15, 60), 40: (70, 115), 60: (125, 170), 80: (180, 225)}
TX = ["01a_login_page", "01b_login", "02_search", "03_cart", "04_checkout"]
FAST_MS = 100   # demo-shop: degraded search replies skip the database and return in under 10 ms


def pct(v, p):
    v = sorted(v)
    k = (len(v) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(v) - 1)
    return v[f] + (v[c] - v[f]) * (k - f)


def avg(v):
    v = [x for x in v if x is not None]
    return sum(v) / len(v) if v else None


def analyze(raw, srv, procs=None):
    """Return {step: metrics} and the second at which the database queue first exceeded 200."""
    rows, t0 = [], None
    with open(raw) as f:
        for r in csv.DictReader(f):
            t = int(r["timestamp"])
            t0 = t if t0 is None else min(t0, t)
            rows.append((t, r["metric_name"], r["metric_value"], r["name"], r["status"], r["check"]))
    step_of = lambda t: next((s for s, (a, b) in WINDOWS.items() if a <= t - t0 < b), None)

    dur = collections.defaultdict(list)
    http_err = collections.Counter()
    checks = collections.defaultdict(lambda: [0, 0])
    dropped = collections.Counter()
    starts = collections.Counter()
    for t, m, val, name, status, chk in rows:
        s = step_of(t)
        if not s:
            continue
        if m == "http_req_duration" and name in TX:
            dur[(s, name)].append(float(val))
            if status and int(status) >= 400:
                http_err[(s, name)] += 1
        elif m == "http_reqs" and name == "01a_login_page":
            starts[s] += 1
        elif m == "checks" and chk:
            checks[(s, chk)][0 if float(val) == 1.0 else 1] += 1
        elif m == "dropped_iterations":
            dropped[s] += int(float(val))

    S = [(float(r["ts"]), int(r["dbInUse"]), int(r["dbQueue"]), int(r["orders"])) for r in csv.DictReader(open(srv))]
    P = []
    if procs:
        def num(x):
            return float(x) if x not in ("", "nan") else None
        P = [(float(r["ts"]), num(r["k6_cpu_pct"]), num(r["node_cpu_pct"]), num(r["machine_busy_pct"]))
             for r in csv.DictReader(open(procs))]

    out = {}
    for s, (a, b) in WINDOWS.items():
        m = {"tx": {}, "achieved": starts[s] / (b - a), "dropped": dropped[s]}
        for n in TX:
            v = dur[(s, n)]
            if v:
                m["tx"][n] = {"n": len(v), "rps": len(v) / (b - a), "p50": pct(v, 50), "p90": pct(v, 90),
                              "p95": pct(v, 95), "p99": pct(v, 99), "max": max(v), "http_err": http_err[(s, n)]}
        m["checks"] = {c: tuple(v) for (st, c), v in checks.items() if st == s}
        sv = dur[(s, "02_search")]
        fast = [x for x in sv if x < FAST_MS]
        slow = [x for x in sv if x >= FAST_MS]
        if not m["checks"].get("search has items", (0, 0))[1]:   # no degraded replies: nothing to split out
            fast, slow = [], sv
        m["search_fast_pct"] = 100 * len(fast) / len(sv) if sv else None
        m["search_slow_p50"] = pct(slow, 50) if slow else None
        m["search_slow_p95"] = pct(slow, 95) if slow else None
        w = [x for x in S if a <= x[0] - t0 < b]
        if w:
            m["srv"] = {"inuse_avg": avg([x[1] for x in w]), "queue_avg": avg([x[2] for x in w]),
                        "queue_max": max(x[2] for x in w),
                        "orders_per_s": (w[-1][3] - w[0][3]) / max(1, w[-1][0] - w[0][0])}
        pw = [x for x in P if a <= x[0] - t0 < b]
        if pw:
            col = lambda i: [x[i] for x in pw if x[i] is not None]
            m["cpu"] = {"k6_avg": avg(col(1)), "k6_max": max(col(1), default=None),
                        "node_avg": avg(col(2)), "node_max": max(col(2), default=None),
                        "machine_avg": avg(col(3)), "machine_max": max(col(3), default=None)}
        out[s] = m
    degrade = next((x[0] - t0 for x in S if x[2] > 200), None)
    return out, degrade


def main():
    raw, srv = sys.argv[1], sys.argv[2]
    procs = sys.argv[3] if len(sys.argv) > 3 else None
    res, degrade = analyze(raw, srv, procs)
    print("== Per step, per transaction (steady-state window, all responses) ==")
    print(f"{'step':>5} {'transaction':<15}{'n':>6}{'req/s':>7}{'p50':>8}{'p90':>8}{'p95':>8}{'p99':>8}{'max':>8}  http>=400")
    for s, m in res.items():
        for n, t in m["tx"].items():
            print(f"{s:>5} {n:<15}{t['n']:>6}{t['rps']:>7.1f}{t['p50']:>8.0f}{t['p90']:>8.0f}{t['p95']:>8.0f}"
                  f"{t['p99']:>8.0f}{t['max']:>8.0f}  {t['http_err']}")
        print()
    print("== Achieved iteration start rate, dropped iterations, failed checks ==")
    for s, m in res.items():
        bad = {c: f"{f}/{p + f}" for c, (p, f) in m["checks"].items() if f}
        print(f"target {s:>2}/s  achieved {m['achieved']:5.1f}/s  dropped {m['dropped']:>4}  failed checks: {bad or 'none'}")
    print("\n== Server side (sampled about once per second) ==")
    for s, m in res.items():
        if "srv" in m:
            v = m["srv"]
            print(f"step {s:>2}: dbInUse avg {v['inuse_avg']:.1f}  dbQueue avg {v['queue_avg']:.1f} max {v['queue_max']}  orders/s {v['orders_per_s']:.1f}")
    if procs:
        print("\n== CPU (percent of one core for processes; percent of the machine for 'machine') ==")
        for s, m in res.items():
            if "cpu" in m:
                c = m["cpu"]
                print(f"step {s:>2}: k6 avg {c['k6_avg']:.0f} max {c['k6_max']:.0f} | node avg {c['node_avg']:.0f} max {c['node_max']:.0f}"
                      f" | machine avg {c['machine_avg']:.0f}% max {c['machine_max']:.0f}%")
    print("\nfirst second with queue > 200 (degraded search trigger):", f"{degrade:.0f}s" if degrade is not None else "never")


if __name__ == "__main__":
    main()
