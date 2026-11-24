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
| Runs | 3 repeat runs of `steps` with `preAllocatedVUs=500`, an earlier run with 100, and 3 runs of the `knee` scenario (60, 65, 70, 75/s) |
| Evidence | k6 raw CSV, target `/metrics` once per second, CPU of k6, target, and machine every ~2 s |

## Skills used

`perf-mode` with the script-building skills (the playbook was then called `script-a-flow`), then `script-authoring`, `script-correlation`, `script-parameterization`, `script-validation`, `script-review`, `load-test-design` (arithmetic), `load-run-checklist`, `results-sanity-check`, and `results-analysis`.

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

Verdict: **pass at 20, 40, and 60/s; fail at 80/s.** A second set of runs and a time-resolved view narrowed the break to between 60 and 65/s (below).

## Narrowing the knee (second set of runs)

Prediction written before the runs: 60/s passes, 65/s sits at about 97% slot use with checkout p95 near or over 400 ms, and 70 and 75/s fail with searches starting to return empty.
Three runs of the `knee` scenario, otherwise identical (median [min-max]):

| Metric | 60/s | 65/s | 70/s | 75/s |
|---|---|---|---|---|
| Achieved iterations/s | 60.0 | 65.0 | 70.0 | 75.0 |
| Dropped iterations | 0 | 0 | 0 | 0 |
| Search p95 (ms) | 98 [90-100] | 232 [196-253] | 820 [801-823] | 822 [813-828] |
| Checkout p95 (ms) | 188 [176-192] | 454 [393-498] | 1647 [1606-1648] | 1757 [1733-1780] |
| Searches returning 200 with no items | 0% | 0% | 28% [20-29] | 57% [55-60] |
| DB slots in use (avg, of 8) | 7.4 | 8.0 | 8.0 | 8.0 |
| DB queue (avg) | 5 | 30 [21-33] | 189 [172-190] | 203 [201-204] |
| Orders completed/s | 60.0 | 64.2 | 68.3 | 75.0 |
| k6 CPU avg / max (% of one core) | 14 / 19 | 14 / 19 | 15 / 20 | 16 / 21 |

The prediction held. Per run at the boundary:

| Run | 60/s search, checkout p95 | 65/s search, checkout p95 | 65/s result |
|---|---|---|---|
| 1 | 100, 192 ms | 196, 393 ms | passes on the window average only |
| 2 | 98, 188 ms | 232, 454 ms | fail both |
| 3 | 90, 176 ms | 253, 498 ms | fail both |

On the window averages, 60/s met both SLAs in all three runs and 65/s in one of three. The time-resolved view below shows that even that one pass does not hold.
The capacity arithmetic also held under degradation: with 28% of searches degraded, capacity is about 71.7/s (offered 70, orders 68.3/s), and with 57% degraded about 77.7/s (offered 75, orders 75.0/s).

### Time-resolved view: is each window steady?

A first-half versus second-half comparison of each 45 s window (checkout p95 ms, queue average), from `timeseries.py`:

| Step | Runs | First half | Second half | Reading |
|---|---|---|---|---|
| 60/s (knee runs) | 3 | 188-197 ms, queue 4-5 | 170-194 ms, queue 4-5 | flat |
| 60/s (steps runs) | 3 | 144-204 ms, queue 2-4 | 171-256 ms, queue 5-6 | slight rise, worst 256 ms |
| 65/s | 3 | 339-386 ms, queue 17-24 | 428-514 ms, queue 25-42 | **rising in every run** |
| 70/s, 75/s | 3 | queue 153-203 | queue 190-206 | stable at the degraded equilibrium |
| 80/s | 3 | 1810-1908 ms, queue 207-213 | 1742-1821 ms, queue 208-213 | stable |

In knee run 2, queue and latency climb through the 65/s hold:

| Seconds | 70-80 | 80-90 | 90-100 | 100-110 | 110-120 |
|---|---|---|---|---|---|
| Checkout p95 (ms) | 334 | 405 | 404 | 449 | 523 |
| Queue average | 20 | 28 | 26 | 35 | 51 |

So at 65/s the queue is still growing when the hold ends. The run that looked like a narrow pass was already over both SLAs in its second half (checkout 428 ms, search 219 ms). The reported 65/s numbers are snapshots of a rising queue, and a longer hold would likely read worse.
60/s met both SLAs in every half-window of all six runs (worst checkout p95 256 ms, worst search p95 126 ms).
The sustainable SLA capacity from these runs is between 60 and 65 iterations/s, against 66.7 from the slot arithmetic. Close to saturation, a few iterations per second separate a stable system from a climbing queue. The 5-minute holds below test that directly.

### Five-minute holds at 62/s and 65/s

The `hold` scenario ramps to the rate over 30 s and holds it for 5 minutes. Three runs each, `PREALLOC=500`, server restarted between runs, no dropped iterations in any run, k6 at 13-15% of one core. Per-minute view from `holdview.py`, excluding the 30 s ramp.

**62/s met both SLAs in every one of the 15 minutes (3 runs x 5):**

| Run | Search p95 (ms) | Checkout p95 (ms) | Queue average | Queue max |
|---|---|---|---|---|
| 1 | 100-112 | 194-223 | 5-9 | 38 |
| 2 | 114-138 | 224-268 | 7-10 | 33 |
| 3 | 111-133 | 223-261 | 8-11 | 40 |

No search came back empty and every check passed. The queue stayed in single digits on average. Within a run the minute-to-minute range was 194-223 ms in run 1, 224-268 ms in run 2 and 223-261 ms in run 3, with no sustained climb. Runs 2 and 3 were slower than run 1 throughout, so the run-to-run spread (up to about 70 ms of checkout p95 in the same minute) is as large as anything within a run.

**65/s climbed until the queue reached its limit, in all three runs:**

| Run | Checkout p95 first minute -> last minute (ms) | Queue average first -> last | Empty searches, last minute |
|---|---|---|---|
| 1 | 528 -> 1570 | 36 -> 186 | 2% |
| 2 | 490 -> 1557 | 31 -> 184 | 3% |
| 3 | 646 -> 1586 | 47 -> 187 | 5% |

- **Crossing the SLAs:** checkout p95 first passed 400 ms in the 10 s bucket starting at 50 s (runs 1 and 3) or 60 s (run 2), and search p95 passed 200 ms in the same bucket as checkout. That is 20-40 s after the ramp ended.
- **Settling:** the queue stopped climbing between about 3 and 5 minutes in, pinned just under the 200 trigger (maximum 200-206). Last-minute search p95 was 790-799 ms and checkout p95 1557-1586 ms, 4 times the checkout SLA.
- **Why it stops there:** this is the degraded mode from finding 4. A few percent of searches skip the database, which is enough to hold the queue at the trigger instead of letting it grow.
- **The threshold gap:** checks passed at 99.71-99.91% and `http_req_failed` was 0%, so the script's thresholds (`checks` above 99%, errors below 1%) passed and k6 exited 0 on all three 65/s runs, even though latency was 2-4 times over the SLAs. The script has no latency threshold. Without an SLA threshold the exit code would not have flagged these runs.
- **Server-side confirmation:** orders created matched iterations exactly in five runs. In 62/s run 1 the target recorded 19,543 orders for 19,544 iterations. I did not investigate the one-order difference; the final `/metrics` sample may have been taken before the last order completed.

**Verdict:** sustainable capacity under these SLAs is at least 62/s and below 65/s, within 7% of the arithmetic ceiling of 66.7. I did not test 63 or 64. The earlier suspicion that 65/s would read worse over a longer hold held: it climbed from 490-646 ms in the first minute to about 1.57 s of checkout p95 in the last.


## Findings

1. **The limiter is the database slot pool.** Slots in use rise to 7.3 of 8 at 60/s and 8.0 at 80/s while the target uses about 5% of a core and k6 at most 22%. Queue wait of about 400 ms per query explains the 80/s latencies: login and cart measured about 400 ms, search (2 queries) about 800 ms, and checkout (4 queries) about 1.6 to 1.8 s.
2. **A 0% HTTP error rate hid a failing system.** Above the queue limit the target answers `/search` with 200 and no items, without touching the database. k6 reported `http_req_failed` at 0% for the whole run. Only the content check `search has items` caught it, failing for 75% of searches at 80/s. A status-only script would have passed.
3. **Degraded replies distorted the latency numbers.** In the first run, at 80/s, they returned in under 10 ms and pulled the all-responses search p50 down to about 315 ms while genuine searches ran at about 756 ms p50. The failing share (1,611 of 3,352) matched the fast share exactly. I did not repeat that split for the three repeat runs.
4. **The degraded mode flattens the queue.** Skipping 2 of 8 queries for 75% of iterations raises capacity to about 82 iterations/s, which matches the measured 79.7 iterations/s and 78.4 orders/s, and keeps the queue hovering near its trigger of 200.
5. **The knee is sensitive, and a window average can hide it.** (See the time-resolved view above.) Checkout p95 at 60/s ranged from 162 to 219 ms across the first three runs, against a 3 ms spread at 20 and 40/s, and at 65/s it ranged from 393 to 498 ms. In the second set the machine was quieter (12 to 13% busy on average) and the spread at 60/s narrowed to 176 to 192 ms, which is consistent with machine noise adding to the spread but does not prove it, since the runs differ in other ways. At 65/s the run with the highest starting load average was the one that passed, so noise does not explain that spread.

## What the first run taught

The first run used `preAllocatedVUs=100`. At 80/s k6 dropped 199 iterations and offered only 75.3/s, and 48% of searches failed. Raising the pool to 500 removed the drops, offered 79.7/s, and moved the failing share to 75%.
The earlier 48% was an artefact of generator-side shortage, not a property of the target.
The generator CPU samples added later are what allowed the repeat to rule out the generator as the limiter.

## Limits of this result

- One laptop ran generator, target, and samplers, and it was never idle. Do not read these numbers as capacity.
- The stepped runs measure 45 s windows, which is too short for slow effects such as memory growth. The 5-minute holds are longer but cover only 62/s and 65/s.
- The SLAs are assumptions made for the exercise, not requirements.
- Between 62 and 65/s was not tested (63 and 64 would narrow it). Holds were 5 minutes, which is enough to see the queue settle in this target but not for slow effects such as memory growth or connection leaks.
- The 62/s runs differ from one another by up to about 70 ms of checkout p95 in the same minute with no change in setup, so a difference of that size between runs is noise.
- Machine CPU and the target's `/metrics` are sampled every 1 to 2 s, so alignment with client events is approximate.

## Reproduce

```sh
cd ../demo-shop
node server.js &                                   # target on :3917
python3 sample-metrics.py server.csv &             # server-side samples
python3 sample-procs.py procs.csv &                # generator, target, and machine CPU
k6 run -e SCENARIO=steps -e PREALLOC=500 --out csv=raw.csv checkout.k6.js   # or SCENARIO=knee, or SCENARIO=hold -e RATE=62
python3 analyze.py raw.csv server.csv procs.csv    # one run (STEPS=60,65,70,75 for the knee scenario)
python3 holdview.py raw.csv server.csv procs.csv   # per-minute view of a hold run
python3 compare-runs.py DIR PREFIX N               # N runs named PREFIX1-raw.csv, PREFIX1-server.csv, PREFIX1-procs.csv, ...
```

Raw result files are large and not committed.
