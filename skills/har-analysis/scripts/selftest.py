#!/usr/bin/env python3
"""Build a synthetic HAR with planted problems and clean controls, and check the analyzer finds exactly those.

usage: python3 selftest.py
The HAR is built in memory and never written to disk. It is synthetic, so passing this does not show the
analyzer handles every real browser's HAR; run it on a real capture too.
"""
import datetime
import os
import sys

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
    print(f"OK: {len(want)} planted findings found, no extra findings on the controls")


main()
