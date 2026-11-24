# Datadog

Not run against a real account; check the metric names and the API version.

Export a series with the metrics query API (API and application keys from the environment, never in a file):
```
GET https://api.datadoghq.com/api/v1/query?from=<epoch s>&to=<epoch s>&query=<query>
headers: DD-API-KEY, DD-APPLICATION-KEY
```
The response holds `series[].pointlist` as `[epoch ms, value]` pairs; write them as `time,value` rows (the ranking script accepts epoch milliseconds). Use `.rollup(max, 15)` for the maximum per 15 s, not the default average.

Queries:
- CPU: `max:system.cpu.user{host:app-*}.rollup(max, 15)`, and `system.cpu.system`
- Memory: `max:system.mem.used{host:app-*}.rollup(max, 15)`
- Container CPU throttling: `max:kubernetes.cpu.cfs.throttled.seconds{kube_deployment:app}.rollup(max, 15)`
- JVM: `max:jvm.gc.major_collection_time{service:app}`, `max:jvm.heap_memory{service:app}`, `max:jvm.thread_count{service:app}`
- Service latency (APM): `p95:trace.http.request{service:app,resource_name:post_/checkout}` (or the `trace.<integration>.request` metric for your framework)
- PostgreSQL: `max:postgresql.connections{*}`, `max:postgresql.locks{*}`

The UI's Export to CSV on a graph is the alternative; check that the time column is in one timezone.
