# Gatling: validation commands and constructs

Verify names and syntax against the Gatling version in use.

## Single-user pass
- Use an injection profile of one user: `setUp(scn.inject(atOnceUsers(1)))`.
- To see every request and response, set the Gatling HTTP engine loggers to `TRACE` in `logback.xml` for the validation run, and revert afterwards.

## Checks and assertions
- Per-request checks fail the request on mismatch: `.check(status.is(200), substring("Order confirmed"))`.
- A check that finds nothing fails the request. Use `.optional` only when absence is expected.
- Whole-simulation pass/fail conditions:
  ```scala
  setUp(scn.inject(atOnceUsers(1)))
    .assertions(
      global.failedRequests.count.is(0),
      global.responseTime.percentile(95).lt(2000)
    )
  ```

## Timing
- Think time: `.pause(1, 3)`. Pacing: `.pace(...)`. Throttle with `.throttle(...)`.

## Data
- Feeders: `csv("users.csv").circular` or `.queue` or `.random`. Choose the strategy deliberately so users do not collide or run out of data.

## Concurrent pass and load run
- Use a small injection (for example `rampUsers(10).during(30)`) before the real profile.
- Remove verbose logging before the real run.
- Reports are generated from `simulation.log` at the end of the run.
