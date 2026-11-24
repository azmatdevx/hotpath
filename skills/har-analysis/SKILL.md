---
name: har-analysis
description: Use when you have a HAR file (or several) from a browser session of a user journey and need to find performance problems in it - slow APIs, duplicate calls, large payloads, uncompressed or uncacheable static files, redirect chains, N+1 call patterns, failed requests. Runs a deterministic analyzer, then separates real problems from expected behaviour.
---

# HAR analysis

Goal: turn a HAR capture into a short, evidence-backed list of candidate performance problems, without eyeballing DevTools.

The detection is a script, so two people (or two agents) get the same findings from the same file. Judgement comes after: deciding which findings are real.

`<skill-dir>` below is the folder that contains this SKILL.md (the scripts live in its `scripts/` folder), and `<skills-dir>` is its parent, where the sibling skills sit. Use the real path your agent loaded this skill from; do not assume the current directory is the hotpath checkout.

## When to use

- A HAR was captured while walking through a user journey, manually or by a script.
- You are reviewing an app's pages and APIs for performance bugs before any load test.
- You need the same checks applied to many journeys in the same way.

## Steps

### 1. Check the capture first
A bad capture gives confident wrong findings. Before analysing, confirm:

- The journey reached its end state (the final page or confirmation is in the HAR). A capture that stopped at an error page is not a capture of the journey.
- Cache state is known: cold (cleared cache, first visit) or warm (repeat visit). Say which in your notes; the findings differ.
- Response bodies were recorded (`content.size` is non-zero for responses that had one). If every size is 0, the analyzer cannot judge payloads.
- It contains one user's session only.

Treat the HAR as sensitive. It holds cookies, tokens, and personal data. Do not commit it, paste it into a bug, or attach it anywhere public. Store it with the test artifacts and redact before sharing.

### 2. Run the analyzer
```
python3 <skill-dir>/scripts/analyze_har.py capture.har
```
Thresholds are flags: `--slow-ms` (default 1000), `--big-kb` for API and document responses (default 500), `--static-kb` for script, stylesheet, image, and font (default 300). Add `--json` for machine-readable output. Use the thresholds your team has agreed; keep the defaults only if none exist, and say so in the report.

The script needs only Python 3 and masks query values for names that look like secrets in its output.

### 3. Capture again and compare
Run the journey at least three times and analyse each HAR. A finding that appears in every run is a candidate bug. One that appears once is noise until shown otherwise (a slow first call, a cold server, a network blip). Report the range across runs for timings, not a single value.

```
python3 <skill-dir>/scripts/compare_runs.py --journey tc-01-cold --json tc-01-cold.json captures/tc-01-*-cold-run*.har
```
This splits findings into consistent (in every run) and intermittent, gives the range of each number across runs, and refuses a HAR whose run record says the journey did not verify. The `--json` output is what `sweep-rollup` reads.

### 4. Read each finding as a hypothesis
The script flags patterns. Decide for each one:

| Finding | What it means | Check before calling it a bug |
|---|---|---|
| `slow-request` | Total time over the threshold. The detail splits server wait from download. | Server wait dominant: backend or database. Download dominant: payload size or network. Repeat in the other runs. |
| `duplicate-concurrent` | The same request fired more than once within half a second. | Usually a real bug (two components fetching the same data). Check that it is not a retry after failure. |
| `duplicate` | The same request repeated later in the journey. | May be legitimate (refresh after an update). Real if the data cannot have changed in between. |
| `polling` | Regular repeated calls. | Not a bug by itself. Raise it only if the interval is aggressive or it keeps running after the user left the page. |
| `n-plus-one` | Many calls to one path template, one per id. | Real if a batch or list endpoint could replace them. |
| `large-payload` | Response over the threshold. | Compare wire size and decoded size. Ask whether the page uses all of it (long lists, unused fields, full-size images). |
| `uncompressed` | Text over 1 KB with no `content-encoding`. | Real unless the response is already tiny or was compressed by a proxy that the HAR bypassed. |
| `not-cacheable` | A static file over 10 KB with missing, `no-store`, or `max-age=0` cache headers. | Real for versioned or fingerprinted assets. Fine for genuinely dynamic files. |
| `redirect` | A redirect chain or a redirected API call. | Real if the client could request the final URL directly. |
| `failed-request` | Status 400 or above, or no response. | A failed call on the happy path is a functional bug. Log it, and note it may also distort timings. |

Anything the analyzer did not flag is not proven fine. Common gaps: slow rendering that is not network time, large DOM, long JavaScript tasks, and anything only visible under load.

### 5. Hand off
Pass the confirmed findings to `perf-bug-writing`. Keep the analyzer output and the run-to-run ranges; the bug needs both.

## Pitfalls to avoid
- Reporting a finding from a single run.
- Reading a single-user timing as capacity. A 900 ms call in one session says nothing about 500 users.
- Logging polling or intentional repeats as duplicate-call bugs.
- Judging payload size from `bodySize` alone; compare it with the decoded size.
- Analysing a capture that did not complete the journey.
- Committing or sharing the HAR.

## Done when
- The capture was checked for completion, cache state, and recorded bodies.
- At least three runs were analysed, and each reported finding appears in all of them or is marked as one-off.
- Every finding is classed real, expected, or unproven, with the reason.
- The analyzer's thresholds are stated.

## Checking the analyzer
`python3 <skill-dir>/scripts/selftest.py` builds a synthetic HAR with planted problems and clean controls and confirms the analyzer reports exactly those. It uses a synthetic file, so also run the analyzer on a real capture from your browser or tool and look at the result before trusting it.
