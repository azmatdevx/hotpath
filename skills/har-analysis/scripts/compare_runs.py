#!/usr/bin/env python3
"""Analyse several HARs of the same journey and report which findings repeat across runs. Standard library only.

usage: compare_runs.py --journey tc-01 [--json out.json] [--slow-ms N --big-kb N --static-kb N] run1.har run2.har ...
A finding present in every run is 'consistent' (a candidate bug); one present in some runs is 'intermittent'.
If a record file named like the HAR but ending .json exists and says the run was not verified, the run is refused.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_har import analyze  # noqa: E402

METRICS = ("time_ms", "wait_ms", "transfer", "decoded", "count", "total_ms", "hops", "repeated_bytes")

ap = argparse.ArgumentParser()
ap.add_argument("hars", nargs="+")
ap.add_argument("--journey", required=True)
ap.add_argument("--json")
ap.add_argument("--slow-ms", type=float, default=1000)
ap.add_argument("--big-kb", type=float, default=500)
ap.add_argument("--static-kb", type=float, default=300)
a = ap.parse_args()

seen = {}
for path in a.hars:
    rec = os.path.splitext(path)[0] + ".json"
    if os.path.exists(rec) and not json.load(open(rec, encoding="utf-8")).get("verified", False):
        sys.exit(f"{path}: the run did not reach its end state; do not analyse it")
    _, findings = analyze(json.load(open(path, encoding="utf-8")), a.slow_ms, a.big_kb, a.static_kb)
    for f in findings:
        seen.setdefault((f["type"], f["method"], f["url"]), []).append(f)

n = len(a.hars)
rows = []
for (t, m, url), fs in seen.items():
    ranges = {k: [min(f[k] for f in fs if k in f), max(f[k] for f in fs if k in f)] for k in METRICS
              if any(f.get(k) for f in fs)}
    rows.append({"journey": a.journey, "type": t, "method": m, "url": url, "runs_seen": len(fs), "runs": n,
                 "consistent": len(fs) == n, "ranges": ranges, "detail": fs[0]["detail"]})
rows.sort(key=lambda r: (not r["consistent"], r["type"], r["url"]))

print(f"# {a.journey}: {n} runs\n")
for label, flag in (("Consistent (in every run)", True), ("Intermittent", False)):
    sel = [r for r in rows if r["consistent"] is flag]
    print(f"## {label} ({len(sel)})\n")
    for r in sel:
        rng = ", ".join(f"{k} {v[0]}" if v[0] == v[1] else f"{k} {v[0]}-{v[1]}" for k, v in r["ranges"].items())
        print(f"- `{r['type']}` `{r['method']} {r['url']}` ({r['runs_seen']}/{n} runs" + (f"; {rng})" if rng else ")"))
    print()
if a.json:
    json.dump(rows, open(a.json, "w", encoding="utf-8"), indent=2)
