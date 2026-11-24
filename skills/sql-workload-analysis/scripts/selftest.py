#!/usr/bin/env python3
"""Check rank_statements.py on synthetic before/after statement statistics with known answers.

usage: python3 selftest.py
"""
import csv
import json
import os
import subprocess
import sys
import tempfile

TOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rank_statements.py")
HEADER = ["queryid", "query", "calls", "total_exec_time", "rows"]


def write(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(HEADER); w.writerows(rows)


def run(*args):
    return subprocess.run([sys.executable, "-I", TOOL, *args], capture_output=True, text=True)


def main():
    with tempfile.TemporaryDirectory() as d:
        b, a_, out = (os.path.join(d, n) for n in ("before.csv", "after.csv", "out.json"))
        # counters are cumulative: the run adds the differences below
        write(b, [(1, "SELECT * FROM item WHERE id = 5", 1000, 5000.0, 1000),
                  (2, "SELECT * FROM orders WHERE user_id = 7", 100, 800.0, 100),
                  (3, "UPDATE stock SET qty = qty - 1 WHERE sku = 'A1'", 50, 100.0, 50),
                  (9, "SELECT 1", 5000, 50.0, 5000)])
        write(a_, [(1, "SELECT * FROM item WHERE id = 5", 9000, 17000.0, 9000),            # +8000 calls, +12000 ms, mean 1.5 ms
                   (2, "SELECT * FROM orders WHERE user_id = 7", 300, 20800.0, 300000),    # +200 calls, +20000 ms, 1500 rows per call
                   (3, "UPDATE stock SET qty = qty - 1 WHERE sku = 'A1'", 150, 6100.0, 150),  # +100 calls, +6000 ms
                   (4, "UPDATE stock SET qty = qty - 1 WHERE sku = 'B2'", 40, 1000.0, 40),    # same shape as 3, new id
                   (9, "SELECT 1", 5000, 50.0, 5000)])                                      # no change: not in the window
        r = run(a_, "--before", b, "--requests", "4000", "--window-seconds", "100", "--json", out)
        rows = json.load(open(out)) if r.returncode == 0 else []
        by = {x["statement"]: x for x in rows}
        orders = by.get("SELECT * FROM orders WHERE user_id = ?", {})
        item = by.get("SELECT * FROM item WHERE id = ?", {})
        stock = by.get("UPDATE stock SET qty = qty - ? WHERE sku = ?", {})
        checks = {
            "the run succeeds": r.returncode == 0,
            "statements are ranked by total time in the window": [x["total_ms"] for x in rows] == [20000, 12000, 7000] and rows[0]["statement"].startswith("SELECT * FROM orders"),
            "the window total is the difference of the snapshots": orders.get("total_ms") == 20000 and item.get("total_ms") == 12000,
            "a statement that did not run is left out": "SELECT 1" not in by,
            "the same shape with different literals and ids is one statement": stock.get("calls") == 140 and stock.get("total_ms") == 7000 and any("2 ids" in f for f in stock.get("flags", [])),
            "an N+1 pattern is flagged with calls per request": any("possible N+1" in f for f in item.get("flags", [])),
            "large results are flagged": any("large results" in f for f in orders.get("flags", [])),
            "calls per second use the window": item.get("calls_per_s") == 80.0,
            "literals are masked": all("'A1'" not in x["statement"] and "= 5" not in x["statement"] for x in rows),
        }
        bad = os.path.join(d, "bad.csv"); open(bad, "w").write("a,b\n1,2\n")
        rb = run(bad)
        checks["an export without the needed columns is refused"] = rb.returncode != 0 and "no column found" in (rb.stdout + rb.stderr)
    bad = [k for k, v in checks.items() if not v]
    for k in bad:
        print("FAILED:", k)
    if bad:
        sys.exit(1)
    print(f"OK: {len(checks)} statement-ranking checks pass")


main()
