#!/usr/bin/env python3
"""Analyse a HAR file for common front-end and API performance problems. Standard library only.

usage: analyze_har.py capture.har [--slow-ms 1000] [--big-kb 500] [--static-kb 300] [--json]

Reports findings by type with evidence. It does not assign severity; see the perf-bug-writing skill.
Query values for names that look like secrets are masked in the output.
"""
import argparse
import collections
import datetime
import json
import re
import sys
import urllib.parse

SECRET_RE = re.compile(r"(token|key|auth|sig|secret|session|code|password|jwt)", re.I)
ID_RE = re.compile(r"(?<=/)(\d+|[0-9a-f]{8}-[0-9a-f-]{27}|[0-9a-f]{12,})(?=/|$)", re.I)
TEXT_MIME = ("json", "javascript", "css", "html", "xml", "svg", "text/plain")


def hdr(headers, name):
    for h in headers or []:
        if h.get("name", "").lower() == name:
            return h.get("value", "")
    return ""


def clean(url):
    p = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
    q = "&".join(f"{k}={'***' if SECRET_RE.search(k) else v}" for k, v in q)
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, q, ""))


def kind(e):
    rt = (e.get("_resourceType") or "").lower()
    mime = (e["response"]["content"].get("mimeType") or "").lower()
    if "event-stream" in mime or rt in ("websocket", "eventsource"):
        return "stream"
    if rt in ("xhr", "fetch"):
        return "api"
    if rt in ("script", "stylesheet", "image", "font", "media"):
        return {"stylesheet": "css", "script": "js"}.get(rt, rt)
    if "javascript" in mime:
        return "js"
    if "css" in mime:
        return "css"
    if "svg" in mime or mime.startswith("image/"):
        return "image"
    if "font" in mime:
        return "font"
    if "html" in mime:
        return "document"
    if "json" in mime or "xml" in mime:
        return "api"
    return "other"


def decoded(e):
    return max(e["response"]["content"].get("size") or 0, 0)


def transfer(e):
    r = e["response"]
    for v in (r.get("_transferSize"), r.get("bodySize")):
        if isinstance(v, (int, float)) and v >= 0:
            return int(v)
    return decoded(e)


def started(e):
    s = e["startedDateTime"].replace("Z", "+00:00")
    return datetime.datetime.fromisoformat(s).timestamp()


def kb(n):
    return f"{n / 1024:.0f} KB" if n < 1024 * 1024 else f"{n / 1024 / 1024:.1f} MB"


def analyze(har, slow_ms=1000, big_kb=500, static_kb=300):
    entries = har["log"]["entries"]
    findings = []

    def add(t, e, detail, **ev):
        findings.append({"type": t, "url": clean(e["request"]["url"]), "method": e["request"]["method"],
                         "detail": detail, **ev})

    by_url = {}
    groups = collections.defaultdict(list)
    templ = collections.defaultdict(list)
    for e in entries:
        k = kind(e)
        e["_k"] = k
        by_url.setdefault(e["request"]["url"], e)
        body = (e["request"].get("postData") or {}).get("text", "")
        groups[(e["request"]["method"], e["request"]["url"], body)].append(e)
        p = urllib.parse.urlsplit(e["request"]["url"])
        if k == "api":
            templ[(e["request"]["method"], p.netloc + ID_RE.sub("{id}", p.path))].append(e)

    for e in entries:
        r, k = e["response"], e["_k"]
        status, t = r["status"], e["time"]
        dsize, tsize = decoded(e), transfer(e)
        wait = (e.get("timings") or {}).get("wait", 0) or 0
        mime = (r["content"].get("mimeType") or "").lower()
        if k == "stream":
            continue
        if status == 0 or status >= 400:
            add("failed-request", e, f"status {status}")
        if t >= slow_ms:
            part = "server wait" if wait >= 0.6 * t else "download or other"
            add("slow-request", e, f"{t:.0f} ms total, {wait:.0f} ms waiting for the server ({part})",
                time_ms=round(t), wait_ms=round(wait), kind=k)
        limit = static_kb if k in ("js", "css", "image", "font") else big_kb
        if max(dsize, tsize) > limit * 1024:
            add("large-payload", e, f"{kb(tsize)} on the wire, {kb(dsize)} decoded ({k})",
                transfer=tsize, decoded=dsize, kind=k)
        if (status == 200 and dsize >= 1024 and any(m in mime for m in TEXT_MIME)
                and not hdr(r.get("headers"), "content-encoding")):
            add("uncompressed", e, f"{kb(dsize)} of {mime} sent with no content-encoding",
                decoded=dsize)
        if k in ("js", "css", "image", "font") and status == 200 and dsize >= 10 * 1024:
            cc = hdr(r.get("headers"), "cache-control").lower()
            if (not cc and not hdr(r.get("headers"), "expires")) or "no-store" in cc or "max-age=0" in cc:
                add("not-cacheable", e, f"{kb(dsize)} {k} with cache-control '{cc or 'missing'}'",
                    decoded=dsize)

    for (m, _, _), es in groups.items():
        if len(es) < 2 or es[0]["_k"] == "stream":
            continue
        starts = sorted(started(x) for x in es)
        gaps = [b - a for a, b in zip(starts, starts[1:])]
        mean = sum(gaps) / len(gaps)
        if len(es) >= 3 and min(gaps) >= 1 and (max(gaps) - min(gaps)) <= 0.25 * mean:
            t = "polling"
            note = f"{len(es)} calls about every {mean:.1f} s (looks like polling; confirm it is intended)"
        else:
            t = "duplicate-concurrent" if min(gaps) < 0.5 else "duplicate"
            note = f"{len(es)} identical calls, smallest gap {min(gaps) * 1000:.0f} ms"
        wasted = sum(transfer(x) for x in es[1:])
        add(t, es[0], note + f"; {kb(wasted)} repeated", count=len(es), repeated_bytes=wasted)

    for (m, _), es in templ.items():
        urls = {x["request"]["url"] for x in es}
        if len(urls) >= 5:
            total = sum(x["time"] for x in es)
            add("n-plus-one", es[0], f"{len(urls)} different ids fetched one by one from this path, {total:.0f} ms of "
                "request time in total", count=len(urls), total_ms=round(total))

    for e in entries:
        if 300 <= e["response"]["status"] < 400 and e["response"]["status"] != 304:
            hops, cur = 0, e
            while cur is not None and 300 <= cur["response"]["status"] < 400 and hops < 10:
                hops += 1
                nxt = urllib.parse.urljoin(cur["request"]["url"], hdr(cur["response"].get("headers"), "location"))
                cur = by_url.get(nxt)
            if hops >= 2 or e["_k"] == "api":
                add("redirect", e, f"{hops} redirect hop(s) before the final response", hops=hops)

    first_party = next((urllib.parse.urlsplit(e["request"]["url"]).netloc for e in entries if e["_k"] == "document"),
                       None)
    third = collections.Counter()
    for e in entries:
        host = urllib.parse.urlsplit(e["request"]["url"]).netloc
        if first_party and host != first_party:
            third[host] += transfer(e)
    total = sum(transfer(e) for e in entries)
    summary = {
        "requests": len(entries),
        "transfer_bytes": total,
        "by_kind": dict(collections.Counter(e["_k"] for e in entries)),
        "first_party_host": first_party,
        "third_party_bytes": sum(third.values()),
        "top_third_party": third.most_common(3),
    }
    order = ["failed-request", "slow-request", "duplicate-concurrent", "n-plus-one", "large-payload",
             "uncompressed", "not-cacheable", "duplicate", "redirect", "polling"]
    findings.sort(key=lambda f: (order.index(f["type"]), -f.get("time_ms", f.get("decoded", f.get("count", 0)))))
    return summary, findings


def render(summary, findings):
    out = [f"# HAR analysis\n",
           f"{summary['requests']} requests, {kb(summary['transfer_bytes'])} transferred, "
           f"by kind {summary['by_kind']}.",
           f"Third-party traffic: {kb(summary['third_party_bytes'])}"
           + (f" ({', '.join(h for h, _ in summary['top_third_party'])})" if summary['top_third_party'] else "")
           + ".\n"]
    if not findings:
        out.append("No findings at these thresholds.")
    for t in dict.fromkeys(f["type"] for f in findings):
        rows = [f for f in findings if f["type"] == t]
        out.append(f"## {t} ({len(rows)})\n")
        for f in rows:
            out.append(f"- `{f['method']} {f['url']}`: {f['detail']}")
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("har")
    ap.add_argument("--slow-ms", type=float, default=1000)
    ap.add_argument("--big-kb", type=float, default=500, help="threshold for API and document responses")
    ap.add_argument("--static-kb", type=float, default=300, help="threshold for js, css, image, font")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    with open(a.har, encoding="utf-8") as f:
        har = json.load(f)
    s, fs = analyze(har, a.slow_ms, a.big_kb, a.static_kb)
    print(json.dumps({"summary": s, "findings": fs}, indent=2) if a.json else render(s, fs))
