#!/usr/bin/env python3
"""Build a synthetic HAR with planted problems and clean controls, and check the analyzer finds exactly those.

usage: python3 selftest.py
The HAR is built in memory and never written to disk. It is synthetic, so passing this does not show the
analyzer handles every real browser's HAR; run it on a real capture too.
"""
import datetime
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_har import analyze  # noqa: E402

T0 = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
HOST = "https://shop.example"


def entry(path, at, ms=80, wait=None, status=200, mime="application/json", size=2000, enc="gzip",
          cc="public, max-age=3600", rtype="xhr", method="GET", host=HOST, location=None):
    headers = [{"name": "cache-control", "value": cc}] if cc else []
    if enc:
        headers.append({"name": "content-encoding", "value": enc})
    if location:
        headers.append({"name": "location", "value": location})
    return {
        "startedDateTime": (T0 + datetime.timedelta(seconds=at)).isoformat(),
        "time": ms,
        "_resourceType": rtype,
        "request": {"method": method, "url": host + path, "headers": []},
        "response": {"status": status, "headers": headers, "bodySize": size // 3 if enc else size,
                     "content": {"size": size, "mimeType": mime}},
        "timings": {"wait": wait if wait is not None else ms * 0.8, "receive": ms * 0.1},
    }


def build():
    e = [entry("/", 0, mime="text/html", size=30000, rtype="document", cc="no-cache")]
    # controls: all of these must produce no finding
    e += [entry("/static/app.js", 0.1, mime="application/javascript", size=120000, rtype="script",
                cc="public, max-age=31536000, immutable"),
          entry("/api/fast", 0.2, ms=90),
          entry("/img/logo.png", 0.2, mime="image/png", size=20000, enc="", rtype="image")]
    # planted problems
    e += [entry("/api/slow-report", 1, ms=2600, wait=2500),
          entry("/api/huge-list", 1, ms=700, size=3_400_000),
          entry("/static/vendor.js", 1, mime="application/javascript", size=2_000_000, enc="", rtype="script",
                cc=""),
          entry("/img/hero.png", 1, mime="image/png", size=1_800_000, enc="", rtype="image",
                cc="public, max-age=86400")]
    e += [entry("/api/profile", 2 + i * 0.05) for i in range(3)]              # concurrent duplicates
    e += [entry("/api/items/%d" % n, 3 + n * 0.05) for n in range(1, 9)]      # N+1
    e += [entry("/api/missing", 4, status=404)]
    e += [entry("/old", 4, status=301, mime="text/html", size=0, location=HOST + "/older", rtype="document"),
          entry("/older", 4.1, status=302, mime="text/html", size=0, location=HOST + "/new", rtype="document"),
          entry("/new", 4.2, mime="text/html", size=1000, rtype="document")]
    # control: polling every 5 s is reported as polling, not as a duplicate
    e += [entry("/api/notifications", 5 + 5 * i) for i in range(4)]
    e += [entry("/track.js", 5, mime="application/javascript", size=40000, rtype="script",
                host="https://ads.example")]
    return {"log": {"entries": e}}


def check_runs_and_rollup():
    """Two runs where one finding is missing from the second: it must be intermittent, the rest consistent."""
    here = os.path.dirname(os.path.abspath(__file__))
    rollup = os.path.join(here, "..", "..", "sweep-rollup", "scripts", "rollup.py")
    with tempfile.TemporaryDirectory() as d:
        full = build()
        fewer = build()
        fewer["log"]["entries"] = [x for x in fewer["log"]["entries"] if "/api/missing" not in x["request"]["url"]]
        paths = []
        for i, har in enumerate((full, fewer)):
            p = os.path.join(d, f"run{i}.har")
            json.dump(har, open(p, "w"))
            paths.append(p)
        outs = []
        for j in ("tc-a", "tc-b"):
            o = os.path.join(d, j + ".json")
            subprocess.run([sys.executable, "-I", os.path.join(here, "compare_runs.py"), "--journey", j,
                            "--json", o] + paths, check=True, capture_output=True)
            outs.append(o)
        # a request that repeats inside one HAR (here a second slow call) must still count once per run
        twice = build()
        twice["log"]["entries"].append(entry("/api/slow-report", 9, ms=2600, wait=2500))
        tp = [os.path.join(d, f"twice{i}.har") for i in range(2)]
        for p_ in tp:
            json.dump(twice, open(p_, "w"))
        to = os.path.join(d, "twice.json")
        subprocess.run([sys.executable, "-I", os.path.join(here, "compare_runs.py"), "--journey", "tc-t",
                        "--json", to] + tp, check=True, capture_output=True)
        slow = next(r for r in json.load(open(to)) if r["type"] == "slow-request")
        assert slow["runs_seen"] == 2 and slow["consistent"], "per-run counting: a repeat inside one HAR is one run"
        rows = json.load(open(outs[0]))
        cons = {(r["type"], r["url"].replace(HOST, "")): r["consistent"] for r in rows}
        assert cons[("failed-request", "/api/missing")] is False, "missing finding should be intermittent"
        assert cons[("slow-request", "/api/slow-report")] is True, "repeated finding should be consistent"
        roll_json = os.path.join(d, "roll.json")
        text = subprocess.run([sys.executable, "-I", rollup, "--json", roll_json] + outs, check=True,
                              capture_output=True, text=True).stdout
        line = next(l for l in text.splitlines() if "/api/slow-report" in l)
        assert "tc-a, tc-b (2)" in line, "the same problem in two journeys should be one row listing both"
        assert "/api/missing" not in text, "intermittent findings must be left out by default"

        # drafts: one per request, unfinished drafts are rejected, finished ones pass
        draft = os.path.join(here, "..", "..", "perf-bug-writing", "scripts", "draft_bugs.py")
        bugs = os.path.join(d, "bugs")
        subprocess.run([sys.executable, "-I", draft, roll_json, "--out", bugs, "--env", HOST, "--build", "t"],
                       check=True, capture_output=True)
        # a thresholds note with no numbers must not hide the real default values
        subprocess.run([sys.executable, "-I", draft, roll_json, "--out", bugs, "--env", HOST, "--build", "t",
                        "--thresholds", "analyzer defaults"], check=True, capture_output=True)
        some = open(os.path.join(bugs, sorted(f for f in os.listdir(bugs) if f.startswith("BUG-"))[0])).read()
        assert "1000 ms" in some and "300 KB" in some, "default thresholds must be written out"
        files = sorted(f for f in os.listdir(bugs) if f.startswith("BUG-"))
        vendor = [f for f in files if "vendor-js" in f]
        assert len(vendor) == 1, "several problems on one request must be one draft"
        assert "uncompressed" in open(os.path.join(bugs, vendor[0])).read(), "the draft must list every problem"
        unfinished = subprocess.run([sys.executable, "-I", draft, "--check", bugs], capture_output=True)
        assert unfinished.returncode != 0, "a draft with placeholders must fail the check"
        for f in files:
            path = os.path.join(bugs, f)
            t = open(path).read().replace("(agent: fill in)", "filled")
            open(path, "w").write(t)
        finished = subprocess.run([sys.executable, "-I", draft, "--check", bugs], capture_output=True, text=True)
        assert finished.returncode == 0, finished.stdout


def main():
    summary, findings = analyze(build())
    got = {(f["type"], f["url"].replace(HOST, "")) for f in findings}
    want = {
        ("slow-request", "/api/slow-report"),
        ("large-payload", "/api/huge-list"),
        ("large-payload", "/static/vendor.js"),
        ("uncompressed", "/static/vendor.js"),
        ("not-cacheable", "/static/vendor.js"),
        ("large-payload", "/img/hero.png"),
        ("duplicate-concurrent", "/api/profile"),
        ("n-plus-one", "/api/items/1"),
        ("failed-request", "/api/missing"),
        ("redirect", "/old"),
        ("polling", "/api/notifications"),
    }
    # hero.png is 1.8 MB with no content-encoding but png is not a text type, so it is not 'uncompressed'
    missing, extra = want - got, got - want
    for t in sorted(missing):
        print("MISSING", t)
    for t in sorted(extra):
        print("UNEXPECTED", t)
    if summary["top_third_party"][0][0] != "ads.example":
        print("third-party host not detected")
        missing.add(("summary", "third-party"))
    if missing or extra:
        sys.exit(1)
    check_runs_and_rollup()
    print(f"OK: {len(want)} planted findings found, no extra findings on the controls; cross-run, rollup and bug-draft checks pass")


main()
