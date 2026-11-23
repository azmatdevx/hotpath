# Locust: parameterization

Verify APIs against the Locust version in use.

## Loading data
```python
import csv, itertools, queue
from locust import HttpUser, task, events

users = queue.Queue()
with open("users.csv") as f:
    for row in csv.DictReader(f):
        users.put(row)

class WebUser(HttpUser):
    def on_start(self):
        self.creds = users.get_nowait()   # one row per user; raises when exhausted
```

## Notes
- A shared `queue.Queue` gives each user a unique row and fails loudly when data runs out. Use `itertools.cycle` over a list when reuse is acceptable.
- Keep per-user data on `self`, not at module level.
- In distributed runs, split rows by worker so workers do not reuse data: use the worker index from the runner (for example `environment.runner.worker_index`, or a `--worker-index`-style custom argument) to select a slice.
- Use the `test_start` event for one-time setup and `test_stop` for cleanup.
- Use libraries like `faker` or `uuid` for generated values. Combine with a user ID to keep unique fields unique.
- Read secrets from environment variables.
