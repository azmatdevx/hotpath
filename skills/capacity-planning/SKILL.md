---
name: capacity-planning
description: Use when sizing infrastructure or answering "how much capacity do we need" from load test evidence. Covers demand forecasting, per-unit capacity at the SLA, headroom policy, redundancy, scaling-behaviour checks, shared-bottleneck limits such as database connections, and validating the plan.
---

# Capacity planning

Goal: a defensible answer to "how many instances (or how much of each resource) do we need to meet the SLA at forecast demand", with the assumptions written down.

Use load test evidence, not guesses (see `results-analysis` and `principle-explain-the-number`).

## When to use

- Sizing a new service, or planning for growth or a known event.
- Deciding whether to scale up, scale out, or optimise.
- Reviewing an autoscaling policy or a cost target.

## Steps

### 1. Forecast demand
State the peak load the system must serve, with units (requests per second per transaction type, concurrent users, jobs per hour). Include growth over the planning period, seasonality, and known events, and say where the numbers came from. Keep the transaction mix (see `load-test-design`).

### 2. Measure capacity per unit at the SLA
From load tests, find the load one instance (or one unit of the scaling dimension) sustains while meeting the SLA percentiles and error budget. This is the capacity at the **knee**, not the maximum before failure. Record the configuration, instance size, and conditions.

### 3. Set a headroom policy
Do not plan to run at the knee. Choose a target utilisation at peak that leaves room for variance, failures, and growth between reviews, and write the rationale. A value around 60 to 70 percent is a common starting point, but agree it for your system.

### 4. Add redundancy
Add capacity so the service still meets the SLA when an instance, node, or zone is lost (for example N+1, or enough to survive a zone failure). Check that load rebalancing after a failure is itself within capacity.

### 5. Calculate and show the working
Worked example:
- Peak demand: 1,200 requests per second.
- Per-instance capacity at SLA: 150 requests per second.
- Target utilisation: 70 percent, so planned load per instance is 105 requests per second.
- Instances for peak: 1,200 / 105 = 11.4, rounded up to 12.
- Add redundancy for one lost instance: 13.

### 6. Check shared and downstream limits
Capacity rarely scales linearly forever. Check what does not scale with instance count:
- **Database:** connections, CPU, IOPS, lock contention. Example by Little's Law: 1,200 requests per second × 2 queries each × 10 ms per query is about 24 connections in use on average, before headroom and bursts.
- **Caches, queues, and third-party rate limits.**
- **Network and load balancer limits.**
Run a scaling test (for example 1, 2, 4 instances) to see whether throughput scales near-linearly. A flat curve means a shared bottleneck.

### 7. Review autoscaling
If autoscaling is used, check the metric, thresholds, scale-up delay, and minimum size against the demand shape. A policy that reacts after saturation, or scales too slowly for a spike, does not provide the capacity you planned. Test it with a spike test.

### 8. Validate the plan
Run a load test at the planned capacity and forecast peak. Confirm the SLA holds, utilisation is near the target, and failure of one unit still meets the SLA (see `load-test-design`).

### 9. Record assumptions and the review date
Write down demand assumptions, per-unit capacity and its test evidence, the headroom and redundancy policy, known limits, and when to re-check (after major releases, at forecast milestones, or on a schedule).

## Pitfalls to avoid
- Using the maximum throughput instead of throughput at the SLA.
- Planning to run at 100 percent of the knee.
- Assuming linear scaling without testing it.
- Forgetting the database, cache, or third-party limits.
- A forecast with no source, or one that ignores the transaction mix.
- Sizing on a test environment that does not match production, with no adjustment stated.

## Done when
- Demand, per-unit capacity at the SLA, headroom, and redundancy are stated with sources.
- The calculation is shown, and shared limits are checked.
- A validation test at planned capacity met the SLA.
- Assumptions and a review date are recorded.
