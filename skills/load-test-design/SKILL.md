---
name: load-test-design
description: Use when planning a load test, before any scripting. Defines the question, NFRs and SLAs with pass/fail criteria, the workload model (transaction mix, peak rate, concurrency, think time, open versus closed model), the test types needed, data and environment needs, and a monitoring and risk plan.
---

# Load test design

Goal: a test plan that answers a specific question, so the scripts, the run, and the report all aim at the same target.

This skill is tool-agnostic. Pair it with `principle-model-real-users`.

## When to use

- A new load test is being planned.
- A release, migration, or infrastructure change needs performance sign-off.
- An existing test no longer reflects how the system is used.

## Steps

### 1. State the question
Write one sentence for the decision the result informs: release gate, SLA check, capacity plan, regression check, or "where does it break". If you cannot state it, stop and ask.

### 2. Define NFRs and pass/fail criteria
Get measurable targets from stakeholders or existing SLAs. Cover:
- **Response time**: percentile and threshold per critical transaction (for example "checkout p95 under 2 s").
- **Throughput**: required rate at peak.
- **Error rate**: maximum acceptable (for example under 1%).
- **Resource limits**: CPU, memory, connection pool, queue depth ceilings.
- **Availability and recovery**, where relevant.
If no targets exist, propose them, mark them as assumptions, and get them confirmed. Pass/fail criteria must be written before the run.

### 3. Choose the journeys
List the user journeys and API flows by business criticality and frequency. Include the few that carry most of the load, and the ones that are costly or risky even if rare (search, report generation, batch submissions, checkout). Exclude flows you cannot make realistic, and say so.

### 4. Build the workload model
- **Transaction mix**: the share of each journey, from production analytics or logs where available, otherwise from business estimates.
- **Peak rate**: the busiest realistic period (for example peak hour), plus agreed headroom for growth.
- **Concurrency**: derive it, do not guess. Little's Law: concurrent users ≈ arrival rate × time in system (response time + think time). Example: 600 checkouts per hour is 0.167 per second, and a 3-minute journey (180 s) gives about 30 concurrent users in that journey.
- **Open or closed model**: use an open model (arrival rate) to test a system under demand it does not control, such as a public site. Use a closed model (fixed users) for a fixed population, such as an internal tool. State which and why. A closed model hides overload because slow responses reduce the arrival rate.
- **Think time and pacing**: from observed user behaviour, with variation, not a single constant.

### 5. Select test types
Choose only what answers the question:

| Type | Purpose |
|---|---|
| Smoke | Prove the script and environment work at minimal load. |
| Load | Confirm behaviour at expected peak. |
| Stress | Find behaviour beyond expected peak and how it fails. |
| Spike | Check response to sudden surges and recovery. |
| Soak (endurance) | Find leaks and slow degradation over hours. |
| Breakpoint | Increase load until a limit is hit, to find capacity. |
| Scalability | Check how throughput changes as resources are added. |

### 6. Plan data and environment
- **Environment**: record the differences from production (size, config, data volume, third-party dependencies). Each difference limits how far results transfer.
- **Test data**: enough variety and volume that caches and indexes behave as in production, with no collisions between users, and a plan to reset or clean up.
- **Dependencies**: decide which third-party or downstream systems are real, stubbed, or mocked, and note the effect on the results.

### 7. Plan monitoring
Decide what to capture on every tier before the run: application and infrastructure metrics (CPU, memory, GC, threads, connection pools), database metrics (waits, slow queries, locks), APM traces, logs, and generator health. Make sure timestamps line up across sources.

### 8. Identify risks and approvals
- Confirm permission to test the target environment, and never plan load against production unless explicitly approved.
- Check for shared-environment impact, rate limits, and alerts that will fire.
- Plan stop conditions, a rollback of test data, and who to notify.

### 9. Write the plan
One page or short document with: question, criteria, journeys and mix, workload model with derivations, test types and order, data and environment notes, monitoring, risks, and the schedule.

## Pitfalls to avoid
- Starting scripts before the criteria and workload are agreed.
- Using averages as criteria instead of percentiles.
- Guessing concurrency instead of deriving it from rate and time in system.
- A single constant think time for every user and step.
- Using the same few test records for every user.
- Testing an environment far smaller than production without saying how results transfer.
- Treating a load test as proof of capacity when only one load level was tested.

## Done when
- The question and measurable pass/fail criteria are written and agreed.
- The workload model has its derivations, and the open or closed choice is justified.
- Test types, data, environment gaps, monitoring, and risks are documented.
- Permission to test the target is confirmed.
