---
name: browser-script-review
description: Use when reviewing a browser-based performance or user-flow script (Playwright, k6 browser, or Puppeteer) before it is run or merged. Checks selectors, waits, state isolation, measurement integrity, flakiness masking, safety, and maintainability, and reports findings by severity with a verdict.
---

# Browser script review

Goal: make sure a browser script measures what a real user experiences, repeatably, and that its timings are not distorted by the script itself.

This skill is tool-agnostic. Per-tool things to look for are in `references/` (`playwright.md`, `k6-browser.md`, `puppeteer.md`). Read the file for the tool in use after reading this one. For protocol-level scripts use `script-review`. For writing one, see `browser-script-authoring`.

## When to use

- A browser script was written or changed, by a person or an agent.
- Browser timings vary between runs and the script is the suspect.
- A script is about to support a frontend performance decision.

## Steps

### 1. Get context
Find out what is being measured (page load, a step, web vitals), under which conditions (device, throttling, cache state, location), and the tool and version.

### 2. Review by category
**Stability and flakiness**
- Selectors use roles, labels, or test attributes, not long CSS paths or positions.
- Waits are conditions (an element, a response), never fixed sleeps.
- Retries are not hiding slowness. A test that passes on a retry reports an inflated or unreliable time.
- Navigation and click races are handled (waiting for navigation started by the click).

**Measurement integrity**
- Timings come from the browser (Performance APIs, `performance.mark` and `measure`, web vitals observers), not from wall-clock timers around automation calls that include tool overhead.
- Tracing, video, screenshots, and verbose logging are off during timed runs and used only for diagnosis.
- Conditions (viewport, CPU and network throttling, cache state, headless or headed) are fixed and recorded.
- The timed region contains only the work being measured.
- Multiple iterations are run and summarised with medians and ranges.

**State and isolation**
- A fresh context per iteration, so cookies, storage, and cache do not leak.
- Authentication reuse is deliberate and stated.
- Test data does not collide between parallel runs.

**Correctness**
- Each step asserts it reached the expected state, so a timed error page is not reported as a measurement (see `principle-prove-the-work-happened`).
- Failures are recorded, not swallowed.

**Resources and safety**
- Browsers and pages are closed in `finally` or equivalent, so failures do not leak processes.
- Parallelism is limited so browsers do not compete for CPU on the runner.
- The target comes from configuration, secrets are not in the script, and no destructive action targets a real system.
- Any blocked third-party requests are disclosed in the report, since they change results.

**Maintainability**
- Shared steps are reused, configuration is externalised, and the file explains how to run it.

### 3. Run it when you can
Run the script several times under the stated conditions. Check that the results are stable, that assertions fail when they should, and that no browsers are left running.

### 4. Report findings
For each finding give: location, severity (**Blocker**, **Major**, **Minor**, **Nit**), why it affects the measurement, and a suggested fix. Group by severity.

### 5. Give a verdict
**approve**, **approve with changes**, or **request changes**, and list what you did not check.

## Pitfalls to avoid
- Accepting fixed sleeps because "it works".
- Missing that retries inflate times.
- Timing around automation calls and calling it page load time.
- Ignoring that tracing or video were on during the timed run.
- Reviewing only the happy path.

## Done when
- Each category was reviewed, and findings have location, severity, effect, and fix.
- The verdict follows from the findings, and unchecked areas are stated.
