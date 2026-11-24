# Playbook: analyse a test run

You own a verified finding that a stakeholder can act on, from a completed load test run (usually the artifacts of a pipeline run). Gather, vet, analyse, explain, write. Every number in the report matches the raw data.

Use when: a load run has finished and its results need analysing and writing up, or someone brings results and asks what they mean.

## Inputs

- The run's raw results (not only summaries), for example the pipeline's artifacts: JTL, k6 output, Gatling logs.
- The script or plan version and the run configuration, and the pipeline run link or identifier.
- Monitoring and observability data covering the same window (read access to the platform, or exports), and database statistics if the database is suspected.
- The SLAs or the question the results are meant to answer.
- Where the data came from: environment, build, date.

## Steps

1. **Gather artifacts.** Collect raw results, the plan or script version, run configuration, environment notes, and monitoring data for the same window.
2. **State the claim.** Write the headline you expect to report, with its metric, percentile, load level, and SLA.
3. **Vet the data.** Run `results-sanity-check`. Fix or record every failed check before continuing.
4. **Analyse.** Run `results-analysis`, starting with `summarize_results.py` so you read a few dozen lines, not the raw file: percentiles per transaction (`principle-percentiles-not-averages`), the steady-state window only, drift between its halves, error triage, throughput against response time, and where latency starts to rise.
5. **Explain the number.** Apply `principle-explain-the-number`: run `observability-analysis` to export the run window from your monitoring platform and rank the series against the latency rise, then check the mechanism of the top candidates. Use `observability-setup` to know what should have been collected, `jvm-gc-analysis` for JVM services, and the `analyse-slow-sql` playbook when the database is the suspect. If you cannot name the limiter, say so and list the evidence that is missing.
6. **Write the report.** Run `test-report`: objectives, method, findings against the SLAs, evidence, risks, and recommendations. Lead with the verdict.
7. **Check the write-up.** Every number matches the raw data, and caveats from failed checks appear in the report, not only in notes.

## Verification

A pass is a report whose numbers come from the raw data, with the steady-state window and its drift checked, the limiter named with evidence (or the gap stated), and failed checks visible. Not a pass: a number taken from a summary that was never reconciled with the raw data, an average used for latency, or a window that was never checked for drift.

## Stop conditions

- A sanity check fails in a way that invalidates the run (generator saturated, iterations dropped, load not what was planned): report the run as inconclusive instead of analysing it.
- Raw data is missing and only summaries exist: say what that limits. Keep the data you read small: summaries from the scripts, never raw results, logs, or series pasted into the conversation.
- Monitoring does not cover the run's window: say that the limiter cannot be named.

## Delegation

The lead owns the claim, the vetting, and the verdict. A worker can compute percentiles or draft a report section from files you point to, but the lead re-checks every number it quotes against the raw data. Workers read `perf-mode/worker.md` first.

## Reply format

The verdict, the headline number with its range and SLA, the conditions, the limiter with evidence (or the gap), the failed and unrun checks, and what the results cannot say. Label each claim measured, inferred, or guess.

## Related playbooks

`design-a-load-test` (the plan the run belongs to), `analyse-slow-sql` (when the database is the suspect).

## Done when

- The report leads with a verdict and a headline number measured against the SLA.
- The limiter is named with evidence, or the gap is stated.
- Failed or unchecked sanity checks are visible in the report.
