#!/usr/bin/env python3
"""Write one markdown draft per problem for a person to verify and log. Standard library only.

usage: draft_bugs.py rollup.json --out bugs/ --env URL --build BUILD [--cache cold] [--thresholds "API 1 s, ..."]
       draft_bugs.py --check bugs/

The drafts hold the evidence exactly as the analyzer produced it. Two lines are left for the agent to fill from
the rubric in SKILL.md: 'Impact' and 'Proposed severity'. --check fails while any draft still has a placeholder
or a missing evidence section, so an unfinished draft cannot be handed over by mistake.
Nothing here files anything. A person verifies each draft, logs it, and records the ticket in the file.
"""
import argparse
import glob
import json
import os
import re
import sys
import urllib.parse

PLACEHOLDER = "(agent: fill in)"
DEFAULT_THRESHOLDS = "analyzer defaults: slow over 1000 ms, API and document responses over 500 KB, static files over 300 KB"
SECTIONS = ("## Where", "## Seen", "## Expected", "## Impact", "## Evidence", "## Not tested", "## Engineer verification")


def num(r, k, unit=""):
    v = r["ranges"].get(k)
    return None if not v else (f"{v[0]}{unit}" if v[0] == v[1] else f"{v[0]}-{v[1]}{unit}")


def kb(n):
    return f"{n / 1024 / 1024:.1f} MB" if n >= 1024 * 1024 else f"{n / 1024:.0f} KB"


def headline(r):
    t, path = r["type"], urllib.parse.urlsplit(r["url"]).path or "/"
    ref = f"{r['method']} {path}"
    rg = r["ranges"]
    if t == "slow-request": return f"{ref} takes {num(r, 'time_ms', ' ms')}"
    if t == "large-payload":
        v = rg.get("transfer") or rg.get("decoded")
        return f"{ref} sends {kb(v[1])}" if v else f"{ref} has a large response"
    if t == "uncompressed": return f"{ref} sends {kb(rg['decoded'][1])} with no compression"
    if t == "not-cacheable": return f"{ref} ({kb(rg['decoded'][1])}) is not cacheable"
    if t in ("duplicate", "duplicate-concurrent"):
        return f"{ref} is called {num(r, 'count')} times" + (" at once" if t == "duplicate-concurrent" else "")
    if t == "n-plus-one": return f"{ref.rsplit('/', 1)[0]}/{{id}} is called {num(r, 'count')} times, one per id"
    if t == "polling": return f"{ref} is polled {num(r, 'count')} times"
    if t == "redirect": return f"{ref} redirects {num(r, 'hops')} time(s)"
    if t == "failed-request": return f"{ref} fails"
    return f"{ref}: {t}"


EXPECTED = {
    "slow-request": "Within the agreed API budget ({thr}).",
    "large-payload": "Within the agreed size limits ({thr}), or the page uses the whole response.",
    "uncompressed": "Text responses over 1 KB are compressed.",
    "not-cacheable": "Static files carry cache headers so repeat visits do not refetch them.",
    "duplicate": "The same data is fetched once unless it can have changed in between.",
    "duplicate-concurrent": "The same data is fetched once; concurrent identical calls are redundant.",
    "n-plus-one": "One batch or list call, not one call per id.",
    "polling": "Polling only where intended, at an interval the product accepts, and stopped when not needed.",
    "redirect": "The client requests the final URL directly.",
    "failed-request": "No failed calls on the happy path.",
}


ORDER = ["failed-request", "slow-request", "duplicate-concurrent", "n-plus-one", "large-payload",
         "uncompressed", "not-cacheable", "duplicate", "redirect", "polling"]


def group(rows):
    """One draft per request: several problems on the same request are one bug, as perf-bug-writing says."""
    by = {}
    for r in rows:
        by.setdefault((r["method"], r["url"]), []).append(r)
    out = []
    for rs in by.values():
        rs.sort(key=lambda r: ORDER.index(r["type"]) if r["type"] in ORDER else 99)
        out.append(rs)
    out.sort(key=lambda rs: (-len({j for r in rs for j in r["journeys"]}), ORDER.index(rs[0]["type"]) if rs[0]["type"] in ORDER else 99))
    return out


def draft(i, rs, a):
    r = rs[0]
    title = headline(r) + (f" (and {len(rs) - 1} more problem{'s' if len(rs) > 2 else ''} on the same request)" if len(rs) > 1 else "")
    journeys = sorted({j for x in rs for j in x["journeys"]})
    r = {**r, "journeys": journeys, "runs": {j: x["runs"][j] for x in rs for j in x["journeys"]},
         "hars": {j: x["hars"].get(j, []) for x in rs for j in x["journeys"]}}
    evid = "; ".join(f"{x['type']}: " + (", ".join(f"{k} {num(x, k)}" for k in x["ranges"]) or "no numeric evidence") for x in rs)
    seen_lines = "\n".join(f"- `{x['type']}`: {x['detail']}" for x in rs)
    # a thresholds note with no number in it ("analyzer defaults") would hide the real values, so use those
    thr = a.thresholds if a.thresholds and re.search(r"\d", a.thresholds) else DEFAULT_THRESHOLDS
    expected_lines = "\n".join("- " + EXPECTED.get(x["type"], "Per the team standard.").format(thr=thr) for x in rs)
    where = "\n".join(f"- {j}: {a.cache or 'cache state not stated'}, {r['runs'][j]} runs, captures: "
                      f"{', '.join(r['hars'].get(j, [])[:3])}{' ...' if len(r['hars'].get(j, [])) > 3 else ''}"
                      for j in r["journeys"])
    return f"""# BUG-{i:02d}: {title}

Status: DRAFT, not verified by a person. Logged as: (engineer fills in after logging)

## Where
Environment: {a.env}, build {a.build}
{where}

## Seen
`{r['method']} {r['url']}` in {len(journeys)} journey(s). Ranges across runs: {evid}.
{seen_lines}

## Expected
{expected_lines}

## Impact
{PLACEHOLDER}

Proposed severity: {PLACEHOLDER}

## Evidence
- Request: `{r['method']} {r['url']}` (query values for secret-like names are masked)
- Ranges across runs: {evid}
- HAR files are stored with the captures, not in this file. Do not attach them to a public ticket.

## Not tested
Single-user, single-browser measurements. This says nothing about behaviour under load, other browsers, or other data.

## Engineer verification
- [ ] Reproduce: run the journey's steps with DevTools open on the same build and see the same behaviour.
- [ ] The numbers are within the ranges above.
- [ ] It is not intended behaviour (for example polling or a deliberate repeat).
- [ ] Not already logged (search the tracker for the request path).
- [ ] Impact and severity are right for this journey; change them if not.
- [ ] Log it, and put the ticket id in the Logged as line.
"""


def slug(r):
    p = re.sub(r"[^a-z0-9]+", "-", urllib.parse.urlsplit(r["url"]).path.lower()).strip("-") or "root"
    return f"{r['type']}-{p}"[:60]


def check(d):
    bad = []
    files = sorted(glob.glob(os.path.join(d, "BUG-*.md")))
    for f in files:
        t = open(f, encoding="utf-8").read()
        if PLACEHOLDER in t:
            bad.append(f"{os.path.basename(f)}: Impact or Proposed severity is still a placeholder")
        for sec in SECTIONS:
            if sec not in t:
                bad.append(f"{os.path.basename(f)}: missing section '{sec}'")
    if not files:
        bad.append("no drafts found")
    return bad


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("rollup", nargs="?")
    ap.add_argument("--out", default="bugs")
    ap.add_argument("--env", default="(environment not stated)")
    ap.add_argument("--build", default="(build not stated)")
    ap.add_argument("--cache")
    ap.add_argument("--thresholds")
    ap.add_argument("--check")
    a = ap.parse_args()
    if a.check:
        problems = check(a.check)
        print("\n".join(problems) if problems else "OK: every draft is complete")
        sys.exit(1 if problems else 0)
    rows = group(json.load(open(a.rollup, encoding="utf-8")))
    os.makedirs(a.out, exist_ok=True)
    index = ["# Bug drafts for review\n", "Each file is a draft for an engineer to verify and log. Nothing here has been filed.\n",
             "| Draft | Problem | Journeys | Logged as |", "|---|---|---|---|"]
    for i, rs in enumerate(rows, 1):
        name = f"BUG-{i:02d}-{slug(rs[0])}.md"
        text = draft(i, rs, a)
        open(os.path.join(a.out, name), "w", encoding="utf-8").write(text)
        index.append(f"| [{name}]({name}) | {text.splitlines()[0].split(': ', 1)[1]} | "
                     f"{', '.join(sorted({j for r in rs for j in r['journeys']}))} | |")
    open(os.path.join(a.out, "INDEX.md"), "w", encoding="utf-8").write("\n".join(index) + "\n")
    print(f"wrote {len(rows)} draft(s) to {a.out}; fill Impact and Proposed severity in each, then run --check")
