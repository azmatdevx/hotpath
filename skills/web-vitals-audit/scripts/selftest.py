#!/usr/bin/env python3
"""Check vitals_summary.py on hand-made run records, and that its rows flow through rollup and the bug drafts.

usage: python3 selftest.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SUMMARY = os.path.join(HERE, "vitals_summary.py")
ROLLUP = os.path.join(HERE, "..", "..", "sweep-rollup", "scripts", "rollup.py")
DRAFT = os.path.join(HERE, "..", "..", "perf-bug-writing", "scripts", "draft_bugs.py")
URL = "http://x.example/page"


def record(lcp, cls, inp, verified=True):
    return {"verified": verified, "conditions": {"cpuSlowdown": 1, "userAgent": "test"},
            "vitals": [{"step": "a", "url": URL, "lcp_ms": 100, "cls": 0, "tbt_ms": 0, "ttfb_ms": 5, "inp_ms": None},
                       {"step": "(end of journey)", "url": URL, "lcp_ms": lcp, "lcpElement": "IMG hero.png", "cls": cls,
                        "fcp_ms": 90, "tbt_ms": 50, "inp_ms": inp, "ttfb_ms": 5}]}


def run(*args, check=True):
    return subprocess.run([sys.executable, "-I", *args], capture_output=True, text=True, check=check)


def main():
    with tempfile.TemporaryDirectory() as d:
        paths = []
        # LCP over the limit in all three runs, CLS in two of three, INP never, TBT never
        for i, (lcp, cls) in enumerate(((3000, 0.2), (3200, 0.2), (3100, 0.05))):
            p = os.path.join(d, f"r{i}.json")
            json.dump(record(lcp, cls, 120), open(p, "w"))
            paths.append(p)
        out = os.path.join(d, "v.json")
        text = run(SUMMARY, "--journey", "tc-v", "--json", out, *paths).stdout
        rows = {r["type"]: r for r in json.load(open(out))}
        checks = {
            "LCP over the limit in every run is consistent": rows["poor-lcp"]["consistent"] and rows["poor-lcp"]["ranges"]["lcp_ms"] == [3000, 3200],
            "LCP element is named": "IMG hero.png" in rows["poor-lcp"]["detail"],
            "CLS in two of three runs is intermittent": "poor-cls" in rows and not rows["poor-cls"]["consistent"] and rows["poor-cls"]["runs_seen"] == 2,
            "metrics under their limits give no finding": "poor-inp" not in rows and "poor-tbt" not in rows and "slow-ttfb" not in rows,
            "only the latest reading per page counts": "100-" not in text and rows["poor-lcp"]["ranges"]["lcp_ms"][0] == 3000,
        }
        # a run that did not verify is refused
        bad = os.path.join(d, "bad.json")
        json.dump(record(3000, 0.2, 120, verified=False), open(bad, "w"))
        refused = run(SUMMARY, "--journey", "tc-v", *paths, bad, check=False)
        checks["an unverified run is refused"] = refused.returncode != 0 and "did not reach its end state" in (refused.stdout + refused.stderr)
        # the rows work in the rollup and the drafts
        roll = os.path.join(d, "roll.json")
        run(ROLLUP, "--include-intermittent", "--json", roll, out)
        bugs = os.path.join(d, "bugs")
        run(DRAFT, roll, "--out", bugs, "--env", "http://x.example", "--build", "t")
        drafts = "".join(open(os.path.join(bugs, f)).read() for f in os.listdir(bugs) if f.startswith("BUG-"))
        checks["a vitals draft has a plain headline"] = "Largest Contentful Paint is 3000-3200 ms" in drafts
        checks["a vitals draft says what is expected"] = "Google's 'good' limit" in drafts
    bad = [k for k, v in checks.items() if not v]
    for k in bad:
        print("FAILED:", k)
    if bad:
        sys.exit(1)
    print(f"OK: {len(checks)} vitals checks pass")


main()
