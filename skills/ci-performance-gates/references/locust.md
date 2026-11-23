# Locust: CI pass/fail

Verify flags and APIs against the Locust version in use.

- Run headless with a bounded duration: `locust -f locustfile.py --headless -u 50 -r 5 -t 5m --csv results`.
- Locust returns a non-zero exit code when requests fail, unless you override it with `--exit-code-on-error`.
- For latency or percentile gates, set the exit code yourself from the `quitting` event:
  ```python
  from locust import events

  @events.quitting.add_listener
  def check_thresholds(environment, **kw):
      stats = environment.stats.total
      if stats.fail_ratio > 0.01:
          environment.process_exit_code = 1
      elif stats.get_response_time_percentile(0.95) > 2000:
          environment.process_exit_code = 1
  ```
- Save `--csv` output as artifacts and compare with a stored baseline in a script for regression gates.
- Percentiles from `stats.total` combine all requests. Check per-transaction stats for per-step budgets.
