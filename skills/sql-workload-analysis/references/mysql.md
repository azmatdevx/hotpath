# MySQL: statement statistics

Not run against a real database; check column names for your version. Needs `performance_schema` with the statement digest consumers on.

Cumulative digests, exported before and after the run (timers are in picoseconds, so divide by 1e9 for milliseconds):
```sql
SELECT DIGEST AS id, LEFT(DIGEST_TEXT, 400) AS digest_text, COUNT_STAR AS count_star,
       SUM_TIMER_WAIT / 1e9 AS total_ms, SUM_ROWS_SENT AS rows_sent, SUM_ROWS_EXAMINED AS rows_examined
FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC LIMIT 500;
```
Or `TRUNCATE TABLE performance_schema.events_statements_summary_by_digest;` right before the run and one export after. Digest text already has literals replaced by `?`.

Statements with no index: `SUM_NO_INDEX_USED` and `SUM_NO_GOOD_INDEX_USED` in the same table. Waits: `performance_schema.events_waits_summary_global_by_event_name`, and the sys schema's `sys.statement_analysis`. The slow query log (`long_query_time = 0` for the test window) gives per-execution detail, at a cost; summarise it with a tool, do not read it raw.

Plans: `EXPLAIN ANALYZE` on reads (MySQL 8); plain `EXPLAIN` on writes. See `sql-plan-analysis`.
