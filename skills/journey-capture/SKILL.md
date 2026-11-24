---
name: journey-capture
description: Use when you need HAR files of a user journey captured by running a flow in a real browser, repeatably and with proof the journey completed - several runs, cold and warm cache, one HAR per run, no credentials leaked. Runs the flow, records HARs, and refuses captures of runs that did not reach the end state.
---

# Journey capture

Goal: HAR files that are safe to analyse, because each one records a journey that reached its end state, with a known cache state, over repeated runs.

This skill is tool-agnostic. The runnable script is for Playwright (`scripts/capture-playwright.js`). `references/` holds the Playwright notes and a Puppeteer outline; read the one for the tool in use.

## When to use
- You have a flow (see `flow-from-test-case`) and want HARs for `har-analysis`.
- You need the same capture done the same way for many journeys.

## Steps

### 1. Check what you need
- A flow module that exports a step list and a `verify` check. Without `verify` you cannot tell a completed journey from a stopped one.
- The base URL of the environment under test, and confirmation that it is the intended one.
- A browser tool installed (for Playwright: `npm i playwright` and `npx playwright install chromium`).

### 2. Pick the environment and keep it steady
Timings are only comparable if the environment is. Capture against an environment that is not being deployed to, and note the build. Do not run captures in parallel against the same environment: they load each other and distort the timings. Run captures one at a time; analysis can run in parallel.

### 3. Capture cold and warm
Cold is a fresh browser profile with an empty cache: what a first-time visitor sees. Warm is a repeat visit with the cache populated by a priming pass. Capture both for journeys where caching matters; the findings differ (assets that are cached when warm do not appear). State which one a result came from.

```
node scripts/capture-playwright.js --flow flows/tc-01.js --base https://env.example --runs 3 --cache cold --out captures/
node scripts/capture-playwright.js --flow flows/tc-01.js --base https://env.example --runs 3 --cache warm --out captures/
```

Use at least 3 runs per cache state. One run cannot separate a real problem from noise.

### 4. Check every run completed
The script writes `<flow>-<cache>-runN.json` beside each HAR with the steps reached and whether `verify` passed, and exits non-zero if any run failed. A run that did not verify is not analysed, and `compare_runs.py` refuses its HAR. Fix the flow or the environment and capture again; do not analyse the partial HAR.

### 5. Keep the HARs safe
Each HAR contains cookies, authorization headers, and request bodies. The script records no response bodies (`content: omit`), but headers and request data are still there.

- Write captures to a directory that is ignored by git (this repo ignores `*.har`) or to your artifact store.
- Do not paste a HAR into a ticket. Attach it only to a restricted location.
- If a HAR must be shared outside the team, redact cookies, authorization headers, and personal data first.

### 6. Hand off
Pass the verified HARs to `har-analysis`. Keep the run records; they show how far each run got.

## Pitfalls to avoid
- Analysing a HAR from a run that did not reach the end state.
- Mixing cold and warm results.
- Capturing in parallel against one environment.
- Capturing while a deployment or a load test is running.
- A single run.
- Leaving HARs where they will be committed or shared.
- Capturing the login in every HAR when the login is not under test.

## Done when
- Each HAR has a run record showing the journey verified.
- There are at least 3 runs for each cache state captured, and each result states which.
- The build and environment are written down.
- The HARs are stored somewhere safe, not in version control.
