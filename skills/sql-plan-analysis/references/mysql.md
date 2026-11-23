# MySQL: plan analysis

Verify syntax against the MySQL or MariaDB version in use. MariaDB differs in places (for example its `ANALYZE` statement for actual runtime data).

## Getting the plan
- Estimated: `EXPLAIN SELECT ...` and `EXPLAIN FORMAT=TREE SELECT ...` (MySQL 8).
- Actual, with timings (MySQL 8.0.18 and later): `EXPLAIN ANALYZE SELECT ...` This **executes** the query. For data changes, run on a copy or inside a transaction you roll back.
- The slow query log and `performance_schema` (statement digests) find the worst queries. `SHOW INDEX FROM table` lists indexes.

## Reading the plan (tabular `EXPLAIN`)
- `type`: `ALL` is a full table scan, `index` a full index scan, `range`, `ref`, `eq_ref`, and `const` are progressively better.
- `key` and `possible_keys` show which index was chosen and which were candidates. `key: NULL` means no index was used.
- `rows` is the estimate of rows examined. Compare with `EXPLAIN ANALYZE` actual rows.
- `Extra`: `Using filesort` (sort not satisfied by an index), `Using temporary` (temp table), `Using where`, `Using index` (covering index).

## Common fixes
- `ANALYZE TABLE` to refresh statistics. Consider histograms (MySQL 8) for skewed non-indexed columns.
- Add or reorder composite indexes to match the filter and sort order, with the most selective equality columns first.
- Avoid functions on indexed columns, implicit type conversions (for example comparing a string column to a number), and leading wildcards in `LIKE`.
- Replace deep `OFFSET` pagination with keyset pagination.
- Use optimizer hints or index hints only after finding the root cause, and re-test after upgrades.
