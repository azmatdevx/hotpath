---
name: results-sanity-check
description: Use before reporting or acting on load test results. Vets a result against nine questions (generator limits, work actually done, errors, achieved load, steady state, environment and data, repeatability, distribution, and explanation) so a flattering or broken number is not shipped as a finding.
---

# Results sanity check

Use this after a load run and before you report a number, claim a pass or fail, or recommend a change. Answer each question with evidence from the run, not with a guess.

If the user wants a quick ballpark, one run is acceptable. Say that it is one run, and still check questions 2, 3, and 4.

## Before you start

- Write down the claim you expect to make in the words you would ship ("checkout p95 is 1.8 s at 500 concurrent users, within the 2 s SLA"). The questions test that sentence.
- Open the test plan or script and note what it times, what it asserts, and what it ignores.

## The questions

1. **Was the load generator the limiter?** Check CPU, memory, network, threads, and GC on the generator machines. If the generator saturated, you measured the generator. If it cannot generate the intended load, add generators or reduce per-generator load, then rerun. If generator metrics were not captured, mark this question unchecked, and note whether the generator and the system under test share a machine.
2. **Did the requests actually do the work?** Status 200 is not proof. Confirm content assertions passed: the expected element, ID, or payload came back, and it was not a login page, an error body, or an empty result. Check that writes landed in the system under test.
3. **What errors occurred?** Count and categorise them: timeouts, 4xx, 5xx, connection errors, assertion failures. Fast errors can lower average latency, so a run with errors can look better than a clean one. Report latency for successful requests separately from the error rate.
4. **Was the load what the design said?** Compare achieved throughput and concurrency with the target. Check whether the model is open (arrival rate) or closed (fixed users), and whether think time and pacing match the design. Under a closed model, a slow server lowers the arrival rate, which hides overload (coordinated omission). Check for dropped or skipped iterations that tools report under an open model (for example `dropped_iterations` in k6): they mean the offered load was below target. Find out whether too few pre-allocated users or generator load caused them.
5. **Is the measured window steady state?** Exclude ramp-up and ramp-down. Check that caches, connection pools, and JIT were warm, and that the run lasted long enough to see slow effects like memory growth or queue build-up.
6. **Is the environment and data representative?** Compare the test environment with production on hardware, configuration, data volume, and dependencies. Check test data: if every user hits the same IDs, you are measuring cache hits. Check that shared environments were not noisy during the run.
7. **Does it reproduce?** Repeat the run. Report the median and the range across runs. A difference smaller than run-to-run variation is no measurable difference.
8. **What does the distribution look like?** Report percentiles (p50, p90, p95, p99) per transaction, not a single average. Look for bimodal shapes, long tails, and periodic spikes. Check that the slowest transactions are not hidden inside an overall number.
9. **Can you explain the number?** Name the limiter using server-side evidence: CPU, memory, DB wait, connection pool exhaustion, GC pauses, queue depth, downstream latency. Line it up with monitoring on the same time axis. A result you cannot explain is a hypothesis, not a finding. Monitoring sampled less often than the system's own swings aligns with the load data only approximately, so state the sampling interval.

## Report

- Lead with the verdict: pass, fail, no measurable difference, or inconclusive.
- Give each number with its unit, the percentile, the run count, and the range. For example: "checkout p95 1.8 s, median of 3 runs, range 1.7 to 1.9 s, 0.2% errors, bounded by DB connection pool at 100 connections."
- Mark the result inconclusive when the generator saturated, work was not verified, the achieved load missed the target, or the limiter is unexplained. Name which check failed.
- Keep a stakeholder summary to one headline number against the SLA. Put the supporting evidence in an appendix or linked notes.

## Done when
- Each of the nine questions has an answer backed by evidence, or is explicitly marked as unchecked with the reason.
- The reported verdict matches what the checks support.
