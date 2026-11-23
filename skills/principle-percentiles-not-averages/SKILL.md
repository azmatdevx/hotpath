---
name: principle-percentiles-not-averages
description: Use when summarising response times. Report percentiles and distribution per transaction instead of a single average.
---

# percentiles-not-averages

Averages hide the experience of the slowest users.

- Report p50, p90, p95, and p99 per transaction, with the sample count.
- Look at the shape: bimodal curves, long tails, and periodic spikes each point to a different cause.
- Do not average percentiles across transactions or time windows. Recompute from raw samples.
- Report latency for successful requests separately from the error rate, since fast failures flatter the numbers.
