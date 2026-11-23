# Locust: distributed setup

Verify flags against the Locust version in use.

- **Master and workers.** Start one master with `locust -f locustfile.py --master`, and workers with `locust -f locustfile.py --worker --master-host=<host>`.
- The master coordinates and aggregates but does not generate load. For headless runs add `--headless --expect-workers N -u <users> -r <rate> -t <time>`.
- **One worker process per CPU core.** Python workers use a single core each, so run as many workers as cores on each generator machine.
- Users are divided across workers, so `-u` is the total, not per worker.
- `FastHttpUser` raises per-core throughput when generator CPU is the limit.
- **Data.** Split test data by worker (use the worker index available from the runner) so workers do not reuse rows.
- Use the same Python, Locust version, and locustfile on every machine. Open the master's coordination ports between machines.
