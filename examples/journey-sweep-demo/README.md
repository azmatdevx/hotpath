# journey-sweep demo

A small web app with planted performance problems, a markdown test case, and a flow for it. It exists to try the `journey-sweep` skills end to end and to show what they produce.

## Files
- `server.js`: the app (port 3918). Planted: three concurrent calls to the same API, a 1.5 s API, a 1.2 MB uncompressed JSON list, a 400 KB uncompressed and uncacheable script, a 900 KB image, eight item calls one by one (N+1), a failing call, a two-hop redirect, and a poll every 1.5 s. Control: a small gzip-compressed script with a fingerprinted name and long-lived cache headers, which must not be flagged.
- `journeys/01-view-orders.md`: the test case, in the markdown shape the skills read.
- `flows/01-view-orders.js`: the flow written from it, with a `verify` check on the end state.

## Run it
```sh
npm i playwright && npx playwright install chromium     # once, outside this repo or in a scratch directory
node server.js &
cd ../.. && node skills/journey-capture/scripts/capture-playwright.js \
  --flow examples/journey-sweep-demo/flows/01-view-orders.js --base http://localhost:3918 \
  --runs 3 --cache cold --out captures/                 # captures/ is ignored by git
python3 skills/har-analysis/scripts/compare_runs.py --journey tc-01-cold --json tc-01-cold.json captures/*-cold-run*.har
python3 skills/sweep-rollup/scripts/rollup.py tc-01-cold.json
```

## What it found
On a real Chromium HAR (Playwright 1.49, 3 cold runs, then 3 warm runs), every planted problem was reported in all three runs of each cache state, and the control script was not:

| Problem | Cold | Warm |
|---|---|---|
| `duplicate-concurrent` on `/api/profile` (3 calls, 0 ms apart) | 3/3 | 3/3 |
| `slow-request` on `/api/orders` (1503 ms, 1502 ms server wait) | 3/3 | 3/3 (1501-1503 ms) |
| `large-payload` and `uncompressed` on `/api/catalog` (1.2 MB) | 3/3 | 3/3 |
| `large-payload`, `uncompressed`, and `not-cacheable` on `/static/vendor.js` (400 KB) | 3/3 | 3/3 |
| `large-payload` on `/img/hero.png` (900 KB) | 3/3 | **gone** (cached for a day) |
| `n-plus-one` on `/api/items/{id}` (8 calls, 520-524 ms cold, 526-567 ms warm) | 3/3 | 3/3 |
| `failed-request` on `/api/recommendations` (500) | 3/3 | 3/3 |
| `redirect` on `/start` (2 hops) | 3/3 | 3/3 |
| `polling` on `/api/notifications` (every 1.5 s) | 3/3 | 3/3 |

The image disappearing when warm, while the script with no cache headers stays, is the cache-state difference the capture skill asks you to record.

## What the real HAR taught
The analyzer's synthetic self-test passed before this run, and the first real HAR still showed three problems with the report, which were fixed:
- Playwright records a decoded size of 0 for the image, so the report said "0 KB decoded". It now says the decoded size was not recorded.
- Tiny repeated bytes printed as "0 KB"; sizes under 1 KB now print in bytes.
- A "Third-party traffic: 0 KB" line printed when there was none.

## Limits
- The app is synthetic and the problems were planted, so finding all of them shows the checks work, not how many real problems the analyzer would catch on a production site.
- One local Chromium on one machine, no throttling, no login, one journey. SSO, MFA, and long journeys are untested.
- Single-user timings only.
