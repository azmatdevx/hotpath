---
name: observability-analysis
description: Use after a load test run to find what limited it, from monitoring and APM data on any platform (Grafana and Prometheus, Datadog, New Relic, Dynatrace, Azure Monitor, CloudWatch, and others). Exports the run window as small series, ranks them against the latency rise, and checks the mechanism before naming a limiter.
---

# Observability analysis

Goal: name what limited the run (the tier, the resource, the queue) with evidence, not a guess, while keeping the data you read small.

This skill is platform-agnostic. How to export series and which queries to use on each platform is in `references/` (`grafana-prometheus.md`, `datadog.md`, `newrelic.md`, `dynatrace.md`, `azure-monitor.md`, `cloudwatch.md`). Read the file for the platform in use after reading this one. The platform references have not been run against real accounts; check the queries against your platform's current documentation.

`<skill-dir>` below is the folder containing this SKILL.md; the scripts are in its `scripts/` folder, and `<skills-dir>` is its parent.

## When to use

- A run showed latency rising, errors, or a throughput ceiling, and you need to know why (`principle-explain-the-number`).
- `results-analysis` found where latency starts to rise, and the next question is what saturated.
- You are comparing two runs and need to know which resource changed.

## Steps

### 1. Fix the window and the reference series
Take the run's start and end from the results, and the steady-state window from `results-analysis`. Make the reference series for the transaction that degraded, with timestamps in epoch seconds so they line up with the platform:

```
python3 <skills-dir>/results-analysis/scripts/summarize_results.py results.csv --series-csv ref.csv --series-bucket 10 --series-label '04_checkout'
```
Use one transaction, not the pooled series, unless the whole system degraded.

### 2. Decide what to export, by tier
Cover every tier with the same questions (see `observability-setup`): for each resource its utilisation, saturation, and errors; for each service its rate, errors, and duration. Typical series:
- **Application:** CPU and throttling, memory and heap, GC pause time, thread pool and connection pool in use and waiting, queue depth, request latency by endpoint.
- **Database:** active sessions, lock and I/O waits, connections, slow statements, cache hit ratio.
- **Infrastructure:** CPU (including steal and container throttling), disk latency and queue, network errors and retransmits.
- **Load generators:** CPU and network. A saturated generator makes every other series misleading.
- **Dependencies:** latency and errors of downstream calls.

### 3. Export the window as small series
Export each series for the run window plus a few minutes either side, at 15 seconds or finer, as a CSV with the time in the first column and the value in the last (the platform references show how). Use the maximum, not the average, where the platform rolls up, because averages hide the peaks that cause tail latency. Use one timezone, and check the platform's clock against the generator's.

Do not paste raw series or logs into your context. Work from the exports with the scripts, and read only the summary.

### 4. Rank the candidates
```
python3 <skill-dir>/scripts/rank_limiters.py ref.csv cpu.csv heap.csv db_active.csv pool_in_use.csv --ceiling cpu=100 --ceiling pool_in_use=50
```
Declare a ceiling for every series that has a capacity (a percentage at 100, a pool at its maximum): the script then reports how much of the window the series spent at it. It reports, for each series, the correlation with p95 latency at the best lag, the correlation with the request rate, the first and second half means, and a reading:
- **candidate limiter**: follows latency but not the load. Look here first.
- **saturated**: at its ceiling for half the window or more. Look here too, and at whatever queues behind it.
- **grows with load and with latency**: check whether it is saturating or simply scaling.
- **tracks load only** or **no clear relationship**: probably not the limiter.

### 5. Check the mechanism
Correlation ranks where to look; it is not proof. For the top candidates:
- Does it move before latency does (lag above zero)? A cause moves first.
- Is there a mechanism? A full pool means requests queue for a connection; a long GC pause stops every request; a CPU at its ceiling stretches service time. Say it in one sentence and check each link in the data.
- What is downstream of it? The limiter is usually the first saturated resource on the path, and the queue in front of it is the symptom.
- Can you rule out the generator, the network, and the dependency?
- If you can, change one thing (`principle-one-variable-at-a-time`) and run again.

### 6. State the limiter, and what is unproven
Write the limiter with the evidence (series, values, lag), the mechanism, and the alternatives you ruled out or could not. If the evidence is missing, say what to collect next. Hand the finding to `test-report`.

## Pitfalls to avoid
- Reading dashboard averages at one-minute resolution and missing the peaks.
- Calling the series with the highest correlation the cause. A metric that merely grows with load correlates with everything.
- Mixed timezones or clock skew between the platform and the generator.
- Forgetting the load generators' own resources.
- Pasting raw data into the conversation instead of summarising it with a script.
- Naming a limiter that no one can verify by changing it.

## Done when
- The reference series and every export cover the same window, in one timezone.
- The ranking was run with ceilings declared for series that have a capacity.
- The limiter is stated with its mechanism and evidence, or the missing evidence is listed.
- Alternatives (generator, network, dependency) are addressed.
