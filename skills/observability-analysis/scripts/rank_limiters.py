#!/usr/bin/env python3
"""Rank monitoring series by how well they explain a latency rise in a load test run. Standard library only.

usage: rank_limiters.py REFERENCE.csv METRIC.csv[:COLUMN] [METRIC.csv[:COLUMN] ...] [--window START,END] [--max-lag 120]
                        [--ceiling NAME=VALUE ...] [--json out.json]
REFERENCE.csv comes from summarize_results.py --series-csv: time (epoch seconds), rate_per_s, p95_ms, error_pct.
Each METRIC.csv is a platform export with the time in the first column (epoch seconds or milliseconds, or ISO 8601)
and the value in the last column. The file name is the metric name. For a file with several value columns, name the
one to use: FILE.csv:COLUMN (the metric is then called COLUMN).

For each metric it reports the correlation with p95 latency (best of several lags, so a metric that moves before
latency does is found), the correlation with the request rate, the mean in the first and second half of the window,
the peak, and, for a metric whose capacity you declare with --ceiling NAME=VALUE (for example cpu_percent=100 or
pool_in_use=50), the share of the window it spent at 90% or more of that ceiling, which is what saturation looks like.
A metric that follows latency but not the rate is a candidate limiter. One that follows both only grows with load.
A metric at its declared ceiling for half the window or more is reported as saturated, even though a flat series has
no correlation with anything: check it first, together with whatever queues behind it.
This ranks candidates; correlation is not cause. Name the mechanism, and check it, before you report it.
"""
import argparse
import csv
import datetime
import json
import math
import os
import statistics
import sys

ap = argparse.ArgumentParser()
ap.add_argument("reference")
ap.add_argument("metrics", nargs="+")
ap.add_argument("--window", help="START,END in epoch seconds; default is the middle of the reference series")
ap.add_argument("--max-lag", type=int, default=120)
ap.add_argument("--ceiling", action="append", default=[], help="NAME=VALUE: the metric's capacity")
ap.add_argument("--json")
a = ap.parse_args()


def parse_time(v):
    v = v.strip()
    try:
        x = float(v)
        return x / 1000 if x > 1e11 else x
    except ValueError:
        return datetime.datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp()


def read(path, col=None):
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        rd = csv.reader(f)
        header = next(rd)
        for r in rd:
            try:
                out.append((parse_time(r[0]), {h: float(x) for h, x in zip(header[1:], r[1:]) if x.strip() != ""}))
            except (ValueError, IndexError):
                continue
    return header, out


def resample(points, grid, step):
    buckets = {}
    for t, v in points:
        buckets.setdefault(int((t - grid[0]) // step), []).append(v)
    return [statistics.fmean(buckets[i]) if i in buckets else None for i in range(len(grid))]


def pearson(x, y):
    pairs = [(p, q) for p, q in zip(x, y) if p is not None and q is not None]
    if len(pairs) < 8:
        return None
    mx, my = statistics.fmean(p for p, _ in pairs), statistics.fmean(q for _, q in pairs)
    sx = math.sqrt(sum((p - mx) ** 2 for p, _ in pairs))
    sy = math.sqrt(sum((q - my) ** 2 for _, q in pairs))
    return None if sx == 0 or sy == 0 else sum((p - mx) * (q - my) for p, q in pairs) / (sx * sy)


ceilings = {k: float(v) for k, _, v in (c.partition('=') for c in a.ceiling)}
hdr, ref = read(a.reference)
need = {"rate_per_s", "p95_ms"}
if not need <= set(hdr):
    sys.exit("the reference file needs the columns time, rate_per_s and p95_ms (use summarize_results.py --series-csv)")
t_all = [t for t, _ in ref]
step = int(statistics.median(b - c for b, c in zip(t_all[1:], t_all)))
if a.window:
    w0, w1 = (float(x) for x in a.window.split(","))
else:
    span = t_all[-1] - t_all[0]
    w0, w1 = t_all[0] + 0.1 * span, t_all[-1] - 0.05 * span
grid = [t for t in t_all if w0 <= t < w1]
if len(grid) < 12:
    sys.exit("the window holds fewer than 12 reference points; use a longer run or a smaller --series-bucket")
lat = resample([(t, v["p95_ms"]) for t, v in ref], grid, step)
rate = resample([(t, v["rate_per_s"]) for t, v in ref], grid, step)
half = len(grid) // 2

rows = []
for spec in a.metrics:
    path, want = (spec, None)
    if not os.path.exists(spec) and ":" in spec:
        path, want = spec.rsplit(":", 1)
    name = want or os.path.splitext(os.path.basename(path))[0]
    h, pts = read(path)
    if not pts:
        print(f"skipped {name}: no readable rows", file=sys.stderr)
        continue
    col = want or (h[-1] if h[-1] in pts[0][1] else next(iter(pts[0][1])))
    if want and want not in h:
        print(f"skipped {name}: no column named {want} in {path}", file=sys.stderr)
        continue
    series = resample([(t, v[col]) for t, v in pts if col in v], grid, step)
    if sum(v is not None for v in series) < 12:
        print(f"skipped {name}: it covers too little of the window", file=sys.stderr)
        continue
    best = None
    for lag in range(-a.max_lag // step, a.max_lag // step + 1):     # positive lag: the metric moves first
        shifted = series[:len(series) - lag] if lag >= 0 else series[-lag:]
        target = lat[lag:] if lag >= 0 else lat[:len(lat) + lag]
        r = pearson(shifted, target)
        if r is not None and (best is None or abs(r) > abs(best[0])):
            best = (r, lag * step)
    vals = [v for v in series if v is not None]
    top = max(vals)
    cap = ceilings.get(name)
    at_ceiling = None if cap is None else round(100 * sum(1 for v in vals if v >= 0.9 * cap) / len(vals))
    first = [v for v in series[:half] if v is not None]
    second = [v for v in series[half:] if v is not None]
    r_rate = pearson(series, rate)
    r_lat = best[0] if best else None      # None: the series is constant, so nothing correlates with it
    if r_lat is None:
        verdict = "constant (no variation to correlate)"
    elif abs(r_lat) >= 0.7 and (r_rate is None or abs(r_rate) < 0.7):
        verdict = "candidate limiter (follows latency, not load)"
    elif abs(r_lat) >= 0.7:
        verdict = "grows with load and with latency (check for saturation)"
    elif r_rate is not None and abs(r_rate) >= 0.7:
        verdict = "tracks load only"
    else:
        verdict = "no clear relationship"
    if at_ceiling is not None and at_ceiling >= 50:
        verdict = f"saturated: at its ceiling for {at_ceiling}% of the window"
    rows.append({"metric": name, "r_latency": None if r_lat is None else round(r_lat, 2), "lag_s": best[1] if best else None, "r_rate": None if r_rate is None else round(r_rate, 2),
                 "mean_first_half": round(statistics.fmean(first), 3) if first else None,
                 "mean_second_half": round(statistics.fmean(second), 3) if second else None,
                 "peak": round(top, 3), "at_ceiling_pct": at_ceiling, "verdict": verdict})
rows.sort(key=lambda r: (0 if r["verdict"].startswith("candidate") else 1 if r["verdict"].startswith("saturated") else 2, -abs(r["r_latency"] or 0)))

print(f"# Limiter candidates ({len(grid)} points of {step} s, window {int(w0)}-{int(w1)})\n")
print("| Metric | r vs p95 | lag s | r vs rate | first half -> second | peak | % of window at ceiling | Reading |")
print("|---|---|---|---|---|---|---|---|")
for r in rows:
    print(f"| {r['metric']} | {r['r_latency']} | {r['lag_s']} | {r['r_rate']} | {r['mean_first_half']} -> {r['mean_second_half']} | {r['peak']} | {'-' if r['at_ceiling_pct'] is None else r['at_ceiling_pct']} | {r['verdict']} |")
print("\nCorrelation ranks where to look; it does not show cause. A lag above zero means the metric moved first.")
if a.json:
    json.dump(rows, open(a.json, "w"), indent=2)
