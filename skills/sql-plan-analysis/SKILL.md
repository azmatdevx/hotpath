---
name: sql-plan-analysis
description: Use when analysing a slow SQL query through its execution plan, on Postgres, Oracle, SQL Server, or MySQL. Covers capturing the real query and the actual plan with runtime statistics, comparing estimated and actual rows, spotting scans, joins, sorts, and non-sargable predicates, and proposing and re-measuring one change at a time.
---

# SQL plan analysis

Goal: find why a query is slow from evidence in its plan, change one thing, and prove the improvement.

This skill is engine-agnostic. Engine-specific commands and plan reading are in `references/` (`postgres.md`, `oracle.md`, `sqlserver.md`, `mysql.md`). Read the file for the engine in use after reading this one.

## When to use

- Load test results point to a slow database call.
- A query is slow in production and fast in test, or the reverse.
- A plan changed after a deployment, data growth, or a statistics refresh.

## Safety first

- Some commands **execute the statement** to collect actual runtime data (for example `EXPLAIN ANALYZE` on Postgres and MySQL). For INSERT, UPDATE, DELETE, or MERGE, run them inside a transaction you roll back, or on a copy of the data.
- Prefer a non-production copy with realistic data volume. Do not run heavy diagnostics against a production database without approval.
- Do not paste real customer values into shared notes. Use representative parameters.

## Steps

### 1. Capture the real query
Get the exact SQL as the application sends it, with the real parameter values or typical ones (not just the template). The same statement can have very different plans for different values. Note whether it uses bind variables or literals.

### 2. Measure the baseline
Record elapsed time over several runs, and the rows returned. Separate execution time from waiting (locks, I/O, network, application). If the database time is small, the problem is not the plan (see `principle-explain-the-number`).

### 3. Get the actual plan with runtime statistics
An estimated plan shows what the optimiser expects. The actual plan shows what happened: real row counts, time per operator, and I/O. Use the actual plan whenever you can (see the engine reference).

### 4. Compare estimated and actual rows
Find operators where the estimate and the actual row count differ by a large factor. A bad estimate is the most common root cause of a bad plan. Likely causes: stale or missing statistics, skewed data, correlated columns, or parameter values that differ from the ones the plan was built for.

### 5. Find the expensive operators
Look for where the time and I/O go: the operator with the largest share of time, the most rows processed, or the most reads. Note loops that run many times (the work multiplies by the loop count).

### 6. Check access paths and joins
- **Full scans** on large tables where a selective filter exists, versus index seeks or range scans.
- **Index lookups per row** that dominate (many lookups back to the table).
- **Join strategy** (nested loops, hash, merge) that does not suit the row counts.
- **Sorts, hashes, or temp tables that spill to disk.**

### 7. Check the query itself
- Functions or casts on indexed columns, implicit type conversions, and leading wildcards in `LIKE`, which prevent index use.
- `SELECT *` fetching more than needed, and unneeded `DISTINCT` or `ORDER BY`.
- Deep `OFFSET` pagination, correlated subqueries, and OR conditions that defeat indexes.
- Many small queries from the application (N+1) that are fast alone and slow together. Count queries per request.

### 8. Form one hypothesis and change one thing
Pick the single most likely cause and one change: refresh statistics, add or adjust an index, rewrite a predicate, change a hint, or fix the application's query pattern. Do not stack changes (see `principle-one-variable-at-a-time`).

### 9. Re-measure and check side effects
- Re-run on the same data and parameters, and compare the actual plan and the timings (median of several runs).
- Check other queries on the same tables. A new index slows writes and can change other plans.
- Test with other parameter values, including rare and common ones.
- Confirm the improvement under load, not just for a single execution.

### 10. Record the finding
Note the query, the before and after plans, the cause, the change, the numbers, and the risks (write cost, plan stability).

## Pitfalls to avoid
- Reading only the estimated plan.
- Tuning with a tiny data set that produces a different plan from production.
- Trusting "missing index" suggestions without checking write cost and overlap.
- Forcing a plan with hints when stale statistics are the real cause.
- Running a data-modifying statement with a command that executes it and forgetting to roll back.
- Measuring a single run, or a run that benefited from a warm cache without noting it.

## Done when
- The actual plan, with estimated versus actual rows, has been read.
- The cause is stated with evidence from the plan.
- One change was made, and the before and after numbers are recorded.
- Side effects on writes and other queries were considered.
