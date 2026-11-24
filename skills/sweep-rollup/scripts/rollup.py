#!/usr/bin/env python3
"""Merge per-journey findings (from compare_runs.py --json) into one list of problems to log. Standard library only.

usage: rollup.py [--include-intermittent] [--json out.json] journey1.json journey2.json ...
One request with one kind of problem seen in several journeys becomes one row that lists the journeys.
By default only findings seen in every run of a journey are rolled up.
"""
import argparse
import collections
import json

ap = argparse.ArgumentParser()
ap.add_argument("files", nargs="+")
ap.add_argument("--include-intermittent", action="store_true")
ap.add_argument("--json", help="also write the merged rows here (input for perf-bug-writing/scripts/draft_bugs.py)")
a = ap.parse_args()

groups = collections.defaultdict(list)
skipped = collections.Counter()
for path in a.files:
    for r in json.load(open(path, encoding="utf-8")):
        if not r["consistent"] and not a.include_intermittent:
            skipped[r["journey"]] += 1
            continue
        groups[(r["type"], r["method"], r["url"])].append(r)

rows = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))
merged_rows = []
print(f"# Sweep rollup: {len(rows)} problem(s) from {len(a.files)} journey file(s)\n")
print("| Problem | Request | Journeys | Evidence (ranges across runs) |")
print("|---|---|---|---|")
for (t, m, url), rs in rows:
    merged = {}
    for r in rs:
        for k, (lo, hi) in r["ranges"].items():
            cur = merged.setdefault(k, [lo, hi])
            cur[0], cur[1] = min(cur[0], lo), max(cur[1], hi)
    ev = ", ".join(f"{k} {lo}" if lo == hi else f"{k} {lo}-{hi}" for k, (lo, hi) in merged.items())
    print(f"| {t} | `{m} {url}` | {', '.join(sorted({r['journey'] for r in rs}))} ({len(rs)}) | {ev} |")
    merged_rows.append({"type": t, "method": m, "url": url, "journeys": sorted({r["journey"] for r in rs}),
                        "runs": {r["journey"]: r["runs"] for r in rs}, "ranges": merged, "detail": rs[0]["detail"],
                        "hars": {r["journey"]: r.get("hars", []) for r in rs}})
if skipped:
    print("\nIntermittent findings left out: " + ", ".join(f"{j} ({n})" for j, n in sorted(skipped.items())))
if a.json:
    json.dump(merged_rows, open(a.json, "w", encoding="utf-8"), indent=2)
