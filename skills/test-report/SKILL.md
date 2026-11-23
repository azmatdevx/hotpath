---
name: test-report
description: Use when writing up a performance test result for stakeholders. Produces a report that leads with a verdict and a headline number against the SLA, then objectives, method, findings with evidence, the limiter, risks and limitations, and recommendations.
---

# Test report

Goal: a report a stakeholder can act on in two minutes, with the evidence behind it for anyone who checks.

Run `results-sanity-check` and `results-analysis` before writing. Every number in the report must come from data that passed those checks, or be marked with the check that failed.

## When to use

- A load test or performance investigation has finished and the result must be communicated.
- A release decision depends on the result.
- A baseline or regression comparison needs to be recorded.

## Steps

### 1. Know the reader
Identify who will read it and what they will decide: release approval, capacity spend, or a fix priority. Write the top of the report for that decision and put the detail below it.

### 2. Lead with the verdict
The first lines say: pass, fail, no measurable difference, or inconclusive, and the one headline number against its SLA. Example: "Fail: checkout p95 is 3.4 s at 500 concurrent users against a 2 s SLA, limited by the database connection pool."

### 3. State objective and scope
One short section: the question the test answered, the journeys covered, the load levels, and what was out of scope.

### 4. Describe the method briefly
Workload model (mix, peak rate, concurrency, think time), test types run, tool and version, environment and how it differs from production, test data, and the run configuration. Enough to repeat the test, no more.

### 5. Show results against the SLAs
A table per transaction: SLA, measured p50, p90, p95, p99, throughput, error rate, and a pass or fail mark. Use steady-state numbers only. Add run count and range where runs were repeated.

### 6. Present findings with evidence
For each finding: what happened, at what load, the supporting chart or number, and the cause or the leading hypothesis. Useful visuals:
- throughput and response time against load on one time axis
- percentile table per transaction
- error rate over time
- server-side resource charts at the knee
Name the limiter and the evidence (see `principle-explain-the-number`). If the cause is unknown, say so and list what evidence would settle it.

### 7. Be explicit about limits
List the caveats: environment differences, mocked dependencies, data limits, unrepeated runs, and any sanity check that failed or was not done. Do not bury these in an appendix.

### 8. Recommend
Give concrete, prioritised actions with an expected effect and an owner or area: fixes, configuration changes, further tests, and the retest plan. Separate what the data proves from what is judgement.

### 9. Check the write-up
- Every number matches the raw data.
- The verdict matches what the checks support.
- No secrets, internal hostnames, or customer data are included if the report will be shared beyond the team.

## Report template

```
# <System>: performance test report

Verdict: <pass | fail | no measurable difference | inconclusive>
Headline: <metric, percentile, load, vs SLA, limiter>

## Objective and scope
## Method (workload, tool, environment, data)
## Results against SLAs (table)
## Findings (evidence per finding, limiter)
## Limitations and open questions
## Recommendations (prioritised)
## Appendix (raw runs, configs, charts)
```

## Pitfalls to avoid
- Burying the verdict at the end.
- Reporting averages or a single number for the whole system.
- Presenting results as production capacity when the environment is smaller or different.
- Listing observations with no cause, owner, or recommendation.
- Hiding failed or skipped checks.
- Charts without units, time axis, or load level.

## Done when
- The report starts with a verdict and a headline number against the SLA.
- Each finding has evidence, and the limiter is named or the gap is stated.
- Limitations are visible in the body of the report.
- Recommendations are specific and prioritised.
