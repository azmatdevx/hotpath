#!/usr/bin/env python3
"""Summarise lab web vitals from journey-capture run records, across runs. Standard library only.

usage: vitals_summary.py --journey tc-03-cold [--json out.json] [--lcp-ms 2500 --cls 0.1 --inp-ms 200
                         --tbt-ms 200 --ttfb-ms 800] run1.json run2.json ...
The inputs are the <flow>-<cache>-runN.json files that capture-playwright.js writes beside each HAR.
For each page, the latest reading in each run is used. A metric over its threshold in every run is 'consistent'
(a candidate bug); over it in some runs is 'intermittent'. A run record that did not verify is refused.
The thresholds are Google's 'good' limits and a lab approximation for TBT; change them to your team's.
The rows have the same shape as compare_runs.py --json, so sweep-rollup and draft_bugs.py read them unchanged.
"""
import argparse
import json
import os
import statistics
import sys
import urllib.parse

METRICS = [  # key in the record, finding type, label, unit, threshold flag
    ("lcp_ms", "poor-lcp", "LCP", "ms", "lcp_ms"),
    ("cls", "poor-cls", "CLS", "", "cls"),
    ("inp_ms", "poor-inp", "worst interaction", "ms", "inp_ms"),
    ("tbt_ms", "poor-tbt", "TBT", "ms", "tbt_ms"),
    ("ttfb_ms", "slow-ttfb", "TTFB", "ms", "ttfb_ms"),
]

ap = argparse.ArgumentParser()
ap.add_argument("records", nargs="+")
ap.add_argument("--journey", required=True)
ap.add_argument("--json")
ap.add_argument("--lcp-ms", type=float, default=2500)
ap.add_argument("--cls", type=float, default=0.1)
ap.add_argument("--inp-ms", type=float, default=200)
ap.add_argument("--tbt-ms", type=float, default=200)
ap.add_argument("--ttfb-ms", type=float, default=800)
a = ap.parse_args()
limits = {m[4]: getattr(a, m[4]) for m in METRICS}

runs = []   # per run: {page url: latest reading}
conditions = set()
for path in a.records:
    rec = json.load(open(path, encoding="utf-8"))
    if not rec.get("verified", False):
        sys.exit(f"{path}: the run did not reach its end state; do not use its vitals")
    latest = {}
    for v in rec.get("vitals", []):
        latest[v["url"]] = v          # later steps overwrite earlier ones for the same page
    runs.append(latest)
    c = rec.get("conditions", {})
    conditions.add(f"cpu x{c.get('cpuSlowdown', 1)}, {c.get('userAgent', 'user agent not recorded')}")

n = len(runs)
rows = []
print(f"# {a.journey}: lab vitals over {n} runs\n")
print("Conditions: " + "; ".join(sorted(conditions)) + ". Lab numbers, one user, no network throttling.\n")
pages = sorted({u for r in runs for u in r})
for url in pages:
    print(f"## {url}\n")
    print("| Metric | Median | Range | Limit | Runs over |")
    print("|---|---|---|---|---|")
    for key, ftype, label, unit, flag in METRICS:
        vals = [r[url][key] for r in runs if url in r and r[url].get(key) is not None]
        if not vals:
            print(f"| {label} | not recorded | | {limits[flag]}{unit} | |")
            continue
        over = [v for v in vals if v > limits[flag]]
        lo, hi, med = min(vals), max(vals), statistics.median(vals)
        print(f"| {label} | {med}{unit} | {lo}-{hi}{unit} | {limits[flag]}{unit} | {len(over)}/{len(vals)} |")
        if over:
            elem = next((r[url].get("lcpElement") for r in runs if url in r and r[url].get("lcpElement")), None)
            detail = f"{label} {lo if lo == hi else f'{lo}-{hi}'}{unit} against a limit of {limits[flag]}{unit}"
            if key == "lcp_ms" and elem:
                detail += f" (LCP element: {elem})"
            rows.append({"journey": a.journey, "type": ftype, "method": "PAGE", "url": url,
                         "runs_seen": len(over), "runs": n, "consistent": len(over) == n,
                         "ranges": {key: [lo, hi]}, "detail": detail,
                         "hars": [os.path.basename(p) for p in a.records]})
    print()
if a.json:
    json.dump(rows, open(a.json, "w", encoding="utf-8"), indent=2)
