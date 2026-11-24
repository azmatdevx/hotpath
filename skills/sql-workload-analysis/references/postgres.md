# PostgreSQL: statement statistics

Not run against a real database; check column names for your version. Needs the `pg_stat_statements` extension and a role allowed to read it.

Export to CSV just before and just after the run (the counters are cumulative):
```sql
\copy (SELECT queryid::text AS id, left(query, 400) AS query, calls, total_exec_time AS total_ms, rows
       FROM pg_stat_statements WHERE dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
       ORDER BY total_exec_time DESC LIMIT 500) TO 'before.csv' CSV HEADER
```
On PostgreSQL 12 and earlier the column is `total_time`. Alternatively `SELECT pg_stat_statements_reset();` right before the run and one export after. Take the same `LIMIT` in both exports: a statement missing from the after export that was in the before export is read as not run.

Waits during the run: sample `pg_stat_activity` every second (`SELECT now(), state, wait_event_type, wait_event, left(query, 120) FROM pg_stat_activity WHERE state <> 'idle'`) and count by `wait_event`.

Plans: `EXPLAIN (ANALYZE, BUFFERS)` on reads with realistic parameters; plain `EXPLAIN` on writes. See `sql-plan-analysis`.
