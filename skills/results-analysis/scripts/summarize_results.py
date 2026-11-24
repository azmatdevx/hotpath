#!/usr/bin/env python3
"""Summarise raw load test results into a few dozen lines: percentiles per transaction over the steady-state window,
error rates, drift between the window's halves, and a coarse time series. Standard library only.

usage: summarize_results.py RESULTS [--format auto|k6-csv|jtl|csv] [--trim-start 60] [--trim-end 15]
                            [--window START,END] [--exclude REGEX] [--sla LABEL=MS ...] [--sla-p95 MS]
                            [--json out.json] [--series-csv out.csv [--series-bucket 10]]
  Formats:  k6-csv   k6 --out csv=...   (http_req_duration per request name; checks and dropped_iterations too)
            jtl      JMeter CSV results file (header with timeStamp, elapsed, label, success, responseCode)
            csv      any CSV; name the columns with --col-time --col-label --col-elapsed --col-ok
                     [--time-unit ms|s] [--ok-values true,1,200]
  The window is relative to the first sample. By default it drops the first --trim-start seconds (ramp-up) and the
  last --trim-end seconds (ramp-down); --window START,END sets it explicitly (seconds after the first sample).
Read this with the run's own conditions in mind: this script cannot tell whether the generator was saturated or
whether the load matched the plan. Use results-sanity-check for that.
"""
import argparse
import array
import csv
import json
import math
import re
import sys

ap = argparse.ArgumentParser()
ap.add_argument("results")
ap.add_argument("--format", default="auto", choices=["auto", "k6-csv", "jtl", "csv"])
ap.add_argument("--trim-start", type=float, default=60)
ap.add_argument("--trim-end", type=float, default=15)
ap.add_argument("--window")
ap.add_argument("--exclude")
ap.add_argument("--sla", action="append", default=[], help="LABEL=MS: p95 limit for one transaction")
ap.add_argument("--sla-p95", type=float, help="p95 limit in ms for every transaction without its own")
ap.add_argument("--json")
ap.add_argument("--series-csv", help="write a time series (epoch seconds, request rate, pooled p95, error %%) for rank_limiters.py")
ap.add_argument("--series-bucket", type=int, default=10, help="bucket seconds for --series-csv")
ap.add_argument("--series-label", help="regex: only these transactions go into --series-csv (default all, pooled)")
ap.add_argument("--col-time")
ap.add_argument("--col-label")
ap.add_argument("--col-elapsed")
ap.add_argument("--col-ok")
ap.add_argument("--time-unit", default="ms", choices=["ms", "s"])
ap.add_argument("--ok-values", default="true,1,200")
a = ap.parse_args()


def pct(sorted_vals, p):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def sniff(header):
    h = set(header)
    if {"metric_name", "metric_value", "timestamp"} <= h:
        return "k6-csv"
    if {"timeStamp", "elapsed", "label"} <= h:
        return "jtl"
    return None


def rows(path, fmt):
    """Yield (time_s, label, elapsed_ms, ok) for requests; side channels go into the dicts below."""
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        rd = csv.DictReader(f)
        fmt = sniff(rd.fieldnames or []) if fmt == "auto" else fmt
        if fmt is None:
            sys.exit("could not recognise the file; use --format csv with --col-time, --col-label, --col-elapsed and --col-ok")
        if fmt == "csv" and not (a.col_time and a.col_label and a.col_elapsed and a.col_ok):
            sys.exit("--format csv needs --col-time, --col-label, --col-elapsed and --col-ok")
        okvals = {v.strip().lower() for v in a.ok_values.split(",")}
        for r in rd:
            try:
                if fmt == "k6-csv":
                    m = r["metric_name"]
                    if m == "http_req_duration":
                        ok = r.get("expected_response", "true").lower() != "false" and not (r.get("status", "") or "0").startswith(("4", "5"))
                        yield float(r["timestamp"]), r.get("name") or r.get("group") or r.get("url", "?"), float(r["metric_value"]), ok
                    elif m == "checks":
                        CHECKS[r.get("check") or "?"][0] += 1
                        CHECKS[r.get("check") or "?"][1] += 1 if float(r["metric_value"]) == 0 else 0
                    elif m == "dropped_iterations":
                        DROPPED[0] += float(r["metric_value"])
                elif fmt == "jtl":
                    yield float(r["timeStamp"]) / 1000, r["label"], float(r["elapsed"]), r.get("success", "true").lower() == "true"
                else:
                    t = float(r[a.col_time]) / (1000 if a.time_unit == "ms" else 1)
                    yield t, r[a.col_label], float(r[a.col_elapsed]), r[a.col_ok].strip().lower() in okvals
            except (ValueError, KeyError):
                BAD[0] += 1


CHECKS = {}
DROPPED = [0.0]
BAD = [0]
import collections  # noqa: E402
CHECKS = collections.defaultdict(lambda: [0, 0])

data = collections.defaultdict(lambda: (array.array("d"), array.array("f"), array.array("b")))   # label -> t, ms, ok
excl = re.compile(a.exclude) if a.exclude else None
t_min, t_max, total = math.inf, -math.inf, 0
for t, label, ms, ok in rows(a.results, a.format):
    if excl and excl.search(label):
        continue
    ts, ds, oks = data[label]
    ts.append(t); ds.append(ms); oks.append(1 if ok else 0)
    t_min, t_max, total = min(t_min, t), max(t_max, t), total + 1
if not total:
    sys.exit("no request samples found in the file")

if a.window:
    w0, w1 = (float(x) for x in a.window.split(","))
else:
    w0, w1 = a.trim_start, (t_max - t_min) - a.trim_end
w0, w1 = t_min + w0, t_min + w1
dur = t_max - t_min
notes = []
if w1 <= w0:
    sys.exit(f"the window is empty (the run lasted {dur:.0f} s); lower --trim-start and --trim-end or set --window")
if w1 - w0 < 120:
    notes.append(f"the window is only {w1 - w0:.0f} s long, which is short for percentiles and drift")
mid = (w0 + w1) / 2

slas = {}
for s in a.sla:
    k, _, v = s.rpartition("=")
    slas[k] = float(v)

report = {"samples": total, "run_seconds": round(dur), "window": [round(w0 - t_min), round(w1 - t_min)], "labels": {}}
for label, (ts, ds, oks) in sorted(data.items()):
    inw = [(d, o, t) for t, d, o in zip(ts, ds, oks) if w0 <= t < w1]
    if not inw:
        continue
    v = sorted(d for d, _, _ in inw)
    h1 = sorted(d for d, _, t in inw if t < mid)
    h2 = sorted(d for d, _, t in inw if t >= mid)
    errs = sum(1 for _, o, _ in inw if not o)
    e1 = sum(1 for _, o, t in inw if not o and t < mid) / max(len(h1), 1)
    e2 = sum(1 for _, o, t in inw if not o and t >= mid) / max(len(h2), 1)
    p95 = pct(v, 95)
    limit = slas.get(label, a.sla_p95)
    row = {"n": len(v), "rate_per_s": round(len(v) / (w1 - w0), 2), "error_pct": round(100 * errs / len(v), 2),
           "p50": round(pct(v, 50)), "p90": round(pct(v, 90)), "p95": round(p95), "p99": round(pct(v, 99)), "max": round(v[-1]),
           "p95_first_half": round(pct(h1, 95)) if h1 else None, "p95_second_half": round(pct(h2, 95)) if h2 else None,
           "error_pct_first_half": round(100 * e1, 2), "error_pct_second_half": round(100 * e2, 2)}
    row["drifting"] = bool(h1 and h2 and (row["p95_second_half"] > 1.15 * row["p95_first_half"] + 20 or e2 > e1 + 0.01))
    if limit is not None:
        row["p95_limit"] = limit
        row["over_limit"] = p95 > limit
    report["labels"][label] = row

# coarse time series over the whole run, about 20 buckets
step = max(10, math.ceil(dur / 20 / 10) * 10)
buckets = collections.defaultdict(lambda: [array.array("f"), 0, 0])
for label, (ts, ds, oks) in data.items():
    for t, d, o in zip(ts, ds, oks):
        b = buckets[int((t - t_min) // step)]
        b[0].append(d); b[1] += 1; b[2] += 0 if o else 1
series = [{"from_s": k * step, "rate_per_s": round(b[1] / step, 1), "p95_all": round(pct(sorted(b[0]), 95)),
           "error_pct": round(100 * b[2] / b[1], 1)} for k, b in sorted(buckets.items())]
report["series"] = series
report["checks"] = {k: {"evaluated": v[0], "failed": v[1]} for k, v in CHECKS.items() if v[1]}
report["dropped_iterations"] = int(DROPPED[0])

print(f"# {a.results.split('/')[-1]}: {total} samples over {dur:.0f} s; window {report['window'][0]}-{report['window'][1]} s\n")
for n in notes:
    print(f"Note: {n}.")
print(f"| Transaction | n | rate/s | err % | p50 | p90 | p95 | p99 | max | p95 first -> second half |")
print("|---|---|---|---|---|---|---|---|---|---|")
for label, r in report["labels"].items():
    flags = (" DRIFTING" if r["drifting"] else "") + (f" OVER {r['p95_limit']:.0f}" if r.get("over_limit") else "")
    print(f"| {label} | {r['n']} | {r['rate_per_s']} | {r['error_pct']} | {r['p50']} | {r['p90']} | {r['p95']} | {r['p99']} | {r['max']} | {r['p95_first_half']} -> {r['p95_second_half']}{flags} |")
print(f"\nTime series ({step} s buckets, pooled over all transactions, requests per second): " + "; ".join(f"{s['from_s']}s {s['rate_per_s']}/s p95 {s['p95_all']} err {s['error_pct']}%" for s in series))
if report["checks"]:
    print("\nFailing checks: " + "; ".join(f"{k}: {v['failed']} of {v['evaluated']}" for k, v in report["checks"].items()))
if report["dropped_iterations"]:
    print(f"\nDropped iterations: {report['dropped_iterations']} (the offered load was lower than planned; results are not what the plan describes)")
if BAD[0]:
    print(f"\n{BAD[0]} unreadable rows were skipped.")
if a.json:
    json.dump(report, open(a.json, "w"), indent=2)
if a.series_csv:
    sb = a.series_bucket
    fine = collections.defaultdict(lambda: [array.array("f"), 0, 0])
    for label, (ts, ds, oks) in data.items():
        if a.series_label and not re.search(a.series_label, label):
            continue
        for t, d, o in zip(ts, ds, oks):
            b = fine[int((t - t_min) // sb)]
            b[0].append(d); b[1] += 1; b[2] += 0 if o else 1
    with open(a.series_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time", "rate_per_s", "p95_ms", "error_pct"])
        for k, b in sorted(fine.items()):
            w.writerow([int(t_min + k * sb), round(b[1] / sb, 2), round(pct(sorted(b[0]), 95), 1), round(100 * b[2] / b[1], 2)])
