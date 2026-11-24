---
name: perf-bug-writing
description: Use when turning confirmed performance findings (from a HAR analysis, a profile, or a test run) into bug reports for a tracker. Gives a template, a severity rubric, evidence rules, and de-duplication so the same problem is logged once with the journeys it affects.
---

# Performance bug writing

Goal: each bug is reproducible by someone who was not there, states a number with its context, and is logged once.

This skill is tracker-neutral. It produces text; paste it into Jira, GitHub, or whatever you use.

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

### 3. Write it
Use this shape:

```
Title: <what is wrong> on <request or asset>, <the number>
        e.g. "GET /api/orders takes 2.4-2.8 s in the Checkout journey"

Where:  journey / test case, step, environment and build, cache state (cold or warm)
Seen:   the measurement, with the range across runs (n runs)
        e.g. server wait 2.3-2.7 s of 2.4-2.8 s total, 3 runs, cold cache
Expected: the threshold or the reason it is a problem
        e.g. "agreed API budget 1 s" or "same data is fetched twice 50 ms apart"
Impact: what the user waits for, and how often the journey hits it
Evidence: request URL (secrets masked), timings, sizes, analyzer line, HAR file name and where it is stored
Suspected cause: only if the evidence shows one, labelled as a suspicion
Affects: other journeys, if any
Not tested: what this single-user capture cannot say (behaviour under load, other browsers, other data)
```

Rules for the content:
- Put the number and its unit in the title.
- Quote ranges across runs, not a single best or worst value.
- Mask tokens, session ids, and personal data in everything pasted. Attach the HAR only to a restricted location, never in public text.
- Describe what you saw. Put a guess about the cause in its own labelled line.
- Do not prescribe a fix unless the cause is shown.

### 4. Set severity with the rubric
Severity comes from impact on the journey, not from how large the number looks. Adjust the thresholds to your team's, and write them in the bug.

| Severity | Typical signs |
|---|---|
| High | The journey step is slow enough that users give up or time out (for example a main action over 3 s), or a failed call on the happy path, or a defect that multiplies load (N+1 over dozens of calls). |
| Medium | A noticeable wait on a common step, a duplicate call on every visit, or a payload several times larger than the page uses. |
| Low | Missing compression or caching on small or rarely used assets, a one-off redirect, polling that is only slightly frequent. |

If you are unsure between two levels, take the lower and say why. Never raise severity because a finding is interesting.

### 5. Review before filing
Read each bug as the developer who gets it. Can they find the request, repeat the steps, and see what "fixed" looks like? If not, add that.

## Pitfalls to avoid
- Titles with no number or no request ("Slow page").
- One bug per journey for the same root cause.
- A bug from a single run.
- HAR files, tokens, or personal data pasted into the ticket.
- A cause stated as fact when it was a guess.
- Treating a single-user timing as a capacity claim.

## Done when
- Each bug passes step 1 and is not a duplicate.
- Each bug states the number, the range, the runs, and the cache state.
- Severity is set from the rubric, with the thresholds used.
- Nothing sensitive is in the text.
