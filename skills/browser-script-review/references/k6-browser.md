# k6 browser script review

Verify details against the k6 version in use. The browser module path has changed between versions, and all browser calls are async.

## What to look for

- **Missing `await`.** Calls without `await` run out of order and produce meaningless timings or unhandled errors.
- **Click and navigation races.** A click that triggers navigation should be combined with the wait for navigation using `Promise.all([...])`, to avoid missing the event.
- **Pages not closed.** `page.close()` should be in a `finally` block, so failures do not leak browsers.
- **Fixed sleeps.** `page.waitForTimeout(...)` or `sleep()` used as a wait. Wait on a locator or response instead.
- **No thresholds.** Web vital metrics (for example LCP, CLS, INP, prefixed `browser_web_vital_`) and check rates should have thresholds so the run can fail (see ci-performance-gates, if the load-testing skills are installed).
- **Too many browser VUs.** Each browser VU is heavy. Check generator CPU and memory and limit the count. Use protocol-level scenarios for scale.
- **Isolation.** A new context or page per iteration where state must not leak.
- **Checks.** Content checks missing after steps, or checks that read values that could be empty.
- **Scenario options.** The `browser` option (type `chromium`) missing from the scenario, or an executor unsuited to the intent.
- **Hybrid tests.** Browser scenario mixed with protocol load without separate thresholds per scenario.
- **Secrets and hosts.** Hard-coded URLs and credentials instead of `__ENV`.
