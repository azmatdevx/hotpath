# Dynatrace

Not run against a real tenant; check the metric keys and the token scope (`metrics.read`).

Export with the Metrics API v2 (a token from the environment):
```
GET <env>/api/v2/metrics/query?metricSelector=<selector>&from=<epoch ms>&to=<epoch ms>&resolution=15s
```
The response holds `result[].data[].timestamps` and `values`; write them as `time,value` rows (epoch milliseconds are accepted).

Selectors:
- Host CPU: `builtin:host.cpu.usage:max`
- Host memory: `builtin:host.mem.usage:max`
- Service latency: `builtin:service.response.time:percentile(95)` split by service or request name
- Service rate and failures: `builtin:service.requestCount.total:rate(1s)`, `builtin:service.errors.total.rate`
- JVM: `builtin:tech.jvm.memory.pool.used`, `builtin:tech.jvm.memory.gc.suspensionTime`
- Connection pool and database time per service: Dynatrace names these by technology; browse the metric catalogue (`/api/v2/metrics?text=pool`) rather than assuming a key.

Very fine resolutions are limited for older windows; export soon after the run.
