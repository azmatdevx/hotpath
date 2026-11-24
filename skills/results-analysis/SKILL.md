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

`<skill-dir>` is the folder containing this SKILL.md; the script is in its `scripts/` folder.

### 0. Summarise first
For k6 CSV, JMeter CSV results (JTL), or any CSV, let the script do the arithmetic, so you read about thirty lines instead of the raw file (which can be hundreds of megabytes):

```
python3 <skill-dir>/scripts/summarize_results.py results.csv --trim-start 60 --trim-end 15 --sla-p95 800 --json summary.json --series-csv ref.csv
```
It gives percentiles per transaction over the steady-state window, error rates, first-half versus second-half p95 and error rate (with a DRIFTING flag), a coarse time series, failing checks, and dropped iterations for k6. `--window START,END` sets the window explicitly; `--sla LABEL=MS` sets a limit per transaction; `--series-csv` writes a series for `observability-analysis`. It cannot tell whether the generator was saturated or the load matched the plan, so run `results-sanity-check` as well. The steps below say what to do with what it shows.

### 1. Collect raw data
Gather the raw per-request samples, not only the tool's summary. Typical sources:
- JMeter: the results file (`.jtl` or CSV) from `-l`
- k6: `--out json=...` or `--out csv=...`
- Locust: `--csv` request history and failures
- Gatling: `simulation.log`
Also gather monitoring data (CPU, memory, DB, pools, GC, queues) covering the same time window, and the run configuration.
Raw k6 CSV output has one row per metric sample (`metric_name`, `timestamp` in seconds, `metric_value`, `name`, `status`, `check`), so filter on `metric_name` (for example `http_req_duration`).

### 2. Define the measurement window
Mark ramp-up, steady state, and ramp-down. Compute headline numbers from steady state only, and check that the window really is steady by comparing its first and second halves. A queue or latency that is still rising means the window average understates the outcome. Keep the full timeline for the degradation analysis.

### 3. Compute the distribution from raw samples
Per transaction, over the steady-state window:
- sample count, throughput, error rate
- p50, p90, p95, p99, and max, plus min
- successful requests and failed requests separately

Never average percentiles across transactions or time buckets. Recompute from raw samples. If some responses skipped the work (fast empty results, cached or degraded replies), split latency by check outcome when the data allows, because mixed in they pull percentiles down. Splitting by a duration threshold is only a heuristic and misclassifies slow genuine responses, so where you can, record the outcome with each sample (a tag or a separate metric) and split on that. A small example using only the Python standard library (adjust column names to the tool; the example uses a JMeter-style CSV with `timeStamp` in milliseconds, `elapsed`, `label`, and `success`):

```python
import csv
from collections import defaultdict

def pct(v, p):
    v = sorted(v); k = (len(v) - 1) * p / 100; f = int(k); c = min(f + 1, len(v) - 1)
    return v[f] + (v[c] - v[f]) * (k - f)

rows = list(csv.DictReader(open("results.csv")))
ts = [int(r["timeStamp"]) for r in rows]
start, end = min(ts) + 120_000, max(ts) - 60_000      # skip 2 min ramp-up and 1 min ramp-down
by_label = defaultdict(list)
for r in rows:
    if start <= int(r["timeStamp"]) <= end and r["success"].lower() == "true":
        by_label[r["label"]].append(float(r["elapsed"]))
for label, v in sorted(by_label.items()):
    print(label, len(v), *(round(pct(v, p)) for p in (50, 90, 95, 99)))
```

If pandas is available, `groupby("label").elapsed.describe(percentiles=[.5, .9, .95, .99])` does the same.

### 4. Triage errors
Group failures by transaction, status or exception, and time. Ask:
- Did errors start at a particular load or time?
- Are they timeouts, rejections, assertion failures, or connection errors?
- Do they cluster on one transaction or dependency?
Errors that appear as load rises usually point to a limit being hit.
Include content-check failures, not only HTTP errors. A degraded system can return 200 with empty or fake results, so the HTTP error rate can read 0% while the work failed.

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
- Reporting a window average without checking it is flat. A rising queue near saturation can read as a pass on the average and fail by the end.
- Mixing failed and successful requests in one latency figure.
- Trusting a 0% HTTP error rate without checking content-check failures.
- Reading the tool's summary without checking the raw data.
- Naming a bottleneck with no server-side evidence.
- Comparing runs where more than one thing changed.
- Ignoring that a closed model hides overload by slowing the arrival rate.

## Done when
- Each headline number comes from steady-state raw samples, per transaction, with percentiles.
- Errors are categorised and tied to a time or load level.
- The knee or the absence of one is stated, with the curves behind it.
- The limiter is named with server-side evidence, or the evidence gap is stated.
