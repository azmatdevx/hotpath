#!/usr/bin/env python3
"""Check rank_limiters.py on synthetic series with a known cause.

usage: python3 selftest.py
The run lasts 900 s. Load ramps for 300 s and then stays flat. A database wait starts rising at 400 s, and latency
follows it 20 s later. CPU tracks the load (and stays well below its ceiling), a connection pool pins at its maximum, memory and a random series are noise.
Time is given as epoch seconds, epoch milliseconds, and ISO 8601 in different files.
"""
import csv
import datetime
import json
import os
import random
import subprocess
import sys
import tempfile

TOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rank_limiters.py")
T0 = 1_800_000_000


def iso(t):
    return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def main():
    rnd = random.Random(1)
    with tempfile.TemporaryDirectory() as d:
        rate = lambda t: 50 + min(t, 300) * 0.3
        db = lambda t: max(0, t - 400) * 0.4
        ref = os.path.join(d, "ref.csv")
        with open(ref, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["time", "rate_per_s", "p95_ms", "error_pct"])
            for t in range(0, 900, 10):
                w.writerow([T0 + t, round(rate(t), 2), round(100 + 2 * db(max(t - 20, 0)) + rnd.uniform(-3, 3), 1), 0])
        def write(name, fn, tfmt):
            p = os.path.join(d, name + ".csv")
            with open(p, "w", newline="") as f:
                w = csv.writer(f); w.writerow(["time", "value"])
                for t in range(0, 900, 5):
                    w.writerow([tfmt(T0 + t), round(fn(t), 3)])
            return p
        files = [write("db_wait_ms", db, lambda t: t),
                 write("cpu_percent", lambda t: rate(t) * 0.5 + rnd.uniform(-1, 1), lambda t: int(t * 1000)),
                 write("pool_in_use", lambda t: min(100, t / 4), iso),
                 write("heap_mb", lambda t: 500 + rnd.uniform(-5, 5), lambda t: t),
                 write("noise", lambda t: rnd.uniform(0, 100), lambda t: t)]
        out = os.path.join(d, "out.json")
        r = subprocess.run([sys.executable, "-I", TOOL, ref, *files, "--ceiling", "pool_in_use=100", "--ceiling", "cpu_percent=100", "--json", out],
                           capture_output=True, text=True)
        rows = {x["metric"]: x for x in json.load(open(out))} if r.returncode == 0 else {}
        first = json.load(open(out))[0]["metric"] if rows else None
        checks = {
            "the run succeeds": r.returncode == 0,
            "the database wait is ranked first as a candidate limiter": first == "db_wait_ms" and rows["db_wait_ms"]["verdict"].startswith("candidate"),
            "the lag is found (the metric moves about 20 s first)": rows["db_wait_ms"]["lag_s"] in (10, 20, 30),
            "CPU is read as tracking load only": rows["cpu_percent"]["verdict"] == "tracks load only",
            "the pinned pool is reported as saturated": rows["pool_in_use"]["at_ceiling_pct"] >= 50 and rows["pool_in_use"]["verdict"].startswith("saturated"),
            "saturated metrics rank after candidates and before the rest": list(rows)[:3] == ["db_wait_ms", "pool_in_use", "cpu_percent"] or list(rows)[:2] == ["db_wait_ms", "pool_in_use"],
            "CPU, with a ceiling of 100, never gets near it": rows["cpu_percent"]["at_ceiling_pct"] == 0,
            "a metric with no declared ceiling reports none": rows["heap_mb"]["at_ceiling_pct"] is None,
            "memory and noise show no clear relationship": rows["heap_mb"]["verdict"] == "no clear relationship" and rows["noise"]["verdict"] == "no clear relationship",
            "epoch seconds, milliseconds, and ISO times all parse": len(rows) == 5,
        }
        # a metric that rises with the load while latency also rises with the load is not singled out as the limiter
        ref2 = os.path.join(d, "ref2.csv")
        with open(ref2, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["time", "rate_per_s", "p95_ms", "error_pct"])
            for t in range(0, 900, 10):
                w.writerow([T0 + t, round(50 + t * 0.3, 2), round(100 + t * 0.5 + rnd.uniform(-2, 2), 1), 0])
        lin = write("cpu_linear", lambda t: t * 0.1 + rnd.uniform(-0.5, 0.5), lambda t: t)
        out2 = os.path.join(d, "out2.json")
        subprocess.run([sys.executable, "-I", TOOL, ref2, lin, "--json", out2], capture_output=True, text=True)
        v2 = json.load(open(out2))[0]["verdict"]
        checks["a metric that grows with load and latency is not called the limiter"] = v2.startswith("grows with load")
        # several value columns in one file: FILE.csv:COLUMN picks one
        multi = os.path.join(d, "server.csv")
        with open(multi, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["ts", "inuse", "queue", "orders"])
            for t in range(0, 900, 5):
                w.writerow([T0 + t, 8, round(db(t), 3), t])
        out3 = os.path.join(d, "out3.json")
        subprocess.run([sys.executable, "-I", TOOL, ref, multi + ":queue", multi + ":inuse", "--ceiling", "inuse=8", "--json", out3], capture_output=True, text=True)
        rows3 = {x["metric"]: x for x in json.load(open(out3))}
        checks["FILE:COLUMN picks the named column and names the metric after it"] = set(rows3) == {"queue", "inuse"} and rows3["queue"]["verdict"].startswith("candidate") and rows3["inuse"]["verdict"].startswith("saturated")
        short = os.path.join(d, "short.csv")
        with open(short, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["time", "rate_per_s", "p95_ms", "error_pct"])
            for t in range(0, 60, 10):
                w.writerow([T0 + t, 10, 100, 0])
        rr = subprocess.run([sys.executable, "-I", TOOL, short, files[0]], capture_output=True, text=True)
        checks["a reference series that is too short is refused"] = rr.returncode != 0 and "fewer than 12" in (rr.stdout + rr.stderr)
    bad = [k for k, v in checks.items() if not v]
    for k in bad:
        print("FAILED:", k)
    if bad:
        sys.exit(1)
    print(f"OK: {len(checks)} limiter-ranking checks pass")


main()
