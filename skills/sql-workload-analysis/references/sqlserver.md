# SQL Server: statement statistics

Not run against a real database; check view and column names for your version. Query Store must be on for the first form.

Query Store, for the run window (interval times in UTC):
```sql
SELECT CAST(q.query_id AS varchar(20)) AS id, LEFT(qt.query_sql_text, 400) AS query,
       SUM(rs.count_executions) AS calls, SUM(rs.count_executions * rs.avg_duration) / 1000.0 AS total_ms,
       SUM(rs.count_executions * rs.avg_rowcount) AS rows
FROM sys.query_store_query q
JOIN sys.query_store_query_text qt ON qt.query_text_id = q.query_text_id
JOIN sys.query_store_plan p ON p.query_id = q.query_id
JOIN sys.query_store_runtime_stats rs ON rs.plan_id = p.plan_id
JOIN sys.query_store_runtime_stats_interval i ON i.runtime_stats_interval_id = rs.runtime_stats_interval_id
WHERE i.start_time >= @start AND i.end_time <= @end
GROUP BY q.query_id, qt.query_sql_text ORDER BY total_ms DESC;
```
This is already windowed, so use it as AFTER without `--before`. Query Store intervals are coarse (the default is an hour); set a smaller interval before the test if you need the window to be accurate.

Cumulative alternative (before and after exports): `sys.dm_exec_query_stats` with `total_elapsed_time / 1000.0 AS total_ms`, `execution_count AS calls`, `total_rows AS rows`, and `SUBSTRING(st.text, 1, 400)` from `CROSS APPLY sys.dm_exec_sql_text(sql_handle) st`.

Waits: `sys.dm_os_wait_stats` before and after (subtract), or Extended Events. Plans: actual execution plan on reads, estimated on writes. See `sql-plan-analysis`.
