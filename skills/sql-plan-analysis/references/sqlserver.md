# SQL Server: plan analysis

Verify syntax against the SQL Server version in use.

## Getting the plan
- Estimated: SSMS "Display Estimated Execution Plan", or `SET SHOWPLAN_XML ON`.
- Actual, with runtime row counts: SSMS "Include Actual Execution Plan", or `SET STATISTICS XML ON`. This **executes** the query, so wrap data changes in a transaction you roll back.
- I/O and time: `SET STATISTICS IO, TIME ON;` shows logical reads per table and CPU and elapsed time.
- Query Store (when enabled) keeps plans and runtime history per query, which helps find regressions and compare plans over time. `sys.dm_exec_query_stats` and `sys.dm_exec_cached_plans` show cached plans and their cost.

## Reading the plan
- Compare estimated and actual rows on each operator. Large gaps point to statistics or parameter sniffing.
- `Clustered Index Scan` or `Table Scan` on a large table with a selective filter, versus `Index Seek`.
- `Key Lookup` or `RID Lookup` repeated for many rows can dominate. A covering index may help.
- Warnings on operators: implicit conversion, spill to tempdb on `Sort` or `Hash Match`, missing statistics.
- Join operators: `Nested Loops`, `Hash Match`, `Merge Join`. Check suitability for row counts.
- "Missing index" hints in the plan are suggestions only. Check overlap with existing indexes and the write cost before creating.

## Common fixes
- `UPDATE STATISTICS` (or rely on automatic updates and check they are on and recent).
- Parameter sniffing: compare the plan for different parameter values. Options include `OPTION (RECOMPILE)`, `OPTIMIZE FOR`, query rewrite, or Query Store plan forcing as a stopgap.
- Add covering or filtered indexes, and remove functions or mismatched types in predicates.
- Check for blocking and waits before blaming the plan (`sys.dm_os_wait_stats`, `sys.dm_exec_requests`).
