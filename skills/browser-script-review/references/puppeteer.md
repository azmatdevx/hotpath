# Puppeteer script review

Verify details against the Puppeteer version in use.

## What to look for

- **Fixed sleeps.** `page.waitForTimeout(...)` (removed in recent versions) or `setTimeout` promises used as waits. Wait on a selector or response instead.
- **`networkidle0` and `networkidle2`.** These can hide or inflate timings on pages with background requests. Prefer a specific element or response.
- **Races.** A click followed by a separate `waitForNavigation` can miss the navigation. Start the wait before the click, for example with `Promise.all([...])`.
- **Timing method.** `Date.now()` around automation calls includes overhead. Use in-page `performance.mark` and `measure`, navigation timing, and `PerformanceObserver` for LCP, CLS, and long tasks.
- **Tracing and screenshots.** `page.tracing` and screenshots on during timed runs add overhead.
- **Isolation.** Reusing one context across iterations. Use a new browser context per iteration (`createBrowserContext`, or `createIncognitoBrowserContext` in older versions).
- **Throttling and cache.** `emulateNetworkConditions`, `emulateCPUThrottling`, and `setCacheEnabled` set inconsistently or not recorded.
- **Headless mode.** Mixing headless modes between runs, or comparing headless with headed. The behaviour and performance can differ between modes and versions.
- **Launch flags.** Flags such as `--no-sandbox` should be deliberate and limited to environments that need them.
- **Cleanup.** `browser.close()` missing from a `finally` block, which leaks processes on failure.
- **Unhandled rejections.** Missing error handling that lets a failed step look like success.
- **Selectors.** `page.$eval` on elements that may not exist yet, and brittle CSS paths.
