---
name: web-vitals-audit
description: Use when auditing web page performance (LCP, INP, CLS, TTFB, waterfall) in any tool (Lighthouse, WebPageTest, Playwright, browser devtools) and proposing measured fixes. Combines lab and field data, diagnoses each metric, and re-measures one change at a time.
---

# Web vitals audit

Goal: find what makes a page feel slow for real users, fix the largest cause first, and prove the improvement.

This skill is tool-agnostic. Per-tool notes are in `references/` (`lighthouse.md`, `webpagetest.md`, `devtools.md`). Read the file for the tool in use after reading this one. For scripted browser flows, see `browser-script-authoring`. `<skill-dir>` below is the folder containing this SKILL.md.

## When to use

- A page or journey feels slow, or a vitals score is poor.
- Before and after a frontend change that may affect performance.
- A release needs a frontend performance check.

## Steps

### 1. Define the pages and conditions
List the pages or journeys and the target users: device class, network, and location. Results depend on these, so record them and keep them fixed between measurements.

### 2. Gather field data, if available
Field data (real user monitoring, or the Chrome UX Report) shows what users actually experience, summarised at the 75th percentile. Use it to decide which pages and metrics matter. Lab tools cannot tell you how many users are affected.

### 3. Measure in the lab
Use a lab tool for repeatable diagnosis: run each test several times, and report the median, because lab results vary between runs. Record the tool, version, device and network emulation, and cache state.

### 4. Know the metrics and thresholds
At the 75th percentile, Google's "good" thresholds are:
- **LCP** (Largest Contentful Paint): 2.5 s or less.
- **INP** (Interaction to Next Paint): 200 ms or less.
- **CLS** (Cumulative Layout Shift): 0.1 or less.
Also track **TTFB** (server and network delay before the first byte), **FCP**, and **Total Blocking Time** (a lab proxy for responsiveness, since INP needs real interactions).

### 5. Diagnose by metric
**LCP**: identify the LCP element, then split its time into TTFB, resource load delay, resource load time, and render delay. Then look for slow server response, late discovery of the element (for example an image loaded by JavaScript or CSS), large or unoptimised images, render-blocking CSS or JavaScript, and client-side rendering that delays content.

**INP**: find slow interactions, then split into input delay (main thread busy), processing time (event handler cost), and presentation delay (rendering). Look for long tasks, heavy handlers, hydration, and third-party scripts.

**CLS**: find the elements that shift. Common causes are images and embeds without dimensions, content injected above existing content, web font swaps, and late-loading ads or banners.

**TTFB**: look at backend time, redirects, TLS and connection setup, and the absence of caching or a CDN.

### 6. Read the waterfall
In the request waterfall, look for: long chains of dependent requests, render-blocking resources, large payloads, uncompressed or uncached assets, too many connections to many hosts, and third-party scripts delaying critical content.

### 7. Prioritise
Rank findings by effect on the failing metric and by effort. Fix the biggest cause of the worst metric first. A fix that does not move the metric is not a fix (see `principle-explain-the-number`).

### 8. Change one thing and re-measure
Apply one change, then re-run the same test under the same conditions, several runs, and compare medians (see `principle-one-variable-at-a-time`). Confirm in field data over time where possible, since lab gains do not always show up for real users.

### 9. Report
Give before and after numbers per metric with the percentile or median, the conditions, the cause found, the change made, and what remains. Hand the write-up to the test-report skill if it is installed; in a journey sweep the write-up is the bug drafts from `perf-bug-writing`.

## In a journey sweep (scripted, repeatable)
`journey-capture` records lab vitals after every step (LCP and its element, CLS, FCP, TBT, TTFB, and the slowest interaction as an INP approximation) into each run's record. Summarise them across the runs of a journey:

```
python3 <skill-dir>/scripts/vitals_summary.py --journey tc-03-cold --json tc-03-vitals.json captures/tc-03-*-cold-run?.json
```
It uses the latest reading per page in each run, shows median and range per metric against the limits (Google's "good" values by default; change them with the flags), refuses a run that did not verify, and writes rows that `sweep-rollup` and `perf-bug-writing` read like HAR findings. A metric over its limit in every run is a candidate finding; in some runs it is intermittent.

What these numbers are: one user, headless Chromium, no network throttling unless you set it (`--cpu-slowdown` slows the CPU). They are lab values to compare across runs under the same conditions, not what real users see; field data is the measure of that. The slowest interaction equals INP only when the journey has few interactions. For a page the journey leaves and returns to, only the last reading per page is kept.

## Pitfalls to avoid
- Optimising the Lighthouse score instead of real user experience.
- Reporting one run, or comparing runs under different throttling.
- Ignoring field data, then fixing a page few users visit.
- Testing only with a warm cache or only on a fast desktop connection.
- Fixing several things at once and not knowing which helped.
- Treating lab Total Blocking Time as if it were INP.

## Done when
- Pages and conditions are recorded, and lab runs are repeated with medians.
- Each failing metric has a diagnosed cause with evidence from the trace or waterfall.
- Each change has before and after measurements under the same conditions.
- Remaining issues and limits of the data are stated.
