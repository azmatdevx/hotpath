#!/usr/bin/env python3
"""Find the dynamic values in a journey by diffing two HARs of the same journey recorded as different users.
Standard library only.

usage: har_correlate.py a.har b.har [--json out.json] [--keep-static]
Both HARs must contain response bodies (record them with bodies embedded) and the same sequence of requests.

For every value that differs between the two recordings it reports:
  correlation  the value first appears in an earlier response, in both recordings, at the same place: extract it
               there and substitute it where it is used
  cookie       a cookie value that comes from Set-Cookie: the tool's cookie jar normally handles it
  parameter    a value no earlier response contains (a username, a search term, an id): test data
  generated    a client-made timestamp or UUID: compute it in the script
Values are masked in the output (first characters and length), so the report does not leak secrets.
It does not decide for you: check each candidate, and see script-correlation for what to do with it.
"""
import argparse
import base64
import collections
import json
import re
import sys
import urllib.parse

ID_RE = re.compile(r"(?<=/)(\d+|[0-9a-f]{8}-[0-9a-f-]{27}|[0-9a-f]{12,})(?=/|$)", re.I)
STATIC_MIME = ("javascript", "css", "image", "font", "video", "audio")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
MIN_LEN = 4


def mask(v):
    v = str(v)
    return f"{v[:4]}...({len(v)} chars)" if len(v) > 8 else f"{v[:2]}...({len(v)} chars)"


def headers_of(h):
    return [(x["name"].lower(), x.get("value", "")) for x in h or []]


def body_text(content):
    t = content.get("text")
    if t is None:
        return ""
    if content.get("encoding") == "base64":
        try:
            return base64.b64decode(t).decode("utf-8", "replace")
        except Exception:
            return ""
    return t


def flatten(obj, prefix="$"):
    """Leaf values of a JSON document with their paths."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from flatten(v, f"{prefix}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from flatten(v, f"{prefix}[{i}]")
    elif obj is not None and not isinstance(obj, bool):
        yield prefix, str(obj)


def load(path):
    har = json.load(open(path, encoding="utf-8"))
    entries = har["log"]["entries"]
    first_party = next((urllib.parse.urlsplit(e["request"]["url"]).netloc for e in entries
                        if "html" in (e["response"]["content"].get("mimeType") or "")), None)
    out = []
    for e in entries:
        mime = (e["response"]["content"].get("mimeType") or "").lower()
        host = urllib.parse.urlsplit(e["request"]["url"]).netloc
        if any(m in mime for m in STATIC_MIME) or (first_party and host != first_party):
            continue
        out.append(e)
    if not any(body_text(e["response"]["content"]) for e in out):
        sys.exit(f"{path}: no response bodies recorded; record the HAR with bodies embedded")
    return out


def dynamic_segment(seg):
    """A path segment that is probably an id: digits, a UUID, long hex, or a long mix of letters and digits."""
    return bool(ID_RE.fullmatch(seg)) or (len(seg) >= 8 and re.search(r"\d", seg) is not None
                                         and re.search(r"[A-Za-z]", seg) is not None)


def template(url):
    return "/".join("{id}" if dynamic_segment(seg) else seg for seg in urllib.parse.urlsplit(url).path.split("/"))


def fields(e):
    """The values a request carries: (location, name, value)."""
    r = e["request"]
    u = urllib.parse.urlsplit(r["url"])
    out = []
    for i, seg in enumerate(u.path.split("/")):
        if seg and dynamic_segment(seg):
            out.append(("path", f"segment {i}", seg))
    out += [("query", k, v) for k, v in urllib.parse.parse_qsl(u.query, keep_blank_values=True)]
    pd = r.get("postData") or {}
    text, mt = pd.get("text") or "", (pd.get("mimeType") or "").lower()
    if text and "json" in mt:
        try:
            out += [("json", p, v) for p, v in flatten(json.loads(text))]
        except ValueError:
            pass
    elif text and "x-www-form-urlencoded" in mt:
        out += [("form", k, v) for k, v in urllib.parse.parse_qsl(text, keep_blank_values=True)]
    for name, value in headers_of(r.get("headers")):
        if name == "authorization":
            out.append(("header", name, re.sub(r"^\w+\s+", "", value)))
        elif name == "cookie":
            out += [("cookie", c.split("=", 1)[0].strip(), c.split("=", 1)[1].strip())
                    for c in value.split(";") if "=" in c]
        elif name.startswith("x-") and name not in ("x-forwarded-for", "x-requested-with"):
            out.append(("header", name, value))
    return out


def find_source(value, entries, upto):
    """The first earlier response that contains the value, and where in it."""
    for j in range(upto):
        resp = entries[j]["response"]
        for name, hv in headers_of(resp.get("headers")):
            if name == "set-cookie" and re.match(rf"^[^=]+={re.escape(value)}(;|$)", hv.strip()):
                return j, "cookie", f"Set-Cookie {hv.split('=', 1)[0]}"
            if value in hv:
                return j, "header", f"response header {name}"
        text = body_text(resp["content"])
        if value not in text:
            continue
        try:
            for p, v in flatten(json.loads(text)):
                if v == value:
                    return j, "body", f"JSON {p}"
        except ValueError:
            pass
        m = re.search(r"<input[^>]*name=[\"']([^\"']+)[\"'][^>]*value=[\"']" + re.escape(value), text) or \
            re.search(r"<input[^>]*value=[\"']" + re.escape(value) + r"[\"'][^>]*name=[\"']([^\"']+)", text)
        if m:
            return j, "body", f"HTML input[name={m.group(1)}] value"
        i = text.index(value)
        return j, "body", f"text between {text[max(0, i - 12):i]!r} and {text[i + len(value):i + len(value) + 12]!r}"
    return None


def classify_unsourced(value):
    if re.fullmatch(r"\d{10}|\d{13}", value):
        return "generated", "timestamp"
    if UUID_RE.match(value):
        return "generated", "UUID"
    return "parameter", "no earlier response contains it"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--json")
    a = ap.parse_args()
    A, B = load(a.a), load(a.b)

    def keyed(entries):
        seen, out = collections.Counter(), {}
        for i, e in enumerate(entries):
            k = (e["request"]["method"], template(e["request"]["url"]))
            seen[k] += 1
            out[(k, seen[k])] = i
        return out
    ka, kb = keyed(A), keyed(B)
    shared = [k for k in ka if k in kb]
    if len(shared) < 0.5 * max(len(ka), len(kb)):
        sys.exit("the two recordings do not follow the same sequence of requests; record the same journey twice")

    groups = {}   # value in A -> info
    for key in shared:
        ia, ib = ka[key], kb[key]
        fb = {(loc, name): v for loc, name, v in fields(B[ib])}
        for loc, name, va in fields(A[ia]):
            vb = fb.get((loc, name))
            if vb is None or vb == va or len(va) < MIN_LEN:
                continue
            g = groups.setdefault(va, {"value_b": vb, "uses": []})
            g["uses"].append((ia, key[0], loc, name))

    results = []
    for va, g in groups.items():
        first = min(u[0] for u in g["uses"])
        src_a = find_source(va, A, first)
        src_b = find_source(g["value_b"], B, min(first, len(B)))
        if src_a:
            j, kind, where = src_a
            conf = "confirmed" if src_b and src_b[2] == where else "seen in one recording only"
            kind_out = "cookie" if kind == "cookie" else "correlation"
            source = {"request": f"{A[j]['request']['method']} {template(A[j]['request']['url'])}", "index": j, "where": where}
        else:
            kind_out, why = classify_unsourced(va)
            conf, source = why, None
        results.append({"kind": kind_out, "value": mask(va), "confidence": conf, "source": source,
                        "uses": [{"index": i, "request": f"{m[0]} {m[1]}", "location": loc, "name": n}
                                 for i, m, loc, n in g["uses"]]})
    order = {"correlation": 0, "cookie": 1, "parameter": 2, "generated": 3}
    results.sort(key=lambda r: (order[r["kind"]], r["uses"][0]["index"]))

    print(f"# Dynamic values: {len(A)} requests in A, {len(B)} in B, {len(shared)} aligned\n")
    for kind, title in (("correlation", "Correlate (extract from a response, substitute later)"),
                        ("cookie", "Cookies (normally handled by the cookie jar)"),
                        ("parameter", "Parameters (test data)"), ("generated", "Generated by the client")):
        rows = [r for r in results if r["kind"] == kind]
        print(f"## {title} ({len(rows)})\n")
        for r in rows:
            uses = "; ".join(f"{u['request']} {u['location']} `{u['name']}`" for u in r["uses"][:4])
            more = f" (+{len(r['uses']) - 4} more)" if len(r["uses"]) > 4 else ""
            if r["source"]:
                print(f"- `{r['value']}` from {r['source']['request']}: {r['source']['where']} [{r['confidence']}]. Used in: {uses}{more}")
            else:
                print(f"- `{r['value']}` ({r['confidence']}). Used in: {uses}{more}")
        print()
    if a.json:
        json.dump(results, open(a.json, "w", encoding="utf-8"), indent=2)


main()
