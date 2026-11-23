# Case study: stepped load test of the demo shop

A worked run of the `perf-mode` playbooks against the local synthetic target in [`../demo-shop`](../demo-shop), using k6.
The target is not a real system, so the numbers show the method working, not any real capacity.

## Question

At what arrival rate does the checkout journey stop meeting its SLAs, and what limits it?

Assumed SLAs (set for the exercise): search p95 under 200 ms, checkout p95 under 400 ms, errors under 1%, and every checkout must actually confirm an order.

## Setup

| | |
|---|---|
| Target | `demo-shop`: in-memory Node app, simulated database of 8 slots at 15 ms per query |
| Journey | login (CSRF field plus session cookie), search, add to cart, checkout; 8 queries per iteration |
| Tool | k6 v1.0.0 (`checkout.k6.js`, scenario `steps`) |
| Workload | open model, arrival rate stepped 20, 40, 60, 80 iterations/s; 50 s hold per step, first 5 s of each hold excluded |
| Machine | one 8-core macOS laptop running generator, target, and samplers; not idle (13 to 29% busy on average per step) |
| Runs | 3 repeat runs with `preAllocatedVUs=500`, plus an earlier run with 100 |
| Evidence | k6 raw CSV, target `/metrics` once per second, CPU of k6, target, and machine every ~2 s |

## Skills used

`perf-mode` with `script-a-flow`, then `script-authoring`, `script-correlation`, `script-parameterization`, `script-validation`, `script-review`, `load-test-design` (arithmetic), `load-run-checklist`, `results-sanity-check`, and `results-analysis`.

## Method notes

- **Capture and correlation.** The flow was run twice as different users and the captures diffed. The dynamic values found were the `sid` cookie, the `csrf` hidden field, the bearer `token`, and the single-use `cartId`. Each is extracted from the response that produces it.
- **Validation.** A single-user run passed 7 of 7 content checks. A 5-user, 3-iteration run passed 105 of 105, and the server's order counter showed 15 orders for 15 iterations.
- **Workload arithmetic.** Each iteration makes 8 queries, so 8 slots / 15 ms / 8 queries is about 66.7 iterations/s before degradation.

## Results (3 runs, median [min-max])

| Metric | 20/s | 40/s | 60/s | 80/s |
|---|---|---|---|---|
| Achieved iterations/s | 20.0 | 40.0 | 60.0 | 79.7 [79.3-80.0] |
| Dropped iterations | 0 | 0 | 0 | 0 |
| Search p95 (ms) | 34 [33-34] | 38 [38-39] | 102 [83-113] | 824 [812-833] |
| Checkout p95 (ms) | 67 [65-67] | 73 [72-74] | 194 [162-219] | 1842 [1781-1874] |
| Searches returning 200 with no items | 0% | 0% | 0% | 75% [71-79] |
| DB slots in use (avg, of 8) | 2.6 | 4.9 | 7.3 | 8.0 |
| DB queue (avg) | 0 | 0 | 4 | 210 |
| Orders completed/s | 20.0 | 40.2 | 59.8 | 78.4 |
| k6 CPU avg (% of one core) | 7 | 11 | 13 | 16 |
| Target CPU avg (% of one core) | 4 | 4 | 4 | 5 |

Verdict: **pass at 20, 40, and 60/s; fail at 80/s.** The SLA break lies between 60 and 80/s and was not narrowed further.

## Findings

1. **The limiter is the database slot pool.** Slots in use rise to 7.3 of 8 at 60/s and 8.0 at 80/s while the target uses about 5% of a core and k6 at most 22%. Queue wait of about 400 ms per query explains the 80/s latencies: login and cart measured about 400 ms, search (2 queries) about 800 ms, and checkout (4 queries) about 1.6 to 1.8 s.
2. **A 0% HTTP error rate hid a failing system.** Above the queue limit the target answers `/search` with 200 and no items, without touching the database. k6 reported `http_req_failed` at 0% for the whole run. Only the content check `search has items` caught it, failing for 75% of searches at 80/s. A status-only script would have passed.
3. **Degraded replies distorted the latency numbers.** In the first run, at 80/s, they returned in under 10 ms and pulled the all-responses search p50 down to about 315 ms while genuine searches ran at about 756 ms p50. The failing share (1,611 of 3,352) matched the fast share exactly. I did not repeat that split for the three repeat runs.
4. **The degraded mode flattens the queue.** Skipping 2 of 8 queries for 75% of iterations raises capacity to about 82 iterations/s, which matches the measured 79.7 iterations/s and 78.4 orders/s, and keeps the queue hovering near its trigger of 200.
5. **The knee is sensitive.** Checkout p95 at 60/s ranged from 162 to 219 ms across runs, against a 3 ms spread at 20 and 40/s. Run 2, the noisiest, was worst, but the calmest run was not best, so machine noise is a possible but unproven cause.

## What the first run taught

The first run used `preAllocatedVUs=100`. At 80/s k6 dropped 199 iterations and offered only 75.3/s, and 48% of searches failed. Raising the pool to 500 removed the drops, offered 79.7/s, and moved the failing share to 75%.
The earlier 48% was an artefact of generator-side shortage, not a property of the target.
The generator CPU samples added later are what allowed the repeat to rule out the generator as the limiter.

## Limits of this result

- One laptop ran generator, target, and samplers, and it was never idle. Do not read these numbers as capacity.
- Each measured window is 45 s, which is too short for slow effects such as memory growth.
- The SLAs are assumptions made for the exercise, not requirements.
- The step between 60 and 80/s was not tested.
- Machine CPU and the target's `/metrics` are sampled every 1 to 2 s, so alignment with client events is approximate.

## Reproduce

```sh
cd ../demo-shop
node server.js &                                   # target on :3917
python3 sample-metrics.py server.csv &             # server-side samples
python3 sample-procs.py procs.csv &                # generator, target, and machine CPU
k6 run -e SCENARIO=steps -e PREALLOC=500 --out csv=raw.csv checkout.k6.js
python3 analyze.py raw.csv server.csv procs.csv    # one run
python3 compare-runs.py DIR PREFIX N               # N runs named PREFIX1-raw.csv, PREFIX1-server.csv, PREFIX1-procs.csv, ...
```

Raw result files are large and not committed.
