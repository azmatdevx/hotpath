# Oracle: plan analysis

Verify syntax against the Oracle version in use. Some diagnostics (AWR, ASH, SQL Monitor) require specific licensed management packs, so confirm licensing before using them.

## Getting the plan
- Estimated: `EXPLAIN PLAN FOR <sql>;` then `SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);`
- Actual, with row counts: run the query with `/*+ GATHER_PLAN_STATISTICS */` (or set `STATISTICS_LEVEL = ALL` for the session), then:
  `SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY_CURSOR(NULL, NULL, 'ALLSTATS LAST'));`
- For a cursor already in the shared pool, find it in `V$SQL` by text or `SQL_ID`, then `DBMS_XPLAN.DISPLAY_CURSOR('<sql_id>', <child>, 'ALLSTATS LAST')`.

## Reading the plan
- Compare `E-Rows` (estimated) with `A-Rows` (actual). Large gaps point to statistics problems, skew, or bind values.
- `TABLE ACCESS FULL` on a large table with a selective filter suggests a missing index or a predicate that cannot use one.
- `INDEX RANGE SCAN`, `INDEX UNIQUE SCAN`, and `INDEX FAST FULL SCAN` are index paths. `TABLE ACCESS BY INDEX ROWID` per row can dominate when many rows match.
- Join methods: `NESTED LOOPS`, `HASH JOIN`, `MERGE JOIN`. Check which suits the row counts.
- `Starts` shows how many times an operation ran. Multiply with per-start cost.
- Look at temp space use (`Used-Tmp`) for sorts and hashes that spilled.

## Common fixes
- Gather statistics: `DBMS_STATS.GATHER_TABLE_STATS(...)`. Consider histograms for skewed columns.
- Bind variable peeking and adaptive cursor sharing can produce plans that suit one value and not another, so test with different binds.
- Add or adjust indexes. Check the effect on DML.
- Use SQL plan baselines to keep a good plan stable after you have fixed the root cause, not instead of fixing it.
- Avoid functions on indexed columns, and implicit conversions from mismatched types.
