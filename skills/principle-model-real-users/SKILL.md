---
name: principle-model-real-users
description: Use when designing a load test workload. Base the transaction mix, think time, pacing, and arrival pattern on real usage, not on what is easy to script.
---

# model-real-users

A load test is only as realistic as its model of users.

- Derive the transaction mix, peak rate, and concurrency from production analytics, logs, or business forecasts.
- Include think time and pacing. Without them, a closed model produces unrealistic request rates and unrealistic queues.
- Choose open (arrival rate) or closed (fixed users) deliberately, and say why.
- Use realistic data variety so caches and indexes behave as in production, and state any gap between test and production usage.
