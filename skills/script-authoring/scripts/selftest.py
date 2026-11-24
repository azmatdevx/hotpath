#!/usr/bin/env python3
"""Check har_transactions.py on a synthetic HAR and run record.

usage: python3 selftest.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "har_transactions.py")
T0 = 1_767_225_600_000   # 2026-01-01T00:00:00Z in ms


def iso(ms):
    import datetime
    return datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def entry(at, method, url, mime="application/json", status=200, body=None):
    e = {"startedDateTime": iso(T0 + at), "time": 5,
         "request": {"method": method, "url": url, "headers": []},
         "response": {"status": status, "headers": [], "content": {"mimeType": mime, "size": 100}}}
    if body:
        e["request"]["postData"] = {"mimeType": "application/json", "text": body}
    return e


def main():
    h = "https://shop.example"
    har = {"log": {"entries": [
        entry(1000, "GET", h + "/", "text/html"),
        entry(1100, "GET", h + "/static/app.js", "application/javascript"),
        entry(1200, "GET", "https://ads.example/collect"),
        entry(1300, "GET", h + "/api/config"),
        entry(3000, "POST", h + "/api/login?token=SECRETVALUE", body='{"u":"a"}'),
        entry(3050, "GET", h + "/api/me"),
        entry(6000, "GET", h + "/api/search?q=laptop"),
    ]}}
    record = {"steps": [
        {"name": "Open the home page", "ok": True, "startedAt": T0 + 900, "endedAt": T0 + 2500},
        {"name": "Log in as the test user", "ok": True, "startedAt": T0 + 2900, "endedAt": T0 + 3500},
        {"name": "Search for a laptop!", "ok": True, "startedAt": T0 + 5900, "endedAt": T0 + 6500},
    ]}
    with tempfile.TemporaryDirectory() as d:
        ph, pr, out = (os.path.join(d, n) for n in ("a.har", "r.json", "out.json"))
        json.dump(har, open(ph, "w")); json.dump(record, open(pr, "w"))
        r = subprocess.run([sys.executable, "-I", TOOL, ph, pr, "--prefix", "TC01", "--json", out], capture_output=True, text=True)
        tx = {t["transaction"]: [x["path"] for x in t["requests"]] for t in json.load(open(out))}
        old = os.path.join(d, "old.json")
        json.dump({"steps": [{"name": "x", "ok": True}]}, open(old, "w"))
        refused = subprocess.run([sys.executable, "-I", TOOL, ph, old], capture_output=True, text=True)
    checks = {
        "transactions are named in journey order from the step text": list(tx) == ["TC01_01_open_the_home_page", "TC01_02_log_in_as_the_test_user", "TC01_03_search_for_a_laptop"],
        "the page and its API call belong to the first step": tx["TC01_01_open_the_home_page"] == ["/", "/api/config"],
        "requests after the click belong to the click": tx["TC01_02_log_in_as_the_test_user"] == ["/api/login?token=***", "/api/me"],
        "the last step gets its request": tx["TC01_03_search_for_a_laptop"] == ["/api/search?q=laptop"],
        "static files and third-party calls are left out": "app.js" not in r.stdout and "ads.example" not in r.stdout and "Left out: 1 static, 1 third-party" in r.stdout,
        "secret query values are masked": "SECRETVALUE" not in r.stdout,
        "a record without step times is refused": refused.returncode != 0 and "no step start times" in (refused.stdout + refused.stderr),
    }
    bad = [k for k, v in checks.items() if not v]
    for k in bad:
        print("FAILED:", k)
    if bad:
        sys.exit(1)
    print(f"OK: {len(checks)} transaction checks pass")


main()
