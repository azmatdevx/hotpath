# Playbook: results to report

Goal: turn completed load test results into a verified finding that a stakeholder can act on.

## Steps

1. **Gather artifacts.** Collect raw results (not just summaries), the test plan or script version, run configuration, environment notes, and monitoring data covering the same time window.
2. **State the claim.** Write the headline you expect to report, with its metric, percentile, load level, and SLA.
3. **Vet the data.** Run `results-sanity-check`. Fix or record every failed check before continuing.
4. **Analyse.** Run `results-analysis`: percentiles per transaction (`principle-percentiles-not-averages`), steady-state window only, error triage, throughput against response time, and where latency starts to rise.
5. **Explain the number.** Apply `principle-explain-the-number`: line up server-side monitoring with the timeline and name the limiter. If you cannot, say so and list what evidence is missing.
6. **Write the report.** Run `test-report`: objectives, method, findings against the SLAs, evidence, risks, and recommendations. Lead with the verdict.
7. **Check the write-up.** Every number matches the raw data. Caveats from failed checks appear in the report, not only in notes.

## Done when

- The report leads with a verdict and a headline number measured against the SLA.
- The limiter is named with evidence, or the gap is stated.
- Failed or unchecked sanity checks are visible in the report.
