# Locust: authoring structure

Verify APIs against the Locust version in use.

## Suggested structure
```python
import os
from locust import HttpUser, SequentialTaskSet, task, between

class Checkout(SequentialTaskSet):
    @task
    def login(self):
        with self.client.post("/login", json=..., name="01_login", catch_response=True) as r:
            ...

    @task
    def search(self):
        self.client.get("/search?q=...", name="02_search")

class WebUser(HttpUser):
    host = os.environ.get("BASE_URL")
    wait_time = between(1, 3)
    tasks = [Checkout]
```

## Notes
- Use `SequentialTaskSet` for ordered journeys, and `@task(weight)` or multiple user classes for a transaction mix.
- Pass `name=` to group requests with dynamic paths (for example `name="/item/[id]"`) so results aggregate. Use stable transaction names.
- Keep per-user state on `self`, set in `on_start`.
- Use `FastHttpUser` when generator CPU limits throughput and you do not need `requests` features.
- Set the workload on the command line or in config (`-u`, `-r`, `-t`), or with a `LoadTestShape` class for custom profiles. Keep it separate from journey logic.
- To report a multi-request step as one transaction, fire a custom event with `self.environment.events.request.fire(...)`.
