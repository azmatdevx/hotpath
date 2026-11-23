---
name: load-run-checklist
description: Use immediately before, during, and after a load run. Covers permission and approvals, environment state, data readiness, load generator sizing, monitoring, ramp plan, stop conditions, live watching, artifact collection, and cleanup.
---

# Load run checklist

Goal: a run whose results you can trust and repeat, with no surprises for the people sharing the environment.

Use this together with `load-test-design` (the plan) and `results-sanity-check` (the vetting afterwards).

## When to use

- Before starting any load run beyond a smoke test.
- While a run is in progress.
- Right after a run, before the environment is changed.

## Before the run

**Permission and communication**
- [ ] Permission to test this environment is confirmed. No load against production unless explicitly approved for this run.
- [ ] Teams that share the environment, and on-call, are told the window. Alerts are muted or the team is warned.
- [ ] A rollback or stop contact exists.

**Environment**
- [ ] Application version, configuration, and feature flags are recorded and match the plan.
- [ ] Dependent systems are in the intended state (real, stubbed, or mocked).
- [ ] Caches are in the intended state (cold or warm), and the plan says which.
- [ ] No other tests, deployments, or batch jobs will run in the window.

**Data**
- [ ] Test data is loaded, valid, and large enough (see `script-parameterization`).
- [ ] Single-use data is reset or freshly generated.

**Script and workload**
- [ ] The script passed validation with the current data and build (see `script-validation`).
- [ ] Debug logging and GUI listeners are off. The run is headless.
- [ ] The workload matches the design: users or arrival rate, ramp-up, duration, think time, pacing.
- [ ] A ramp plan exists, with a smoke test first and step increases after.

**Load generators**
- [ ] Generators are sized for the target load, with spare capacity. As a rule of thumb, keep CPU well below saturation (for example under 70 to 80 percent), and confirm by running the generator at the target load against a known-fast endpoint.
- [ ] Network capacity and latency from the generator to the target match the plan.
- [ ] Generator clocks are synchronised with servers (NTP).
- [ ] Output location has enough disk space, and the data file exists on every generator.

**Monitoring**
- [ ] Metrics are collecting on every tier: CPU, memory, GC, threads, pools, DB waits and slow queries, queues, APM traces, logs.
- [ ] Generator health is monitored.
- [ ] Timestamps align across sources.

**Stop conditions**
- [ ] Abort thresholds are agreed (for example error rate, response time, or resource ceiling) and known to whoever watches the run.

**Run record**
- [ ] A run ID, the plan version, the script version, and the start time are noted.

## During the run

- Watch error rate, throughput, response time percentiles, generator health, and server resources.
- Annotate events as they happen: ramp steps, deployments, alerts, anomalies, with timestamps.
- Stop early if the error rate climbs at low load, the generator saturates, or an abort threshold is hit. Fix, then restart. Do not let a bad run continue to completion and report it.
- Change nothing in the environment during the run unless the plan says so.

## After the run

- [ ] Stop load cleanly. Allow in-flight requests to finish where possible.
- [ ] Collect artifacts before anything is changed: raw results, tool logs, monitoring exports, application and database logs, configs, and the annotated event list.
- [ ] Record run metadata (template below).
- [ ] Clean or reset test data, and restore alerts and any temporary settings.
- [ ] Note anything unusual, then run `results-sanity-check`.

## Run record template

```
Run ID:            <id>
Date/time:         <start - end, timezone>
Plan/script:       <versions>
Tool and version:  <tool>
Environment:       <name, app version, config, differences from production>
Workload:          <users or rate, ramp, duration, think time>
Generators:        <count, size, location>
Data:              <source, volume, reset state>
Events:            <timestamped notes>
Artifacts:         <paths>
Outcome:           <aborted | completed>, <first impression>
```

## Pitfalls to avoid
- Starting at full load without a smoke test and ramp.
- Letting the generator become the bottleneck without noticing.
- Changing two things between runs.
- Running while another team is deploying to the same environment.
- Collecting only the tool's summary, then resetting the environment.
- Leaving alerts muted after the run.

## Done when
- Every item before the run is checked or explicitly waived.
- The run was watched, and events were annotated.
- All artifacts are saved with a run record, and the environment is cleaned up.
