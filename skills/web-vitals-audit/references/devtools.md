# Browser DevTools: web vitals audit

Verify panel names against the browser version in use. These notes assume Chrome DevTools.

## Setup
- Use a clean profile or an incognito window with extensions disabled, so extensions do not distort results.
- Throttle the network and CPU in the Network and Performance panels to match the target device, and record the settings. Disable cache when measuring a cold load.

## Panels
- **Performance**: record a page load or an interaction. The timeline marks LCP, layout shifts, and long tasks, and the insights show LCP phases and interaction breakdowns.
- **Network**: the request waterfall, sizes, caching and compression headers, priorities, and blocking.
- **Lighthouse**: a quick lab run from within DevTools.
- **Rendering**: "Layout Shift Regions" highlights shifting elements.
- **Coverage**: unused CSS and JavaScript.

## Measuring in the console
```js
new PerformanceObserver((list) => {
  for (const e of list.getEntries()) console.log(e.entryType, e.startTime, e);
}).observe({ type: 'largest-contentful-paint', buffered: true });
```
Use the same pattern with `layout-shift` and `longtask`. The `web-vitals` library gives the same values as the field tools.

## Notes
- Local DevTools results depend on your machine. Compare only runs made in the same conditions, and repeat them.
- Use local overrides to test a change without deploying it, then confirm with a proper repeated measurement.
