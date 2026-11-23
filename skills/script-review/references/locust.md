# Locust script review

Verify details against the Locust version in use.

## What to look for

- **Responses never marked failed.** Without `catch_response=True` and an explicit `failure()`, a 200 with the wrong body counts as success.
- **Dynamic URLs without `name=`.** Each unique URL becomes its own statistics row. Pass a stable `name`.
- **Blocking calls.** `time.sleep()` and other blocking code stall every user on that worker. Use `wait_time` for think time, or `gevent.sleep`.
- **Bypassing the client.** Using the `requests` library directly instead of `self.client` means those calls are not measured or monkey-patched consistently.
- **CPU-heavy code in tasks.** Heavy parsing or computation makes the generator the limiter. Consider `FastHttpUser`, or move the work out of the hot path.
- **Module-level shared state.** Per-user data kept in module variables is shared across users.
- **Unhandled response errors.** `response.json()["key"]` raises on error responses and hides the real failure. Validate status first.
- **Data exhaustion.** Queues or iterators that raise or wrap when data runs out, without a clear failure.
- **Think time.** `wait_time` missing, or a constant where variation is intended.
- **Task weights.** Weights that do not match the intended transaction mix.
- **Authentication.** Logging in on every task instead of once in `on_start` (or the reverse, when the model requires it).
- **Hard-coded config.** Host and credentials in code instead of environment or arguments.
- **Distributed readiness.** Data splitting and worker count handled (see `distributed-load-generation`).
