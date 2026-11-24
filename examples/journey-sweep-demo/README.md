# journey-sweep demo

A small web app with planted performance problems, a markdown test case, and a flow for it. It exists to try the `journey-sweep` skills end to end and to show what they produce.

## Files
- `server.js`: the app (port 3918). Planted: three concurrent calls to the same API, a 1.5 s API, a 1.2 MB uncompressed JSON list, a 400 KB uncompressed and uncacheable script, a 900 KB image, eight item calls one by one (N+1), a failing call, a two-hop redirect, and a poll every 1.5 s. Control: a small gzip-compressed script with a fingerprinted name and long-lived cache headers, which must not be flagged.
- `journeys/01-view-orders.md`: the test case, in the markdown shape the skills read.
- `flows/01-view-orders.js`: the flow written from it, with a `verify` check on the end state.
- `walks/02-refresh-orders.jsonl` and `flows/02-refresh-orders.from-cli.js`: a walk of `TC-02` recorded with `playwright-cli`, and the flow `cli_to_flow.py` built from it.
- `repairs.md`: the repair log from the test of `flow-repair`.
- `journeys/02-refresh-orders.md` and `flows/02-refresh-orders.js`: a journey that clicks a button whose id and class change on every page load.

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

## Dynamic ids and failed steps
The Refresh orders button gets a new random id on every load. Three flows for `TC-02` were run once each (cold) on Playwright 1.49:

| Flow | Locator | Result |
|---|---|---|
| Stable | `find` with role and accessible name first, text second | verified, primary locator used, no drift |
| Stale id first | a recorded id (`#btn-1a2b3c4d`) as candidate 0, role and name as candidate 1 | verified, recorded `drifted: true` (candidate 1 used) |
| Brittle | only the recorded id | failed at the click step, exit 1, and wrote a failure bundle |

The failure bundle's accessibility snapshot showed `button "Refresh orders"`, which is what `flow-repair` needs to find the element by meaning. The repair loop was run once end to end on this app (see `repairs.md`): three failed cold runs of the brittle flow wrote bundles, the flow was repaired from the snapshot, and 6 fresh runs (3 cold, 3 warm) all verified. I performed that repair following `flow-repair`, in a test of the skill, so it shows the loop works on this case, not that an unattended agent repairs real apps reliably. A failed run's HAR is refused downstream, as with a failed `verify`.

## Flow from a `playwright-cli` walk
`TC-02` was walked once with `playwright-cli` (open, find, snapshot, click by ref), each step recorded with `cli_to_flow.py record`, and the flow built with `cli_to_flow.py build`. The converter's checks earned their keep on the first try: I had recorded "Wait for the orders count" while the test case says "Wait for the orders count to appear", and the build warned about both the unmatched recorded step and the unrecorded test case step, so I re-walked it with the test case's wording. The rebuilt flow verified in 3 of 3 cold runs, and the same flow built with a wrong expected text ("4 orders") failed `verify`, as it should. The click step came out as `getByRole('button', { name: 'Refresh orders' })`, which does not depend on the page's random button id.

This was one small journey walked by me, not an unattended agent.

## Bug drafts
`perf-bug-writing/scripts/draft_bugs.py` turns the rollup into one markdown draft per request (9 for journey 1), with the evidence copied from the analyzer, two lines left for impact and proposed severity, and an engineer verification checklist. `--check` fails until those lines are filled. Nothing is filed; engineers verify and log each draft.

## What the real HAR taught
The analyzer's synthetic self-test passed before these runs, and real HARs still showed four problems, which were fixed:
- A request that repeats inside one HAR (journey 2 calls `/api/orders` twice) was counted once per request instead of once per run, so a consistent finding showed as `6/3 runs` and landed under intermittent. It now counts once per run, and the self-test covers it.
- Playwright records a decoded size of 0 for the image, so the report said "0 KB decoded". It now says the decoded size was not recorded.
- Tiny repeated bytes printed as "0 KB"; sizes under 1 KB now print in bytes.
- A "Third-party traffic: 0 KB" line printed when there was none.

## Limits
- The app is synthetic and the problems were planted, so finding all of them shows the checks work, not how many real problems the analyzer would catch on a production site.
- One local Chromium on one machine, no throttling, no login, one journey. SSO, MFA, and long journeys are untested.
- Single-user timings only.
