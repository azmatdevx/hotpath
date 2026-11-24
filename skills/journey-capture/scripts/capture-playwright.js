#!/usr/bin/env node
// Run a journey flow in headless Chromium and record a HAR per run, plus a small JSON record of how far it got.
//
// usage: node capture-playwright.js --flow flows/01.js --base http://localhost:3918 --runs 3 --cache cold --out captures/
//   --cache cold   fresh browser profile for every run (empty cache)
//   --cache warm   a priming pass first, then the measured pass in the same profile (populated cache)
//   --content omit|embed   embed records response bodies in the HAR (needed to find correlations for a load test
//                  script); the default omit records none. A HAR with bodies holds real tokens and personal data.
//   --label NAME   put NAME in the file names (for example the test account), so two recordings of one journey
//                  can sit in one folder
//   --env NAME=VALUE   set an environment variable for the flow (repeatable), for example the test account:
//                  --env TEST_USER=alice. Use it for non-secret values; secrets come from the environment.
//   --cpu-slowdown N   throttle the CPU N times (Chromium only); recorded in the run record
//   --overwrite    replace existing captures with the same name; without it the script refuses, so runs from
//                  different attempts cannot be mixed by accident. Delete discarded captures instead where you can.
// Needs the `playwright` package and a browser (npm i playwright; npx playwright install chromium).
//
// A flow module exports { id, steps: [[name, async (page, base, find) => {}], ...], verify: async (page) => {} }.
// `find` resolves an element from ordered candidate locators (see locate.js) and records which one matched.
// verify must throw unless the journey reached its end state; a run that fails verify is marked failed and
// its HAR must not be analysed.
const fs = require('fs');
const os = require('os');
const path = require('path');
let chromium;
try {
  // look in the project the command is run from first, then next to this script
  ({ chromium } = require(require.resolve('playwright', { paths: [process.cwd(), __dirname] })));
} catch (e) {
  console.error('the playwright package was not found. In your project run: npm i playwright && npx playwright install chromium');
  process.exit(2);
}
const { createFinder } = require('./locate');
const vitals = require('./vitals');

// --env NAME=VALUE (repeatable) sets variables for the flow, so no shell prefix is needed under an allowlist
process.argv.forEach((v, i) => {
  if (v === '--env' && /^[A-Za-z_][A-Za-z0-9_]*=/.test(process.argv[i + 1] || '')) {
    const [k, ...rest] = process.argv[i + 1].split('=');
    process.env[k] = rest.join('=');
  }
});
const arg = (n, d) => { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; };
const flowPath = path.resolve(arg('flow'));
const base = arg('base');
const runs = Number(arg('runs', 3));
const cache = arg('cache', 'cold');
const content = arg('content', 'omit');
const label = arg('label', '');
const out = path.resolve(arg('out', 'captures'));
const cpuSlowdown = Number(arg('cpu-slowdown', 1));
if (!flowPath || !base || !['cold', 'warm'].includes(cache) || !['omit', 'embed'].includes(content) || /[^\w.-]/.test(label)) {
  console.error('usage: capture-playwright.js --flow F --base URL [--runs 3] [--cache cold|warm] [--content omit|embed] [--label NAME] [--out DIR]');
  process.exit(2);
}
const flow = require(flowPath);
fs.mkdirSync(out, { recursive: true });
const tagOf = (n) => `${flow.id}${label ? '-' + label : ''}-${cache}-run${n}`;
if (content === 'embed') {
  console.error('recording response bodies: these HARs hold real tokens and personal data. Keep them out of version control and out of bug text.');
}
const existing = [];
for (let n = 1; n <= runs; n++) {
  for (const ext of ['.har', '.json', '.failure.json']) {
    const f = path.join(out, `${tagOf(n)}${ext}`);
    if (fs.existsSync(f)) existing.push(path.basename(f));
  }
}
if (existing.length && !process.argv.includes('--overwrite')) {
  console.error('refusing to overwrite existing captures: ' + existing.join(', ') +
    '\nDelete the ones you are discarding, use another --out, or pass --overwrite.');
  process.exit(2);
}

async function walk(page, meta, tag) {
  const record = [];
  const usage = [];
  const find = createFinder(page, usage);
  for (const [name, fn] of flow.steps) {
    const t = Date.now();
    try {
      await fn(page, base, find);
      record.push({ name, ok: true, ms: Date.now() - t, startedAt: t, endedAt: Date.now() });
      if (meta) {   // lab vitals as the page stands after this step; the summary keeps the latest per page
        const v = await vitals.collect(page);
        if (v) (meta.vitals = meta.vitals || []).push({ step: name, ...v });
      }
    }
    catch (e) {
      record.push({ name, ok: false, ms: Date.now() - t, startedAt: t, endedAt: Date.now(), error: String(e.message).split('\n')[0] });
      if (meta) await writeFailureBundle(page, meta, tag, name, e);
      break;
    }
  }
  if (meta && record.length && record.every((r) => r.ok)) {
    // a final reading with a settle, so slow interactions (reported after the next paint) are included
    const v = await vitals.collect(page, 400);
    if (v) (meta.vitals = meta.vitals || []).push({ step: '(end of journey)', ...v });
  }
  if (meta) meta.locators = usage;
  return record;
}

// What an agent (or person) needs to repair a step: the step, what was tried, and what the page shows now.
// It can contain page text, so keep it with the captures and out of version control.
async function writeFailureBundle(page, meta, tag, step, err) {
  const bundle = { flow: flow.id, run: meta.run, cache: meta.cache, step, error: String(err.message).split('\n')[0],
                   tried: err.tried || [], url: page.url() };
  try { bundle.title = await page.title(); } catch (e) { /* page may be closed */ }
  try { bundle.ariaSnapshot = await page.locator('body').ariaSnapshot(); } catch (e) { /* ignore */ }
  fs.writeFileSync(path.join(out, tag + '.failure.json'), JSON.stringify(bundle, null, 2));
  meta.failureBundle = tag + '.failure.json';
}

(async () => {
  let failed = 0;
  for (let n = 1; n <= runs; n++) {
    const tag = tagOf(n);
    const har = path.join(out, tag + '.har');
    const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'sweep-profile-'));
    let ctx;
    const meta = { flow: flow.id, run: n, cache, label: label || undefined, content, base, steps: [], verified: false };
    try {
      if (cache === 'warm') {
        const prime = await chromium.launchPersistentContext(profile, { headless: true });
        await walk(await prime.newPage(), null, tag);
        await prime.close();
        ctx = await chromium.launchPersistentContext(profile, { headless: true, recordHar: { path: har, content } });
      } else {
        const browser = await chromium.launch({ headless: true });
        ctx = await browser.newContext({ recordHar: { path: har, content } });
        ctx._sweepBrowser = browser;
      }
      await ctx.addInitScript(vitals.init);
      const page = await ctx.newPage();
      if (cpuSlowdown > 1) {
        const cdp = await ctx.newCDPSession(page);
        await cdp.send('Emulation.setCPUThrottlingRate', { rate: cpuSlowdown });
      }
      meta.conditions = { cpuSlowdown, userAgent: await page.evaluate(() => navigator.userAgent) };
      meta.steps = await walk(page, meta, tag);
      meta.drifted = (meta.locators || []).some((l) => l.drifted);
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
    console.log(`${tag}: ${meta.verified ? 'verified' : 'FAILED ' + (meta.error || meta.steps.filter((x) => !x.ok).map((x) => x.name + ': ' + x.error).join('; ') || 'a step failed')}`
      + (meta.drifted ? ' (a fallback locator was used: the page has drifted from the flow)' : '')
      + (meta.failureBundle ? ` -> see ${meta.failureBundle}` : ''));
  }
  process.exit(failed ? 1 : 0);
})();
