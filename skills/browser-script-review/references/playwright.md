# Playwright script review

Verify details against the Playwright version in use.

## What to look for

- **Fixed sleeps.** `page.waitForTimeout(...)`. Replace with a wait on an element, response, or state.
- **`networkidle`.** `waitForLoadState('networkidle')` and `waitUntil: 'networkidle'` are discouraged for general use and can hide or inflate timings on pages with background requests. Prefer a specific element or response.
- **Retries.** A non-zero `retries` in config can mask flaky or slow behaviour and distort timing. For performance runs, prefer zero retries and investigate failures.
- **Tracing, video, screenshots.** `trace: 'on'`, `video: 'on'`, or constant screenshots add overhead. Use them on failure or in separate diagnostic runs.
- **Parallelism.** `workers` and `fullyParallel` that run many browsers on one machine compete for CPU and distort timings.
- **Timing method.** `Date.now()` around Playwright calls includes automation overhead. Prefer `performance.mark` and `measure` inside the page, navigation and paint timings, and `PerformanceObserver` for LCP, CLS, and long tasks (with `buffered: true`).
- **State.** A shared context between iterations, or `storageState` reused without it being stated.
- **Selectors.** Legacy `page.$` or brittle CSS paths. Prefer `getByRole`, `getByLabel`, and `getByTestId`.
- **Assertions.** Missing `expect(...)` after steps, or `expect` with excessively long timeouts that hide slow responses.
- **Request blocking.** `page.route(...)` aborts that change page weight and behaviour without being reported.
- **Throttling.** CDP throttling (Chromium only) applied inconsistently or not recorded.
- **Cleanup.** Browser or context not closed on failure.
