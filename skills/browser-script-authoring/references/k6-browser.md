# k6 browser: browser performance scripts

Verify APIs against the k6 version in use. The browser module has moved between versions (`k6/experimental/browser` earlier, `k6/browser` in recent versions). All browser calls are async.

## Structure
```js
import { browser } from 'k6/browser';
import { check } from 'k6';

export const options = {
  scenarios: {
    ui: {
      executor: 'shared-iterations',
      options: { browser: { type: 'chromium' } },
    },
  },
};

export default async function () {
  const page = await browser.newPage();
  try {
    await page.goto(`${__ENV.BASE_URL}/`, { waitUntil: 'networkidle' });
    await page.locator('button[type=submit]').click();
    check(await page.locator('#welcome').textContent(), { 'welcome shown': (t) => !!t });
  } finally {
    await page.close();
  }
}
```

## Notes
- k6 records web vitals as built-in metrics (for example LCP, CLS, and INP, prefixed `browser_web_vital_`). Set thresholds on them.
- Combine a browser scenario with a protocol scenario in the same test to measure user experience under backend load. Keep browser VUs few.
- Always close pages in `finally` so failures do not leak browsers.
- Use `page.locator()` with stable selectors and wait on conditions, not sleeps.
- Each browser VU is heavy. Watch generator CPU and memory.
