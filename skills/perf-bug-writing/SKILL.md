---
name: perf-bug-writing
description: Use when turning confirmed performance findings (from a HAR analysis, a profile, or a test run) into bug reports for a tracker. Gives a template, a severity rubric, evidence rules, and de-duplication so the same problem is logged once with the journeys it affects.
---

# Performance bug writing

Goal: each bug is reproducible by someone who was not there, states a number with its context, and is logged once.

This skill is tracker-neutral. It produces markdown drafts, one file per bug, for an engineer to verify and log. The agent never files anything: the workflow is at a stage where a person checks every bug first.

## Steps

### 1. Check the finding is ready
Do not write a bug from an unconfirmed finding. It needs:

- the same result in at least three runs, with the range
- the journey, step, and cache state it occurred in
- a reason it counts as a problem (an agreed threshold, a duplicate with no purpose, a payload the page does not use)

If any are missing, go back to `har-analysis`.

### 2. De-duplicate before writing
Search the tracker (or your list of bugs for this exercise) for the same request path, asset, or root cause. One problem seen in many journeys is one bug.

- If it exists, add the new journey and evidence as a comment. Do not open a second bug.
- If several findings share a cause (one slow API, many pages), write one bug and list the affected journeys.
- If one request has several problems (large, uncompressed, and uncached), write one bug unless different teams fix them.

### 3. Generate the drafts
Run the sweep rollup with `--json`, then:
```
python3 skills/perf-bug-writing/scripts/draft_bugs.py roll.json --out bugs/ --env <base URL> --build <build> --cache <cold|warm> --thresholds "<the ones used>"
```
It writes `BUG-NN-<slug>.md` per request, plus `INDEX.md`. Several problems on one request are one draft. The evidence (request, ranges across runs, analyzer lines, capture file names) is copied as the analyzer produced it; do not retype numbers.

Each draft follows this shape, which you can use for a bug found some other way:

```
Title: <what is wrong> on <request or asset>, <the number>
Where:  journey / test case, environment and build, cache state
Seen:   the measurement, with the range across runs (n runs)
Expected: the threshold or the reason it is a problem
Impact: what the user waits for, and how often the journey hits it
Evidence: request URL (secrets masked), timings, sizes, analyzer line, where the capture is stored
Suspected cause: only if the evidence shows one, labelled as a suspicion
Not tested: what this single-user capture cannot say
Engineer verification: a checklist for the person who logs it
```

### 4. Fill in what only judgement can supply
Two lines are left as `(agent: fill in)`: **Impact** and **Proposed severity**. Fill them from the journey and the rubric below. If you have a suspicion about the cause, add a clearly labelled "Suspected cause" line. Do not prescribe a fix unless the cause is shown.

Rules for the content:
- Put the number and its unit in the title, and quote ranges across runs, not a single best or worst value.
- Mask tokens, session ids, and personal data in everything you add. Capture files stay in the artifact store, never in public text.
- Describe what you saw. Keep a guess about the cause in its own labelled line.

Then run:
```
python3 skills/perf-bug-writing/scripts/draft_bugs.py --check bugs/
```
It fails while any draft still has a placeholder or a missing section, so an unfinished draft cannot be handed over.

### Severity rubric
Severity comes from impact on the journey, not from how large the number looks. Adjust the thresholds to your team's, and write them in the bug.

| Severity | Typical signs |
|---|---|
| High | The journey step is slow enough that users give up or time out (for example a main action over 3 s), or a failed call on the happy path, or a defect that multiplies load (N+1 over dozens of calls). |
| Medium | A noticeable wait on a common step, a duplicate call on every visit, or a payload several times larger than the page uses. |
| Low | Missing compression or caching on small or rarely used assets, a one-off redirect, polling that is only slightly frequent. |

If you are unsure between two levels, take the lower and say why. Never raise severity because a finding is interesting.

### 5. Hand over, do not file
Give the engineers the `bugs/` folder. Each draft is marked as not verified by a person and carries a checklist: reproduce in DevTools on the same build, confirm the numbers, rule out intended behaviour, search for duplicates, confirm impact and severity, then log it and record the ticket id in the file. The agent does not file, comment on, or close tickets.

Before handing over, read each draft as the engineer who gets it. Can they find the request, repeat the steps, and see what "fixed" looks like? If not, add that.

## Pitfalls to avoid
- Titles with no number or no request ("Slow page").
- One bug per journey for the same root cause.
- A bug from a single run.
- HAR files, tokens, or personal data pasted into the ticket.
- A cause stated as fact when it was a guess.
- Treating a single-user timing as a capacity claim.

## Done when
- Each bug passes step 1 and is not a duplicate.
- Each draft states the number, the range, the runs, and the cache state.
- Impact and proposed severity are filled in from the rubric, with the thresholds used, and `--check` passes.
- Nothing sensitive is in the text.
- Nothing was filed; an engineer verifies and logs each draft.
