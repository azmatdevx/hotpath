# Playwright: journey capture

`scripts/capture-playwright.js` was run against Playwright 1.49 (Chromium headless shell) on macOS, on a local app. It has not been run against SSO, MFA, or a real production-like site.

## Flow module
```js
module.exports = {
  id: 'tc-01-view-orders',
  steps: [
    ['Open the base URL', async (page, base) => { await page.goto(base + '/start'); }],
    ['Wait for the orders count', async (page) => { await page.getByText('3 orders').waitFor(); }],
  ],
  async verify(page) {                       // throw unless the journey reached its end state
    if ((await page.locator('#orders').textContent()) !== '3 orders') throw new Error('wrong end state');
  },
};
```

## What the script does
- **Cold:** a new browser and context per run, so the HTTP cache is empty.
- **Warm:** a persistent profile in a temporary directory. The flow runs once with no HAR (priming), the browser closes, then it reopens on the same profile and records the measured pass.
- **HAR:** `recordHar` with `content: 'omit'`. Sizes are still recorded. `content.size` can be 0 for some binary responses (an image showed 0 here), and the analyzer then reports the wire size and says the decoded size was not recorded.
- Every run's profile is deleted afterwards.

## Notes
- Playwright HARs have no `_resourceType`, so the analyzer classifies requests by MIME type.
- To reuse a saved login, create a context with `storageState` in a setup script; the capture script does not do this yet, so add it to your flow's first step or extend the script.
- Network and CPU throttling are not applied. Add them in the script (Chromium only, through a CDP session) if the exercise needs them, and state the profile in the results.
- A flow that uses a popup or a new tab needs `context.waitForEvent('page')`; `recordHar` is set per context, so pages opened in the same context should land in the same HAR; this was not tested.
