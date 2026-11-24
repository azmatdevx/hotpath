# New Relic

Not run against a real account; check the event types and attributes against your agents.

Run NRQL in the query builder and export CSV, or through the NerdGraph API (an API key from the environment). Use `TIMESERIES 15 seconds` and the run window in `SINCE ... UNTIL ...` (epoch seconds or ISO times).

Queries (NRQL):
- Latency: `SELECT percentile(duration, 95) FROM Transaction WHERE appName = 'app' AND name LIKE '%checkout%' SINCE <start> UNTIL <end> TIMESERIES 15 seconds` (duration is in seconds)
- Rate and errors: `SELECT rate(count(*), 1 second), percentage(count(*), WHERE error IS true) FROM Transaction WHERE appName = 'app' TIMESERIES 15 seconds`
- Host CPU and memory: `SELECT max(cpuPercent), max(memoryUsedPercent) FROM SystemSample WHERE hostname LIKE 'app%' TIMESERIES 15 seconds`
- Where time goes inside a service: `SELECT average(duration) FROM Span WHERE service.name = 'app' FACET name TIMESERIES 15 seconds LIMIT 10`
- Database calls: `SELECT average(databaseDuration), average(databaseCallCount) FROM Transaction WHERE appName = 'app' TIMESERIES 15 seconds`

Metrics with a finer resolution than the default may need the `Metric` event type; check the agent's documentation. Save each result as `time,value`.
