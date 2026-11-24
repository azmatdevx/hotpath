#!/usr/bin/env python3
"""Group a HAR into named transactions by the journey's steps, for writing a load test script. Standard library only.

usage: har_transactions.py capture.har record.json [--prefix TC01] [--json out.json] [--keep-static]
                           [--keep-third-party]
record.json is the run record that capture-playwright.js writes beside the HAR; its steps carry start and end times.
Each request goes to the step that had started most recently when the request began, so requests fired after a
click belong to the click. Transactions are named NN_<step text>, in journey order, ready to use as transaction
names in the script. Static files and third-party calls are left out unless you keep them.
Query values for secret-like names are masked in the output.
"""
import argparse
import datetime
import json
import re
import sys
import urllib.parse

SECRET_RE = re.compile(r"(token|key|auth|sig|secret|session|code|password|jwt)", re.I)
STATIC = ("javascript", "css", "image", "font", "video", "audio")


def epoch_ms(iso):
    return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000


def slug(text, n=40):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:n] or "step"


def clean(url):
    p = urllib.parse.urlsplit(url)
    q = "&".join(f"{k}={'***' if SECRET_RE.search(k) else v}" for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True))
    return urllib.parse.urlunsplit(("", "", p.path, q, ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("har")
    ap.add_argument("record")
    ap.add_argument("--prefix", default="")
    ap.add_argument("--json")
    ap.add_argument("--keep-static", action="store_true")
    ap.add_argument("--keep-third-party", action="store_true")
    a = ap.parse_args()
    entries = json.load(open(a.har, encoding="utf-8"))["log"]["entries"]
    steps = json.load(open(a.record, encoding="utf-8")).get("steps", [])
    if not steps or any("startedAt" not in s for s in steps):
        sys.exit("the run record has no step start times; capture again with a current capture-playwright.js")
    steps = sorted(steps, key=lambda s: s["startedAt"])
    first_party = next((urllib.parse.urlsplit(e["request"]["url"]).netloc for e in entries
                        if "html" in (e["response"]["content"].get("mimeType") or "")), None)
    names = [f"{(a.prefix + '_') if a.prefix else ''}{i:02d}_{slug(s['name'])}" for i, s in enumerate(steps, 1)]
    groups = {n: [] for n in names}
    dropped = {"static": 0, "third-party": 0, "before the first step": 0}
    for e in sorted(entries, key=lambda e: epoch_ms(e["startedDateTime"])):
        mime = (e["response"]["content"].get("mimeType") or "").lower()
        host = urllib.parse.urlsplit(e["request"]["url"]).netloc
        if not a.keep_static and any(m in mime for m in STATIC):
            dropped["static"] += 1
            continue
        if not a.keep_third_party and first_party and host != first_party:
            dropped["third-party"] += 1
            continue
        t = epoch_ms(e["startedDateTime"])
        owner = None
        for s, n in zip(steps, names):
            if s["startedAt"] <= t:
                owner = n
        if owner is None:
            dropped["before the first step"] += 1
            continue
        groups[owner].append({"method": e["request"]["method"], "path": clean(e["request"]["url"]),
                              "status": e["response"]["status"],
                              "request_bytes": max((e["request"].get("postData") or {}).get("text", "").__len__(), 0),
                              "response_bytes": max(e["response"]["content"].get("size") or 0, 0)})
    print(f"# Transactions from {len(entries)} requests\n")
    for n, s in zip(names, steps):
        print(f"## {n}  (step: {s['name']})\n")
        if not groups[n]:
            print("- no requests\n")
            continue
        for r in groups[n]:
            print(f"- `{r['method']} {r['path']}` -> {r['status']} ({r['response_bytes']} B)")
        print()
    print("Left out: " + ", ".join(f"{v} {k}" for k, v in dropped.items() if v) if any(dropped.values()) else "Nothing left out.")
    if a.json:
        json.dump([{"transaction": n, "step": s["name"], "requests": groups[n]} for n, s in zip(names, steps)],
                  open(a.json, "w", encoding="utf-8"), indent=2)


main()
