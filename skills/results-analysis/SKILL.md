---
name: results-analysis
description: Use when analysing load test results from any tool (JMeter, k6, Locust, Gatling, etc.). Computes percentiles per transaction from raw samples over the steady-state window, triages errors, reads throughput against response time and concurrency, finds where the system degrades, and forms a bottleneck hypothesis backed by server-side evidence.
---

# Results analysis

Goal: turn raw load test data into findings you can defend, with the limiter named and the evidence attached.

Run `results-sanity-check` first, or alongside this. This skill assumes the run itself is trustworthy.

## When to use

- A load run has finished and you need to know what it showed.
- You are comparing two runs (baseline versus change, or build versus build).
- You are asked where the system breaks or what limits it.

## Steps

### 1. Collect raw data
Gather the raw per-request samples, not only the tool's summary. Typical sources:
- JMeter: the results file (`.jtl` or CSV) from `-l`
- k6: `--out json=...` or `--out csv=...`
- Locust: `--csv` request history and failures
- Gatling: `simulation.log`
Also gather monitoring data (CPU, memory, DB, pools, GC, queues) covering the same time window, and the run configuration.

### 2. Define the measurement window
Mark ramp-up, steady state, and ramp-down. Compute headline numbers from steady state only. Keep the full timeline for the degradation analysis.

### 3. Compute the distribution from raw samples
Per transaction, over the steady-state window:
- sample count, throughput, error rate
- p50, p90, p95, p99, and max, plus min
- successful requests and failed requests separately

Never average percentiles across transactions or time buckets. Recompute from raw samples. A small example for tabular results (adjust column names to the tool):

```python
import pandas as pd

df = pd.read_csv("results.csv")           # e.g. JMeter CSV: timeStamp, elapsed, label, success
start = df.timeStamp.min() + 120_000      # skip first 2 minutes of ramp-up (ms)
end = df.timeStamp.max() - 60_000         # skip last minute of ramp-down
w = df[(df.timeStamp >= start) & (df.timeStamp <= end)]

ok = w[w.success.astype(str).str.lower() == "true"]
summary = ok.groupby("label").elapsed.describe(percentiles=[.5, .9, .95, .99])
errors = w.groupby("label").success.apply(lambda s: (s.astype(str).str.lower() != "true").mean())
print(summary, errors, sep="\n\n")
```

### 4. Triage errors
Group failures by transaction, status or exception, and time. Ask:
- Did errors start at a particular load or time?
- Are they timeouts, rejections, assertion failures, or connection errors?
- Do they cluster on one transaction or dependency?
Errors that appear as load rises usually point to a limit being hit.

### 5. Read the curves
Plot over time, on a shared time axis:
- active users or arrival rate
- throughput
- response time percentiles
- error rate
Look for the **knee**: the load level where throughput stops rising and latency climbs. That is the effective capacity. Throughput that falls while load rises means the system is past saturation.

### 6. Check consistency with Little's Law
For a closed model, concurrent users should be about throughput × (response time + think time). If the numbers disagree strongly, the data, the window, or the think time is wrong.

### 7. Find the limiter
Align server-side monitoring with the timeline at the knee and at any spikes:
- CPU or memory saturation on application, database, or other tiers
- connection pool exhaustion, thread pool queues, lock waits
- GC pauses or memory growth
- slow queries (see `sql-plan-analysis`), slow downstream calls, network limits
State the limiter as a hypothesis with its evidence. If you cannot find one, say what evidence is missing and how to get it (for example profiling, tracing, or a targeted rerun).

### 8. Compare runs, if relevant
- Same workload, data, environment, and build except the one thing under test (`principle-one-variable-at-a-time`).
- Compare medians and ranges across repeated runs. A difference inside run-to-run variation is no measurable difference.

### 9. Report the findings
For each finding give: the number with unit and percentile, the load level, the run count and range, the SLA it is measured against, and the limiter with evidence. Lead with the verdict. Hand the write-up to `test-report`.

## Pitfalls to avoid
- Reporting averages, or averaging percentiles.
- Including ramp-up and ramp-down in the headline numbers.
- Mixing failed and successful requests in one latency figure.
- Reading the tool's summary without checking the raw data.
- Naming a bottleneck with no server-side evidence.
- Comparing runs where more than one thing changed.
- Ignoring that a closed model hides overload by slowing the arrival rate.

## Done when
- Each headline number comes from steady-state raw samples, per transaction, with percentiles.
- Errors are categorised and tied to a time or load level.
- The knee or the absence of one is stated, with the curves behind it.
- The limiter is named with server-side evidence, or the evidence gap is stated.
