# Azure Monitor and Application Insights

Not run against a real workspace; check the table and column names against your workspace.

Run KQL in Log Analytics and export CSV, or `az monitor log-analytics query --workspace <id> --analytics-query "<kql>"` and convert the JSON to `time,value`. Use `bin(<time>, 15s)` and the run window in a `where ... between` clause.

Queries (KQL):
- Application latency and rate (Application Insights): `requests | where timestamp between (datetime(<start>) .. datetime(<end>)) and name contains "checkout" | summarize p95 = percentile(duration, 95), n = count() by bin(timestamp, 15s)`
- Downstream calls: `dependencies | where timestamp between (...) | summarize p95 = percentile(duration, 95) by target, bin(timestamp, 15s)`
- VM CPU: `Perf | where TimeGenerated between (...) and ObjectName == "Processor" and CounterName == "% Processor Time" | summarize max(CounterValue) by bin(TimeGenerated, 15s)`
- Container CPU and memory: `InsightsMetrics | where Namespace == "container.azm.ms" | summarize max(Val) by Name, bin(TimeGenerated, 15s)`
- Azure SQL and platform metrics: `AzureMetrics | where ResourceProvider == "MICROSOFT.SQL" and MetricName in ("cpu_percent", "workers_percent", "sessions_percent") | summarize max(Maximum) by MetricName, bin(TimeGenerated, 15s)`

Platform metrics are often available only at 1 minute; say so when the resolution limits what you can conclude.
