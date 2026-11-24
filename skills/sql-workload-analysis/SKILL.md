---
name: sql-workload-analysis
description: Use after a load test when the database may be the limiter. Finds the SQL statements that cost the most during the run window from the engine's own statistics (PostgreSQL, Oracle, SQL Server, MySQL), ranks them by total time, flags N+1 and scan-heavy patterns, and hands the top few to plan analysis.
---

# SQL workload analysis

Goal: know which statements the database spent its time on during the run, and which of them deserve a plan, before anyone changes an index.

This skill is engine-agnostic. How to export the statement statistics for each engine is in `references/` (`postgres.md`, `oracle.md`, `sqlserver.md`, `mysql.md`). The queries have not been run against real databases; check them against your engine version. Plans are read with `sql-plan-analysis`.

`<skill-dir>` below is the folder containing this SKILL.md; the script is in its `scripts/` folder.

## When to use

- `observability-analysis` or `results-analysis` points at the database (active sessions up, waits, a pool saturated, a slow transaction with database time).
- A transaction is slow and its trace shows most of the time in database calls.
- You are comparing two runs and the database time changed.

## Steps

### 1. Get permission and use a safe account
Use a read-only monitoring account. Statement statistics can hold literal values and personal data, so keep the exports out of version control and out of bug text. Do not run `EXPLAIN ANALYZE` (which executes the statement) on writes or on production.

### 2. Snapshot before and after the window
The statistics are cumulative counters. Export them just before the run starts and right after it ends (or reset them before the run where your engine allows), and note the exact times. Without a snapshot pair you rank everything since the last restart, not the run. Keep the same row limit on both exports and take them in the same way.

### 3. Rank by total time
```
python3 <skill-dir>/scripts/rank_statements.py after.csv --before before.csv --window-seconds 900 --requests 54000
```
It subtracts the snapshots, merges statements that differ only by literals or ids, ranks by total time in the window with the cumulative share, and flags:
- **possible N+1**: several calls per request, each fast (needs `--requests`, the number of requests the test sent in the window)
- **large results**: thousands of rows returned per call
- **scan-heavy**: many rows examined per row returned (where the engine reports it)

Total time includes waiting (locks, a full pool, I/O queues), so a statement can rank high because it waited, not because it is slow alone.

### 4. Tie statements to transactions
Match each top statement to the transaction that issues it: through comments or `application_name` the application sets, trace and APM span attributes, or by reading the code. A statement you cannot tie to a transaction is a lead, not a finding.

### 5. Get the plans for the top few
For the top three to five statements (usually enough to cover most of the time), get the plan with realistic bind values and data volumes, and analyse it with `sql-plan-analysis`. Plans on an empty or tiny database say nothing about a loaded one.

### 6. Change one thing and re-measure
One index, one rewrite, or one setting, then the same test again, with a new snapshot pair (`principle-one-variable-at-a-time`). Report the statement's total time, calls, and mean before and after, not only the transaction's latency.

### 7. Report
Give the window, the snapshot times, the top statements with their share and flags, which transaction each belongs to, what the plans showed, and what is unproven. Statement text goes into reports with literals masked.

## Pitfalls to avoid
- Ranking by mean time, which promotes rare slow statements over the frequent ones that cost the database most.
- Using statistics that include time outside the run.
- Reading a plan from a small data set and calling it the cause.
- Fixing a statement that is high only because it waits on a lock or a pool.
- Missing an N+1 because each call is fast.
- Copying SQL literals or personal data into a bug or report.

## Done when
- The snapshot pair covers the run window, with times recorded.
- The top statements are ranked by total time, with their share of database time.
- Each of the top few is tied to a transaction, or marked as unknown.
- Plans were read at realistic volumes, and nothing was changed without a re-measurement.
