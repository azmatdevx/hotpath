---
name: ci-performance-gates
description: Use when adding automated performance checks to a CI/CD pipeline, in any tool (JMeter, k6, Locust, Gatling, etc.). Covers what to gate and when, deriving budgets from a baseline, handling noisy CI runners, baseline comparison, flaky-gate policy, and publishing results.
---

# CI performance gates

Goal: catch performance regressions automatically, with a gate people trust because it rarely cries wolf.

This skill is tool-agnostic. Per-tool pass/fail mechanics are in `references/` (`jmeter.md`, `k6.md`, `locust.md`, `gatling.md`). Read the file for the tool in use after reading this one.

## When to use

- Performance is only checked manually, and regressions reach production.
- A gate exists but is ignored because it is flaky.
- A release process needs an objective performance criterion.

## Steps

### 1. Decide what to gate and when
Match the test to the pipeline stage and its time budget:
- **Per pull request:** a short smoke or small load test on the changed service (minutes).
- **Per merge or nightly:** a fuller load test on a stable environment.
- **Weekly or pre-release:** soak, stress, or capacity tests.
Do not run long tests on every commit. Slow gates get skipped.

### 2. Establish a baseline
Run the test several times on the target environment and record medians and ranges for the key metrics. The gate compares against this baseline, so it must come from the same workload, environment, and data.

### 3. Set budgets with tolerance
Define pass/fail thresholds per critical transaction: a percentile latency, an error rate, and where relevant throughput. Derive them from the SLA and the baseline, and leave a tolerance larger than run-to-run noise. A threshold tighter than the noise makes the gate flaky. Prefer relative thresholds ("no more than 10% above baseline") for regression gates and absolute thresholds for SLA gates.

### 4. Control the environment
Shared CI runners are noisy. Use a dedicated or consistent environment for the system under test, and do not run the load generator on the same machine as the system under test. Reset test data before each run. Record versions and configuration with each result.

### 5. Reduce flakiness
- Run the test more than once for borderline results, and judge on the median.
- Require the failure to repeat (for example 2 of 3 runs) before failing the build.
- Separate **fail** (clear breach) from **warn** (within tolerance of the limit).
- Exclude warm-up and ramp phases from the evaluated window.

### 6. Make failures actionable
On failure, show the metric, the threshold, the baseline, and a link to the full report. Save raw results and the run record as build artifacts. Link the failing run to the commit range that introduced it.

### 7. Keep a trend
Store results per build, so you can see slow drift that never crosses a single threshold. Review the trend regularly and update baselines on purpose, never automatically after a failure.

### 8. Protect the pipeline
- Keep secrets in the CI secret store, not in scripts.
- Limit the load so a bad change cannot overwhelm a shared environment.
- Add a timeout and a stop condition to the job.
- Make the gate's owner clear, so failures are triaged.

## Pitfalls to avoid
- Gating microbenchmarks that vary more than the effect you want to detect.
- Thresholds set tighter than the noise.
- Running the generator and the system under test on the same runner.
- Updating the baseline automatically so regressions become the new normal.
- A gate that is allowed to fail without anyone investigating.
- Gating on averages instead of percentiles.

## Done when
- The gate runs at the right pipeline stage within its time budget.
- Budgets come from a baseline and exceed the measured noise.
- Failures show metric, threshold, baseline, and a link to the report.
- Raw results are stored and trended, and baseline updates are deliberate.
