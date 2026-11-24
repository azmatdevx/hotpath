---
name: sweep-rollup
description: Use after several user journeys have each been captured and analysed, to merge their findings into one de-duplicated list of problems to log, so the same slow API or large asset seen in many journeys becomes one bug listing every affected journey.
---

# Sweep rollup

Goal: one row per real problem across the whole set of journeys, with the journeys it affects and the evidence range, ready for `perf-bug-writing`.

## Steps

### 1. Check every journey is in
List the journeys you set out to cover and compare with the analysed ones. A journey that failed to capture, or whose runs did not verify, is not "clean"; it is missing. Report it as missing.

### 2. Roll up
Each journey has a JSON file from `har-analysis` (`compare_runs.py --json`). Run:
```
python3 skills/sweep-rollup/scripts/rollup.py tc-01-cold.json tc-02-cold.json ...
```
By default it keeps only findings seen in every run of a journey and lists the intermittent ones' counts at the bottom. Pass `--include-intermittent` only to inspect them; do not log them as bugs without more runs.

### 3. Group by cause, not only by request
The script merges identical request-and-problem pairs. Then look for causes it cannot see:

- Several URLs of the same service slow together: one backend problem, probably one bug.
- The same script or image large on many pages: one bug on the asset.
- Different ids behind one path template (the N+1 case) from different journeys: one bug.

Merge by cause where the evidence supports it, and keep a note of why.

### 4. Rank
Rank by impact: how many journeys it touches, how common those journeys are, and the severity rubric in `perf-bug-writing`. A problem in one rare journey ranks below a smaller one on every journey.

### 5. Hand off
Give each ranked row to `perf-bug-writing`. Include the list of missing journeys and the cache state and build the sweep ran against.

## Pitfalls to avoid
- Treating a missing journey as having no findings.
- Mixing cold and warm results in one rollup without saying so.
- Logging one bug per journey for a shared cause.
- Logging intermittent findings from only a few runs.
- Ranking by how large a number looks instead of by impact.

## Done when
- Every planned journey is accounted for as analysed or missing, with the reason.
- Each problem appears once, with all affected journeys listed.
- The rollup states the cache state and build.
