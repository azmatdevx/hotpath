# Locust: validation commands

Verify flags against the Locust version in use.

## Single-user pass
- Headless, one user, short run: `locust -f locustfile.py --headless -u 1 -r 1 -t 30s --host https://target`
- Use `-t` or `--run-time` to bound the run, and read the log output for failures.

## Assertions
- Use `catch_response=True` and mark failures explicitly:
  ```python
  with self.client.get("/path", catch_response=True) as r:
      if "expected text" not in r.text:
          r.failure("content check failed")
  ```
- Without `catch_response`, a 200 with the wrong body counts as success.

## Timing
- Think time: `wait_time = between(1, 3)`. Fixed pacing: `constant_pacing(seconds)`. Fixed rate: `constant_throughput(rate)`.

## Data
- Keep per-user state on `self`, set in `on_start`. Do not use module-level variables for per-user data.
- Load shared data once and hand out items with a thread-safe iterator to avoid collisions.

## Concurrent pass
- `locust -f locustfile.py --headless -u 10 -r 2 -t 1m --csv results`
- `--csv` writes request statistics and failures for analysis.
