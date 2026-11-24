# sweep demo

A small web app with planted performance problems, a markdown test case, and a flow for it. It exists to try the sweep-mode skills end to end and to show what they produce.

## Files
- `server.js`: the app (port 3918). Planted: three concurrent calls to the same API, a 1.5 s API, a 1.2 MB uncompressed JSON list, a 400 KB uncompressed and uncacheable script, a 900 KB image, eight item calls one by one (N+1), a failing call, a two-hop redirect, and a poll every 1.5 s. Control: a small gzip-compressed script with a fingerprinted name and long-lived cache headers, which must not be flagged.
- `journeys/01-view-orders.md`: the test case, in the markdown shape the skills read.
- `flows/01-view-orders.js`: the flow written from it, with a `verify` check on the end state.
- `journeys/03-promo-page.md` and `flows/03-promo-page.js`: a page with planted web vitals problems (`/promo` in `server.js`): a hero image delayed 3 s (LCP), a banner injected above the content at 1 s (CLS), a 500 ms blocking script (TBT), and a click handler that blocks for 400 ms (interaction latency).
- `journeys/04-sign-in.md` and `flows/04-sign-in.js`: a sign-in with a CSRF token in the page, a session cookie, a token returned by the sign-in call and sent as a bearer token, and a client timestamp (for trying `script-correlation`). The user comes from `TEST_USER`.
- `walks/02-refresh-orders.jsonl` and `flows/02-refresh-orders.from-cli.js`: a walk of `TC-02` recorded with `playwright-cli`, and the flow `cli_to_flow.py` built from it.
- `repairs.md`: the repair log from the test of `flow-repair`.
- `journeys/02-refresh-orders.md` and `flows/02-refresh-orders.js`: a journey that clicks a button whose id and class change on every page load.

## Run it
```sh
npm i playwright && npx playwright install chromium     # once, outside this repo or in a scratch directory
node server.js &
cd ../.. && node skills/journey-capture/scripts/capture-playwright.js \
  --flow examples/sweep-demo/flows/01-view-orders.js --base http://localhost:3918 \
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

## Correlation on real browser HARs
`TC-04` was recorded twice with `--content embed`, once as `alice` and once as `bobby` (Playwright 1.49), and the pair given to `har_correlate.py`. It found every dynamic value, with the right source and use, and masked them in its output:

| Value | Reported as | Source | Used in |
|---|---|---|---|
| CSRF token | correlation (confirmed) | `GET /account`: HTML `input[name=csrf]` | `POST /api/signin` form field `csrf` |
| Bearer token | correlation (confirmed) | `POST /api/signin`: JSON `$.token` | `GET /api/me` header `authorization` |
| Session cookie | cookie (confirmed) | `GET /account`: `Set-Cookie sid` | `POST /api/signin` and `GET /api/me` |
| Username | parameter | no earlier response contains it | `POST /api/signin` form field `username` |
| `ts` | generated (timestamp) | none | `GET /api/me` query |

`har_transactions.py` grouped the same HAR by the test case's steps: `TC04_01_open_the_account_page` holds `GET /account`, `TC04_03_click_sign_in` holds `POST /api/signin` and `GET /api/me`, and the two steps that make no requests are listed as empty. These are the transaction names and the correlation list a k6 or JMeter script would be built from.

## An agent run of `script-from-test-case`
An agent followed the `perf-mode` playbook on `TC-04`: author a flow from the test case, capture it as `alice` and `bobby` with bodies, group the requests into transactions, find the correlations, write a k6 script, validate it, and deliver it on a feature branch of a scratch repository (the remote was a local bare repository, and with no PR tool it wrote the PR text to a file). It took four attempts; the last cost about $0.79 and 81 turns.

What the delivered work looked like, which I checked myself:
- **Delivery:** one commit on `perf/tc04-sign-in-initial-script` adding `k6/tc04-sign-in.js`; `main` on the remote unchanged; no HAR in the commit; the HARs (3 requests each, all with bodies) outside the repository; a 31-line PR text with the playbook's headings, including what was not covered.
- **The script:** transactions named after the test case steps (`01_open_the_account_page`, `02_click_sign_in`); the CSRF token extracted from the HTML input and the bearer token from the JSON response, the cookie left to k6's jar, the client timestamp generated; configuration from `BASE_URL` and `TEST_USER` only; content checks that include "Welcome <user>". None of the six token-like values from the captures appears in the script or the commit.
- **Validation, re-run by me on the real demo app:** 1 user for 3 iterations passed 21 of 21 checks; 5 users with both accounts passed 175 of 175 with no failed requests. A copy expecting the wrong name failed with exit code 99, and the script without `BASE_URL` failed with exit code 107.

What the four attempts showed about the skills (all fixed, none re-run since the last two):
1. **No shell access outside the repo** (a test-setup problem, solved with working directories).
2. **Shell variable prefixes and `curl` rejected by the allowlist.** The one-command-per-call rule lived only in the worker rules, so both modes now carry it, with "stop on a denied command".
3. **The capture command set the account with a shell prefix** (`TEST_USER=alice node ...`), which allowlists reject. The capture script now takes `--env TEST_USER=alice`.
4. **The hard rule was not followed in spirit.** With every detail in the prompt, the agent contacted the target without writing the goal, target, permission, and tool back first. The last run wrote only "I'll read the playbook before contacting anything", which is the right order but not the content. The rule now says to begin with `Restating:` and give the four items, so it can be checked in a transcript. That change has not been tested.
- **Smaller:** the agent ran two stub servers to show a check fails without breaking the target, which is good practice but left background processes (none were still running). The playbook now says to name a stub and stop it. `playwright-cli` left a `.playwright-cli/` folder in the repository; the reference now says to keep it out of the diff.

What this does not show: one journey with three requests, a local app, one model, and a PR that was only written as text. The correlation step was easy here because the demo has one CSRF field and one token. Drift (`repair-a-script`) and `open-a-pr` against a real PR tool were not exercised.

## Web vitals
`TC-03` was captured 3 times cold (Playwright 1.49, Chromium 131 headless, no throttling, a laptop that was not idle) and summarised with `vitals_summary.py`:

| Metric | Median | Range over 3 runs | Limit | Planted |
|---|---|---|---|---|
| LCP | 3030 ms | 3028-3082 ms | 2500 ms | a 3 s image delay |
| CLS | 0.2 | 0.2-0.2 | 0.1 | a 260 px banner at 1 s |
| Slowest interaction | 432 ms | 424-440 ms | 200 ms | a 400 ms click handler |
| TBT | 799 ms | 799-802 ms | 200 ms | 450 ms + 350 ms of long tasks |
| TTFB | 2 ms | 1-29 ms | 800 ms | none (control) |

All four planted problems were over their limit in 3 of 3 runs, and the control was not flagged. Building this exposed three mistakes in my first attempt, all fixed:
- A 1x1 PNG as the hero image never counted for LCP, because Chrome leaves out low-entropy images. The demo now serves a noise image.
- The slow interaction was missed at first. The browser reports an interaction's timing only after the next paint, so the capture now takes one final reading with a 400 ms settle after the last step.
- The first banner was too small to push CLS over its limit.

These are lab values from one machine; they show the capture and summary work, not what real users would see.

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

## Agent runs
The three reference agents in `examples/agents/claude-code/` ran the sweep over both journeys twice, headless, each time authoring the flows from the test cases (through `cli_to_flow.py`), capturing 3 cold runs per journey, analysing, drafting bugs, and having the drafts reviewed. Nothing was filed. What the runs showed:

- **It worked, and the numbers held.** All 12 captures verified, with no drift. The 8 drafts agreed with the earlier hand-run analysis, and the orchestrator's claims matched the run records.
- **Run-to-run spread is real.** `/api/orders` read 1503-1965 ms in the first run and 1503-1505 ms in the second, on an unchanged app: one slow call in one run. The reviewer in the first run flagged that the high end came from a single journey, which is the reason for at least 3 runs and for reporting ranges.
- **Five defects in my agents and skills, found by watching them:**
  1. An allowlist rejected a chained command (`mkdir; python3 | tail; cd …`), and the orchestrator stopped. The agents now run one command per call.
  2. `curl` was denied and nothing said how else to check the app was up. The orchestrator now has a Python one-liner and `git check-ignore` is allowed.
  3. Drafts said "the worker agreed" and "I judged" (6 of 8 drafts). The rules now say to write for the engineer; the second run had none.
  4. The reviewer said CHANGE on every draft, and nothing acted on it. The orchestrator now makes one revision pass on the text it wrote, never on evidence, and reports what it changed.
  5. A worker's second capture overwrote the first run's HAR, and the sweep only recovered because the worker noticed and recaptured. The capture script now refuses to overwrite and tells you to delete discarded captures.
- **Still open:**
  - The reviewer said CHANGE on all 8 drafts in the second run too. Part of it was substance and part wording, which is why it now separates BLOCKING from NIT. That change is untested.
  - The reviewer said it could not read the rubric or the HARs, and tried to search the filesystem. The orchestrator now passes absolute paths and the reviewer says CANNOT CHECK instead. Also untested.
  - In the revision pass, the orchestrator lowered BUG-03 (three concurrent identical calls on every load) from Medium to Low, against the rubric row for a duplicate on every visit, giving its own reason. The reviewer disagreed. The draft shows the reasoning, so the engineer can see it, but it is the kind of judgment the trust ladder says a person should make.

### Third run, after the fixes (`sweep-mode`, three journeys)
The orchestrator ran the sweep over `TC-01` to `TC-03` through `sweep-mode` (about $2.07, 58 orchestrator turns, 6 workers and 2 reviews). All 9 captures verified, with no repairs or drift, and it wrote 10 drafts that passed `--check`. Against the second run:
- **The reviewer is usable now.** It said OK on 9 of 10 drafts with nits listed, against CHANGE on all 8 before, because it separates BLOCKING issues from NITs. Its first round still caught two wrong facts in text the orchestrator had written (an LCP range off by two milliseconds, and the wrong step blamed for a 3 s page open), and the orchestrator fixed both. I checked the step timings: "Open the promo page" took 3015-3033 ms in the run records, so the correction was right.
- **No agent chatter in any draft**, and the threshold values were written out. The reviewer read the rubric and the evidence, so `CANNOT CHECK` never fired.
- **A new finding:** the slow hero image on `/promo` came out as its own draft (3003-3005 ms), next to the vitals draft for the same page.
- **What it got wrong, fixed afterwards:**
  - A `[]` vitals file from `vitals_summary.py` means no metric was over its limit, but the orchestrator read it as a failure and regenerated it. The script now says so, and the skill documents it.
  - A walk failed once with a 15 s timeout while two authoring workers ran at the same time. The playbook now treats a failure during parallel authoring as inconclusive until re-run alone.
  - A worker left a dry-run script beside the flows. Workers now keep scratch files in a `scratch/` folder and list them.
  - The generated drafts said "agreed" limits even when the analyzer defaults were used. The wording now says "the limit used".
  - The one blocking note left on a draft was in a sentence the orchestrator added in its revision pass. The playbook now allows a second pass for BLOCKING issues only.
- **Still a judgment, not a rule:** BUG-03 (three identical calls on every load) is Low with a stated reason, though the rubric row for a duplicate on every visit says Medium. The reviewer accepted it this time. A person should decide.

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
