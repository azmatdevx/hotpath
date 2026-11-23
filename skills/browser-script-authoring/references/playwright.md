# Playwright: browser performance scripts

Verify APIs against the Playwright version in use.

## Structure
```ts
import { chromium } from 'playwright';

const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 1366, height: 768 } });
const page = await context.newPage();

await page.goto(process.env.BASE_URL!);
await page.getByRole('button', { name: 'Sign in' }).click();
await page.getByTestId('welcome').waitFor();   // wait on a condition
```

## Notes
- Prefer `getByRole`, `getByLabel`, and `getByTestId`. Playwright auto-waits on actions, and `expect(...)` web assertions retry.
- Use a new context per iteration. Reuse login with `storageState` when authentication is not under test, and state that.
- Read metrics from the page:
  ```ts
  const nav = await page.evaluate(() =>
    JSON.stringify(performance.getEntriesByType('navigation')[0]));
  ```
  Use `PerformanceObserver` (via `page.evaluate` or `addInitScript`) for LCP, CLS, and long tasks, or inject the `web-vitals` library.
- Throttling on Chromium is available through a CDP session (`context.newCDPSession(page)`) with `Network.emulateNetworkConditions` and `Emulation.setCPUThrottlingRate`. It does not work in the same way on other browsers.
- Record a trace with `context.tracing.start({ screenshots: true, snapshots: true })` and open it with the trace viewer, and capture a HAR with `recordHar` on the context.
- Keep workers low when timing matters, because parallel browsers compete for CPU.
