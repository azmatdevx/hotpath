---
name: journey-capture
description: Use when you need HAR files of a user journey captured by running a flow in a real browser, repeatably and with proof the journey completed - several runs, cold and warm cache, one HAR per run, no credentials leaked. Runs the flow, records HARs, and refuses captures of runs that did not reach the end state.
---

# Journey capture

Goal: HAR files that are safe to analyse, because each one records a journey that reached its end state, with a known cache state, over repeated runs.

This skill is tool-agnostic. The runnable script is for Playwright (`scripts/capture-playwright.js`). `references/` holds the Playwright notes and a Puppeteer outline; read the one for the tool in use.

Capture stays scripted. `playwright-cli` is for writing and repairing flows, not for measured runs: it has no HAR recording, and an agent steering the browser would make runs differ.

`<skill-dir>` below is the folder that contains this SKILL.md (the scripts live in its `scripts/` folder), and `<skills-dir>` is its parent, where the sibling skills sit. Use the real path your agent loaded this skill from; do not assume the current directory is the hotpath checkout.

The script finds the `playwright` package by looking in the current directory and then next to the script, so install it in your project (`npm i playwright`, `npx playwright install chromium`) and run the command from there.

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
node <skill-dir>/scripts/capture-playwright.js --flow flows/tc-01.js --base https://env.example --runs 3 --cache cold --out captures/
node <skill-dir>/scripts/capture-playwright.js --flow flows/tc-01.js --base https://env.example --runs 3 --cache warm --out captures/
```

Use at least 3 runs per cache state. One run cannot separate a real problem from noise.

**Recording for a load test script (perf-mode).** A script needs the request and response bodies to find its correlations, and two recordings made as different users. Record with `--content embed` and give each recording a label, using a different test account for each (the flow reads the account from the environment, never from the file):

```
TEST_USER=alice node <skill-dir>/scripts/capture-playwright.js --flow flows/tc-04.js --base https://env.example --runs 1 --content embed --label alice --out captures/
TEST_USER=bobby node <skill-dir>/scripts/capture-playwright.js --flow flows/tc-04.js --base https://env.example --runs 1 --content embed --label bobby --out captures/
```
These HARs hold real tokens, cookies, and personal data. Keep them out of version control, out of bug text, and out of replies; the script prints a warning when it records bodies. Pass the pair to the script-correlation skill (`har_correlate.py`) and one of them with its run record to the script-authoring skill (`har_transactions.py`), if the load-testing skills are installed. The run record's steps carry their start and end times for that grouping.

The script also records lab web vitals after every step into the run record (`vitals`, with the browser's user agent and any CPU slowdown under `conditions`). Add `--cpu-slowdown 4` to throttle the CPU four times (Chromium only) when the question is how a slower device fares, and state it in the results. Summarise vitals with `web-vitals-audit` (`vitals_summary.py`).

The script refuses to overwrite captures that already exist for the same flow, cache state, and run number, so runs from two attempts cannot mix by accident. When you recapture after a failure or a repair, delete the discarded files first (or use a new `--out`); `--overwrite` exists but hides what you replaced.

### 4. Check every run completed
The script writes `<flow>-<cache>-runN.json` beside each HAR with the steps reached and whether `verify` passed, and exits non-zero if any run failed. A run that did not verify is not analysed, and `compare_runs.py` refuses its HAR. Fix the flow or the environment and capture again; do not analyse the partial HAR.

### 5. When a step fails
Do not retry with the flow improvising, and do not let an agent steer the browser during a measured run. The extra latency and the chance of acting on the wrong element make the HAR untrustworthy.

- The script writes `<flow>-<cache>-runN.failure.json`: the failed step, what was tried, the URL and title, and an accessibility snapshot of the page at that moment.
- Run `flow-repair` between captures, using the bundle and the test case step. It repairs the flow and then you capture again from scratch.
- A run that verified but used a fallback locator is recorded `drifted: true`. Its HAR is valid, because the flow's own code chose the fallback and the end state was verified. Treat it as a sign to repair the primary locator before the next sweep.

### 6. Keep the HARs safe
Each HAR contains cookies, authorization headers, and request bodies. The script records no response bodies (`content: omit`), but headers and request data are still there.

- Write captures to a directory that is ignored by git (this repo ignores `*.har`) or to your artifact store.
- Do not paste a HAR into a ticket. Attach it only to a restricted location.
- If a HAR must be shared outside the team, redact cookies, authorization headers, and personal data first.

### 7. Hand off
Pass the verified HARs to `har-analysis`. Keep the run records; they show how far each run got.

## Pitfalls to avoid
- Analysing a HAR from a run that did not reach the end state.
- Mixing cold and warm results.
- Capturing in parallel against one environment.
- Capturing while a deployment or a load test is running.
- A single run.
- Letting the flow or an agent improvise mid-run, then analysing that run.
- Leaving HARs where they will be committed or shared.
- Capturing the login in every HAR when the login is not under test.

## Done when
- Each HAR has a run record showing the journey verified, and any `drifted` runs are noted.
- There are at least 3 runs for each cache state captured, and each result states which.
- The build and environment are written down.
- The HARs are stored somewhere safe, not in version control.
