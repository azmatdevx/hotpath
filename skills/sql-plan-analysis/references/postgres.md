# PostgreSQL: plan analysis

Verify syntax against the PostgreSQL version in use.

## Getting the plan
- Estimated only: `EXPLAIN SELECT ...`
- Actual, with I/O: `EXPLAIN (ANALYZE, BUFFERS) SELECT ...` Add `VERBOSE` for column output, and `SETTINGS` for non-default settings.
- `ANALYZE` **executes** the statement. For data changes, wrap it: `BEGIN; EXPLAIN (ANALYZE, BUFFERS) UPDATE ...; ROLLBACK;`
- Set `track_io_timing = on` for I/O time in the plan, where acceptable.
- `auto_explain` logs plans of slow queries. `pg_stat_statements` ranks queries by total time and calls.

## Reading the plan
- Compare `rows=` (estimate) with `actual rows=`. Large gaps point to statistics or data skew.
- `actual time` is per loop. Multiply by `loops` for total time of that node.
- `Seq Scan` on a large table with a selective filter, and `Rows Removed by Filter` being large, suggest a missing or unusable index.
- `Index Scan`, `Index Only Scan`, and `Bitmap Heap Scan` are index paths. Check heap fetches for index-only scans.
- `Buffers: shared hit` versus `read` shows cache use. High `read` means disk I/O.
- `Sort Method: external merge Disk` means the sort spilled. Look at `work_mem`. Hash nodes with many batches also spilled.
- Join nodes: `Nested Loop` (good for few outer rows), `Hash Join`, `Merge Join`.

## Common fixes
- `ANALYZE table;` to refresh statistics. For correlated columns, consider extended statistics (`CREATE STATISTICS`).
- Create an index that matches the filter and sort order, and check for expression or partial index needs.
- Rewrite predicates that wrap columns in functions, or add a matching expression index.
- Check `pg_stat_user_indexes` for unused indexes, which cost writes.
- Prepared statements can use a generic plan after several executions, which may differ for skewed values. Check `plan_cache_mode` if plans vary by parameter.
