#!/usr/bin/env node
// Run a journey flow in headless Chromium and record a HAR per run, plus a small JSON record of how far it got.
//
// usage: node capture-playwright.js --flow flows/01.js --base http://localhost:3918 --runs 3 --cache cold --out captures/
//   --cache cold   fresh browser profile for every run (empty cache)
//   --cache warm   a priming pass first, then the measured pass in the same profile (populated cache)
// Needs the `playwright` package and a browser (npm i playwright; npx playwright install chromium).
//
// A flow module exports { id, steps: [[name, async (page, base) => {}], ...], verify: async (page) => {} }.
// verify must throw unless the journey reached its end state; a run that fails verify is marked failed and
// its HAR must not be analysed.
const fs = require('fs');
const os = require('os');
const path = require('path');
const { chromium } = require('playwright');

const arg = (n, d) => { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; };
const flowPath = path.resolve(arg('flow'));
const base = arg('base');
const runs = Number(arg('runs', 3));
const cache = arg('cache', 'cold');
const out = path.resolve(arg('out', 'captures'));
if (!flowPath || !base || !['cold', 'warm'].includes(cache)) {
  console.error('usage: capture-playwright.js --flow F --base URL [--runs 3] [--cache cold|warm] [--out DIR]');
  process.exit(2);
}
const flow = require(flowPath);
fs.mkdirSync(out, { recursive: true });

async function walk(page) {
  const record = [];
  for (const [name, fn] of flow.steps) {
    const t = Date.now();
    try { await fn(page, base); record.push({ name, ok: true, ms: Date.now() - t }); }
    catch (e) { record.push({ name, ok: false, ms: Date.now() - t, error: String(e.message).split('\n')[0] }); return record; }
  }
  return record;
}

(async () => {
  let failed = 0;
  for (let n = 1; n <= runs; n++) {
    const tag = `${flow.id}-${cache}-run${n}`;
    const har = path.join(out, tag + '.har');
    const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'sweep-profile-'));
    let ctx;
    const meta = { flow: flow.id, run: n, cache, base, steps: [], verified: false };
    try {
      if (cache === 'warm') {
        const prime = await chromium.launchPersistentContext(profile, { headless: true });
        await walk(await prime.newPage());
        await prime.close();
        ctx = await chromium.launchPersistentContext(profile, { headless: true, recordHar: { path: har, content: 'omit' } });
      } else {
        const browser = await chromium.launch({ headless: true });
        ctx = await browser.newContext({ recordHar: { path: har, content: 'omit' } });
        ctx._sweepBrowser = browser;
      }
      const page = await ctx.newPage();
      meta.steps = await walk(page);
      if (meta.steps.every((s) => s.ok)) {
        try { await flow.verify(page); meta.verified = true; } catch (e) { meta.error = String(e.message).split('\n')[0]; }
      }
    } catch (e) { meta.error = String(e.message).split('\n')[0]; }
    finally {
      if (ctx) { await ctx.close(); if (ctx._sweepBrowser) await ctx._sweepBrowser.close(); }
      fs.rmSync(profile, { recursive: true, force: true });
    }
    if (!meta.verified) failed++;
    fs.writeFileSync(path.join(out, tag + '.json'), JSON.stringify(meta, null, 2));
    console.log(`${tag}: ${meta.verified ? 'verified' : 'FAILED ' + (meta.error || 'a step failed')}`);
  }
  process.exit(failed ? 1 : 0);
})();
