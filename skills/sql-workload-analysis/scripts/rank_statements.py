#!/usr/bin/env python3
"""Rank the SQL statements that cost the most during a load test window. Standard library only.

usage: rank_statements.py AFTER.csv [--before BEFORE.csv] [--window-seconds N] [--requests N] [--top 15] [--json out.json]
AFTER.csv is an export of the database's statement statistics (see the engine references). The columns are found by
name: an id (queryid, sql_id, query_id, digest), the text (query, sql_text, digest_text), calls (calls, executions,
count_star, execution_count), total time in ms (total_ms, total_exec_time, elapsed_ms) and, if you have them, rows
(rows, rows_processed, rows_sent) and rows_examined.
The counters are cumulative, so give the snapshot taken before the run as --before: the script subtracts it. If you
reset the statistics before the run, leave --before out.
With --requests (how many requests the load test sent in the window) it also reports calls per request.
Literals in the text are replaced by ? in the output, so values and personal data are not copied into reports.
It ranks and flags; whether a statement is the problem, and why, needs its plan (see sql-plan-analysis).
"""
import argparse
import csv
import hashlib
import json
import re
import sys

ALIASES = {
    "id": ("queryid", "sql_id", "query_id", "digest", "id"),
    "text": ("query", "sql_text", "digest_text", "text", "statement"),
    "calls": ("calls", "executions", "count_star", "execution_count", "exec_count"),
    "total_ms": ("total_ms", "total_exec_time", "total_time", "elapsed_ms", "total_elapsed_ms"),
    "rows": ("rows", "rows_processed", "rows_sent", "sum_rows_sent"),
    "examined": ("rows_examined", "sum_rows_examined"),
}

ap = argparse.ArgumentParser()
ap.add_argument("after")
ap.add_argument("--before")
ap.add_argument("--window-seconds", type=float)
ap.add_argument("--requests", type=float)
ap.add_argument("--top", type=int, default=15)
ap.add_argument("--json")
a = ap.parse_args()


def normalise(text):
    t = re.sub(r"'(?:[^']|'')*'", "?", text)
    t = re.sub(r"\b\d+(?:\.\d+)?\b", "?", t)
    t = re.sub(r"\(\s*\?(?:\s*,\s*\?)+\s*\)", "(?)", t)          # IN lists
    return re.sub(r"\s+", " ", t).strip()


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        low = {h.lower(): h for h in rd.fieldnames or []}
        col = {k: next((low[n] for n in names if n in low), None) for k, names in ALIASES.items()}
        missing = [k for k in ("text", "calls", "total_ms") if col[k] is None]
        if missing:
            sys.exit(f"{path}: no column found for {', '.join(missing)}; rename the export's columns (see the engine references)")
        out = {}
        for i, r in enumerate(rd):
            try:
                text = r[col["text"]]
                key = r[col["id"]] if col["id"] else hashlib.md5(text.encode()).hexdigest()[:12]
                out[key] = {"text": text, "calls": float(r[col["calls"]]), "total_ms": float(r[col["total_ms"]]),
                            "rows": float(r[col["rows"]]) if col["rows"] and r[col["rows"]] != "" else None,
                            "examined": float(r[col["examined"]]) if col["examined"] and r[col["examined"]] != "" else None}
            except (ValueError, KeyError):
                continue
        return out


after = load(a.after)
resets = 0
if a.before:
    before = load(a.before)
    delta = {}
    for k, v in after.items():
        b = before.get(k)
        if b is None:
            delta[k] = v
        elif v["calls"] < b["calls"] or v["total_ms"] < b["total_ms"]:
            resets += 1          # the counters were reset between the snapshots; use the after values
            delta[k] = v
        else:
            delta[k] = {"text": v["text"], "calls": v["calls"] - b["calls"], "total_ms": v["total_ms"] - b["total_ms"],
                        "rows": None if v["rows"] is None or b["rows"] is None else v["rows"] - b["rows"],
                        "examined": None if v["examined"] is None or b["examined"] is None else v["examined"] - b["examined"]}
    after = {k: v for k, v in delta.items() if v["calls"] > 0}

groups = {}
for k, v in after.items():                  # the same statement with different literals or ids is one statement
    n = normalise(v["text"])
    g = groups.setdefault(n, {"text": n, "ids": [], "calls": 0.0, "total_ms": 0.0, "rows": 0.0, "has_rows": False,
                              "examined": 0.0, "has_examined": False})
    g["ids"].append(k)
    g["calls"] += v["calls"]; g["total_ms"] += v["total_ms"]
    if v["rows"] is not None:
        g["rows"] += v["rows"]; g["has_rows"] = True
    if v["examined"] is not None:
        g["examined"] += v["examined"]; g["has_examined"] = True

grand = sum(g["total_ms"] for g in groups.values())
if not groups or grand <= 0:
    sys.exit("no statements ran in the window (check the snapshots and the --before file)")
ranked = sorted(groups.values(), key=lambda g: -g["total_ms"])
cum = 0.0
rows = []
for g in ranked[:a.top]:
    cum += g["total_ms"]
    mean = g["total_ms"] / g["calls"]
    flags = []
    if a.requests and g["calls"] / a.requests >= 2 and mean < 10:
        flags.append(f"possible N+1 ({g['calls'] / a.requests:.1f} calls per request, mean {mean:.1f} ms)")
    if g["has_rows"] and g["rows"] / g["calls"] >= 1000:
        flags.append(f"large results ({g['rows'] / g['calls']:.0f} rows per call)")
    if g["has_examined"] and g["has_rows"] and g["rows"] > 0 and g["examined"] / g["rows"] >= 100:
        flags.append(f"scan-heavy ({g['examined'] / max(g['rows'], 1):.0f} rows examined per row returned)")
    if len(g["ids"]) > 1:
        flags.append(f"{len(g['ids'])} ids with the same shape")
    rows.append({"share_pct": round(100 * g["total_ms"] / grand, 1), "cumulative_pct": round(100 * cum / grand, 1),
                 "total_ms": round(g["total_ms"]), "calls": int(g["calls"]), "mean_ms": round(mean, 2),
                 "calls_per_s": round(g["calls"] / a.window_seconds, 1) if a.window_seconds else None,
                 "flags": flags, "statement": g["text"][:140]})

print(f"# Top statements by total time ({len(groups)} distinct, {grand / 1000:.1f} s of database time in the window)\n")
if resets:
    print(f"Note: {resets} statements had counters lower than in the before snapshot (reset or evicted); their after values are used.\n")
print("| # | share % | cum % | total ms | calls | mean ms | calls/s | flags | statement |")
print("|---|---|---|---|---|---|---|---|---|")
for i, r in enumerate(rows, 1):
    print(f"| {i} | {r['share_pct']} | {r['cumulative_pct']} | {r['total_ms']} | {r['calls']} | {r['mean_ms']} | {r['calls_per_s'] if r['calls_per_s'] is not None else '-'} | {'; '.join(r['flags']) or '-'} | `{r['statement']}` |")
print("\nTotal database time counts waiting as well as work, so a statement can rank high because it queues (locks, a full pool) and not because it is slow alone. Get its plan before changing anything.")
if a.json:
    json.dump(rows, open(a.json, "w"), indent=2)
