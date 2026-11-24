# Oracle: statement statistics

Not run against a real database; check view names for your version and licence (AWR and ASH need the Diagnostics Pack).

Cumulative statistics from the cursor cache, exported before and after the run:
```sql
SELECT sql_id AS id, SUBSTR(sql_text, 1, 400) AS sql_text, executions, elapsed_time / 1000 AS total_ms,
       rows_processed AS rows, buffer_gets, disk_reads
FROM v$sqlstats ORDER BY elapsed_time DESC FETCH FIRST 500 ROWS ONLY;
```
Statements can age out of the cursor cache; if so, a statement in the before export but not the after export was evicted, not idle. With AWR, take snapshots (`DBMS_WORKLOAD_REPOSITORY.CREATE_SNAPSHOT`) before and after, and use `DBA_HIST_SQLSTAT` between them.

Where the time went, from Active Session History for the window:
```sql
SELECT sql_id, event, COUNT(*) AS samples FROM v$active_session_history
WHERE sample_time BETWEEN :start AND :end GROUP BY sql_id, event ORDER BY samples DESC FETCH FIRST 30 ROWS ONLY;
```
Each sample is about one second of one session; the event shows waiting, not work. Plans: `DBMS_XPLAN.DISPLAY_CURSOR(sql_id, NULL, 'ALLSTATS LAST')`. See `sql-plan-analysis`.
