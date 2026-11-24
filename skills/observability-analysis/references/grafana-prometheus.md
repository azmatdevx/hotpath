# Grafana and Prometheus

Not run against a real instance; check the metric names against your exporters.

Export a window from the Prometheus HTTP API (read-only, a token from the environment if needed), as time and value:
```python
import csv, json, os, sys, urllib.parse, urllib.request
base, query, start, end, step, out = sys.argv[1:7]          # start and end in epoch seconds, step like 15
url = f"{base}/api/v1/query_range?" + urllib.parse.urlencode({"query": query, "start": start, "end": end, "step": step})
req = urllib.request.Request(url, headers={"Authorization": os.environ["PROM_AUTH"]} if os.environ.get("PROM_AUTH") else {})
data = json.load(urllib.request.urlopen(req))["data"]["result"]
with open(out, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["time", "value"])
    for t, v in data[0]["values"]:
        w.writerow([int(t), v])
```
In Grafana, a panel's Inspect, Data, Download CSV also works (check the time format).

Queries (PromQL), aggregated to one series per tier:
- CPU: `100 * (1 - avg(rate(node_cpu_seconds_total{mode="idle", instance=~"app.*"}[1m])))`
- Container CPU and throttling: `sum(rate(container_cpu_usage_seconds_total{pod=~"app-.*"}[1m]))`, `sum(rate(container_cpu_cfs_throttled_seconds_total{pod=~"app-.*"}[1m]))`
- Memory: `sum(container_memory_working_set_bytes{pod=~"app-.*"})`
- JVM: `sum(rate(jvm_gc_pause_seconds_sum[1m]))`, `sum(jvm_memory_used_bytes{area="heap"})`, `sum(jvm_threads_live_threads)`
- Connection pool (HikariCP via Micrometer): `sum(hikaricp_connections_active)`, `sum(hikaricp_connections_pending)`, `max(hikaricp_connections_max)`
- Request latency (Micrometer): `histogram_quantile(0.95, sum by (le) (rate(http_server_requests_seconds_bucket{uri="/checkout"}[1m])))`
- PostgreSQL exporter: `sum(pg_stat_activity_count{state="active"})`, `sum(pg_locks_count)`

Use a step of 15 s or finer and the same range as the reference series. Rates over `[1m]` smooth short spikes; use `[30s]` if the scrape interval allows.
