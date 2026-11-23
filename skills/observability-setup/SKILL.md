---
name: observability-setup
description: Use before a load test to make sure the right metrics, traces, and logs are collected on every tier at a useful resolution, with test runs annotated and correlatable. Tool-agnostic across APM and monitoring platforms (Prometheus and Grafana, Datadog, New Relic, Dynatrace, CloudWatch, Azure Monitor, and others).
---

# Observability setup for performance tests

Goal: when a result looks bad, the data to explain it already exists, lined up on one timeline.

A result you cannot explain is only a hypothesis (see `principle-explain-the-number`). This skill makes sure the evidence is collected before the run, not wished for after it.

## When to use

- Planning a load test and deciding what to monitor.
- A past run could not be explained because data was missing or too coarse.
- Introducing tracing or an APM agent on a system under test.

## Steps

### 1. Choose a framework for coverage
Use the same questions on every tier:
- **Resources (USE):** utilisation, saturation, and errors for CPU, memory, disk, and network.
- **Services (RED):** request rate, error rate, and duration for each service and endpoint.
Cover each tier: load generators, load balancer, application instances, caches, message queues, databases, and downstream dependencies.

### 2. List what to collect per tier
- **Application:** request latency by endpoint, throughput, errors, thread and connection pool usage, queue depths, GC pauses and heap use (for managed runtimes).
- **Database:** active sessions and waits, slow queries, connection counts, lock waits, cache hit ratio, replication lag.
- **Infrastructure:** CPU (including steal and throttling in containers), memory, disk I/O and latency, network throughput and errors.
- **Load generators:** CPU, memory, network, and the generator's own error counts (see `results-sanity-check`).
- **Dependencies:** latency and error rate of calls to downstream or third-party services.

### 3. Check resolution
Default metric resolution (often 30 to 60 seconds) hides short spikes. Set a finer scrape or collection interval for the test window (for example 1 to 10 seconds), and note its storage cost. State the resolution when you report.

### 4. Make runs correlatable
- Synchronise clocks on all machines (NTP).
- Tag load test traffic with a run ID header or attribute (for example `X-Test-Run-Id`), so traces and logs can be filtered to the test.
- Annotate the monitoring timeline with test start, stop, and each ramp step.
- Use the same timezone in every tool.

### 5. Decide on tracing and APM overhead
- Measure the overhead of the agent or tracing before relying on results. Compare a run with and without it if the overhead matters.
- Choose a sampling rate deliberately. Full tracing gives more evidence and more overhead. Head-based sampling can drop the slow requests you care about, so consider keeping slow and error traces.
- Keep the same agent configuration between runs you compare.

### 6. Build a run dashboard
Create one dashboard for the test with: load level, throughput, latency percentiles, error rate, resource use per tier, pool and queue depths, GC, and database waits, all on the same time axis. Save it as code or a link in the run record.

### 7. Capture a baseline and test the setup
Record an idle baseline and a small smoke run. Confirm every expected metric appears, timestamps align, and annotations show. Fix gaps now.

### 8. Preserve the data
Export or snapshot the metrics, traces, and logs for each run, since retention windows expire. Store them with the run record (see `load-run-checklist`). Remove secrets and customer data from logs before sharing.

## Pitfalls to avoid
- Discovering missing metrics after the run.
- Coarse resolution that averages away the spike.
- Clocks out of sync, so tiers cannot be lined up.
- An APM agent whose overhead changes the result, unmeasured.
- Sampling that drops the slow requests.
- Monitoring the system under test but not the load generators.
- Letting retention delete the evidence before the report is written.

## Done when
- Every tier has the metrics it needs at a useful resolution.
- Runs are tagged and annotated, and clocks are synchronised.
- A dashboard shows all key signals on one timeline, and a smoke run confirmed it.
- Data from each run is exported and stored with the run record.
