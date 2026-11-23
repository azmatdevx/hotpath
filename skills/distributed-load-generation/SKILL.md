---
name: distributed-load-generation
description: Use when one load generator cannot produce the target load, or load must come from several locations. Covers when to distribute, sizing a single generator, controller and worker topology, splitting data and workload, OS and network limits, verifying merged results, and cleanup, in any tool (JMeter, k6, Locust, Gatling).
---

# Distributed load generation

Goal: generate the intended load from multiple machines without the generators, the network, or the merging of results becoming the thing you measure.

This skill is tool-agnostic. Per-tool setup is in `references/` (`jmeter.md`, `k6.md`, `locust.md`, `gatling.md`). Read the file for the tool in use after reading this one.

## When to use

- A single generator saturates (CPU, memory, network, or file descriptors) before reaching the target load.
- Load must originate from different regions or networks.
- Load must come from many distinct source IPs.

## Steps

### 1. Confirm you need it
Distribution adds failure modes. First check whether tuning one generator is enough: headless mode, lean logging, efficient script code, and a larger machine. Distribute only when one generator cannot reach the target (see `results-sanity-check`, question 1).

### 2. Measure single-generator capacity
Run one generator against a known-fast target or the real system, and find the load at which its CPU, memory, or network approaches saturation. Plan the number of generators from that figure with spare capacity, and confirm by testing at the planned scale.

### 3. Choose the topology
- **Controller and workers:** one machine coordinates, workers generate load, and results flow back or are merged afterwards.
- **Independent instances:** run the same test on several machines and merge the results afterwards.
- **Managed or orchestrated:** a hosted service or a cluster operator starts and coordinates workers.
Choose based on your tool's support (see the reference) and your environment.

### 4. Divide the workload
Be explicit about how the total load maps to each generator. Some tools multiply the configured users by the number of workers, while others divide the total. Write down the arithmetic, and check the achieved total against the target during a small run.

### 5. Split the data
Give each generator its own slice of test data so two generators do not use the same rows (see `script-parameterization`). Make sure every generator has the files it needs.

### 6. Match versions and configuration
Use the same tool version, runtime, plugins, and script on every machine. Synchronise clocks (NTP), because result merging and monitoring correlation depend on it.

### 7. Check OS and network limits
Raise or verify, on each generator:
- open file descriptor limits
- ephemeral port range and port exhaustion (many connections from few source IPs to one target)
- connection reuse and DNS behaviour
- bandwidth to the target
Few source IPs can also skew load balancing (for example IP-hash or sticky routing), so use enough distinct sources when it matters.

### 8. Place generators sensibly
Put generators close to the target when you want to measure the system, and in real user locations when you want to measure user experience, and say which. A distant generator adds network latency to every measurement.

### 9. Control result volume
Do not stream every sample to a single controller if that becomes a bottleneck. Prefer aggregation on workers or post-run merging, and keep per-sample logging lean.

### 10. Verify merged results
Compare the merged totals with expectations: total requests, achieved throughput, error counts, and percentile calculation from raw samples (see `principle-percentiles-not-averages`). Do not average percentiles from workers.

### 11. Monitor and clean up
Monitor every generator during the run. Afterwards, stop workers, collect results, and shut down temporary machines to avoid cost.

## Pitfalls to avoid
- Distributing before checking whether one tuned generator would do.
- Counting users wrongly because the tool multiplies per worker.
- Two generators using the same data rows.
- Mixed tool or plugin versions.
- Running out of ephemeral ports or file descriptors.
- Merging percentiles by averaging.
- Leaving cloud generators running.

## Done when
- The need for distribution is justified by a measured single-generator limit.
- The total load maps to the workload design, and data is split.
- Generators share versions, clocks, and OS limits are verified.
- Merged results are verified, and generators are stopped and cleaned up.
