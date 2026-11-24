// Lab web vitals for one page, read from the browser's PerformanceObservers.
// `init` runs in every document before the page's own scripts; `collect` reads the values after a step.
//
// These are lab numbers from one unthrottled-by-default headless Chromium, so compare them only across runs made
// under the same conditions (the capture records the conditions). They are approximations of the field metrics:
//   lcp   latest largest-contentful-paint candidate (ms)        cls   layout shifts without recent input
//   fcp   first-contentful-paint (ms)                           tbt   sum of (long task duration - 50 ms) after FCP
//   ttfb  navigation responseStart (ms)                         inp   the slowest interaction seen (ms); with few
//                                                                     interactions this is what INP reports
function init() {
  const v = { lcp: null, lcpElement: null, cls: 0, fcp: null, tbt: 0, inp: null };
  window.__vitals = v;
  const watch = (type, fn, opts) => {
    try { new PerformanceObserver((l) => l.getEntries().forEach(fn)).observe({ type, buffered: true, ...opts }); } catch (e) { /* unsupported */ }
  };
  watch('largest-contentful-paint', (e) => {
    v.lcp = e.startTime;
    v.lcpElement = e.element ? e.element.tagName + (e.url ? ' ' + e.url.split('?')[0].split('/').pop() : '') : null;
  });
  watch('layout-shift', (e) => { if (!e.hadRecentInput) v.cls += e.value; });
  watch('paint', (e) => { if (e.name === 'first-contentful-paint') v.fcp = e.startTime; });
  watch('longtask', (e) => { if (v.fcp !== null && e.startTime >= v.fcp) v.tbt += Math.max(0, e.duration - 50); });
  watch('event', (e) => { if (e.interactionId) v.inp = Math.max(v.inp || 0, e.duration); }, { durationThreshold: 16 });
}

async function collect(page, settleMs = 0) {
  try {
    return await page.evaluate(async (settle) => {
      // two frames let paint-related entries arrive; a longer settle lets slow interactions report (they arrive after the next paint)
      await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
      if (settle) await new Promise((r) => setTimeout(r, settle));
      const v = window.__vitals;
      if (!v) return null;
      const nav = performance.getEntriesByType('navigation')[0];
      const r = (n) => (n === null ? null : Math.round(n * 1000) / 1000);
      return { url: location.origin + location.pathname, lcp_ms: v.lcp === null ? null : Math.round(v.lcp), lcpElement: v.lcpElement,
               cls: r(v.cls), fcp_ms: v.fcp === null ? null : Math.round(v.fcp), tbt_ms: Math.round(v.tbt),
               inp_ms: v.inp === null ? null : Math.round(v.inp), ttfb_ms: nav ? Math.round(nav.responseStart) : null };
    }, settleMs);
  } catch (e) {
    return null;   // the page navigated or closed mid-read
  }
}
module.exports = { init, collect };
