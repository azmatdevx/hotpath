---
name: browser-script-authoring
description: Use when writing browser-based performance or user-flow scripts in any tool (Playwright, k6 browser, Puppeteer, etc.). Covers when to use a real browser, stable selectors, condition-based waits, isolated state, throttling, metrics capture, repeat runs, and hybrid browser plus protocol load.
---

# Browser script authoring

Goal: a browser script that measures what a real user experiences, repeatably, without measuring its own flakiness.

This skill is tool-agnostic. Per-tool syntax is in `references/` (`playwright.md`, `k6-browser.md`, `puppeteer.md`). Read the file for the tool in use after reading this one.

## When to use

- The measurement is client-side: rendering, JavaScript execution, web vitals, perceived load time.
- The page computes values in JavaScript that a protocol-level script cannot reproduce.
- You need a user-experience measurement while backend load runs at the same time.

Do not use a browser to generate large load. Browsers are expensive per user. Generate scale at protocol level (see script-authoring, if the load-testing skills are installed) and use a few browsers for experience measurements.

## Steps

### 1. Define the flow and the measurements
Write the user steps and what you will measure at each: navigation timing, web vitals (LCP, INP, CLS), custom step durations, and the end state that proves success.

### 2. Fix the test conditions
Decide and record: device and viewport, CPU throttling, network throttling, browser version, headless or headed (keep it the same between runs), cache state (cold or warm), and geographic location of the runner. Different conditions give different numbers, so do not compare across them.

### 3. Use stable selectors
Select by role, accessible name, label, or a dedicated test attribute. Avoid long CSS paths and positional selectors that break on layout changes.

### 4. Wait on conditions, not time
Wait for a visible element, a network response, or an application signal. Never use fixed sleeps. A fixed sleep either adds noise to the measurement or fails when the page is slower.

### 5. Isolate state
Use a fresh browser context for each iteration so cookies, storage, and cache do not leak between runs. If login is expensive and not under test, authenticate once and reuse the saved session state, and say that you did.

### 6. Capture metrics
- Use the browser's Performance APIs (navigation timing, resource timing, paint timing, `PerformanceObserver` for LCP, CLS, long tasks).
- Add `performance.mark` and `performance.measure` around user steps to record custom durations in the page.
- Save a trace, HAR, or screenshots on failure and optionally on every run, and keep them out of version control if they contain real tokens.

### 7. Add assertions
Assert that each step reached the right state (expected text, element, URL). A timing from a page that showed an error is not a measurement (see `principle-prove-the-work-happened`).

### 8. Repeat and summarise
Run multiple iterations and report the median and range, not a single run. Discard a warm-up run if the plan says so. Keep the runner machine quiet, because CPU contention on the runner distorts timings.

### 9. Combine with protocol load when needed
For user experience under load, run a small number of browser users alongside protocol-level load, and report the browser metrics measured during the load.

## Pitfalls to avoid
- Fixed sleeps in place of waits.
- Comparing headless to headed, or different throttling, as if they were the same.
- Sharing browser state across iterations.
- Running many browsers on one machine and measuring the machine.
- A single run reported as a result.
- Timing a page that failed to reach the expected state.
- Selectors tied to layout.

## Done when
- Conditions (device, throttling, cache state, browser version) are recorded.
- Every step asserts its end state and waits on conditions.
- Metrics are captured, repeated, and reported as a median with a range.
- Artifacts are saved without committed secrets.
