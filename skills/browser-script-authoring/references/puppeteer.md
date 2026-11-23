# Puppeteer: browser performance scripts

Verify APIs against the Puppeteer version in use.

## Structure
```js
import puppeteer from 'puppeteer';

const browser = await puppeteer.launch();
const context = await browser.createBrowserContext();   // isolated state per iteration
const page = await context.newPage();

await page.goto(process.env.BASE_URL, { waitUntil: 'networkidle0' });
await page.waitForSelector('#welcome');                  // wait on a condition
```

## Notes
- Older versions use `createIncognitoBrowserContext()`. Use one context per iteration for isolation.
- Throttling: `page.emulateNetworkConditions(...)` with a predefined profile, and `page.emulateCPUThrottling(4)`. Record the settings.
- Metrics: `page.metrics()` for coarse runtime metrics, `page.evaluate(() => performance.getEntriesByType('navigation'))` for navigation timing, and `PerformanceObserver` for LCP, CLS, and long tasks.
- Traces: `page.tracing.start({ path: 'trace.json', screenshots: true })` and `page.tracing.stop()`. Open in Chrome DevTools Performance panel.
- `waitUntil: 'networkidle0'` can hide or inflate timings on pages with background requests, so prefer waiting for a specific element or response.
- Close the browser in `finally` to avoid leaking processes.
