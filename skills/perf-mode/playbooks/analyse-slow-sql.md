# Playbook: analyse slow SQL

You own finding which SQL statements the database spent its time on during a load test run and what to do about the top few, with a plan and a re-measurement behind every recommendation. Window, rank, tie, plan, verify.

Use when: an analysis points at the database as the limiter or a contributor (active sessions or waits up, a connection pool saturated, a transaction whose time is mostly in database calls).

## Inputs

- The run window (start and end times, timezone) and the transactions that degraded.
- Read access to the database's statement statistics, as a read-only monitoring account, and the engine and version.
- A statement-statistics snapshot from just before and just after the run (or a reset before the run). If none exists, say that the ranking will cover everything since the last reset.
- The number of requests the test sent in the window (from the results), for the N+1 check.
- Permission to run `EXPLAIN` against the database (see the hard rule); never `EXPLAIN ANALYZE` on writes or on production.

## Steps

1. **Confirm the window and the evidence.** Check the snapshots bracket the run, and that the database really is implicated (`observability-analysis`).
2. **Export and rank.** Run `sql-workload-analysis`: export the statistics for the engine, then `rank_statements.py` with the before snapshot, the window, and the request count.
3. **Tie statements to transactions** through application tags, traces, or the code. Mark any you cannot tie as leads.
4. **Read the plans** of the top three to five statements with `sql-plan-analysis`, with realistic bind values and data volumes.
5. **Propose one change per statement,** with the mechanism it relies on and the metric that should move (the statement's total time, calls, or mean).
6. **Verify.** Apply one change on a test copy or in the next run, take a new snapshot pair, and compare the statement's numbers (`principle-one-variable-at-a-time`). A change that does not move the statement's own numbers is not a fix.
7. **Report.**

## Verification

A pass is a ranked list from a snapshot pair that brackets the run, each top statement tied to a transaction or marked unknown, a plan read at realistic volume, and a before and after for any change. Not a pass: a ranking of everything since the last restart, a plan from an empty table, an index recommended because a statement ranked high while it was only waiting on a lock, or a statement text with real values copied into the report.

## Stop conditions

- No snapshot pair and no reset: report that the ranking covers more than the run, and what that limits.
- The statistics extension is not enabled or you lack access: stop and say what is needed.
- The top statements are mostly waiting (locks, pool): the cause is upstream of the SQL; say so and go back to `observability-analysis`.
- A change would run against production or a shared database without approval: stop and ask.

## Delegation

The lead owns the ranking and the recommendations. A worker can export statistics and run the script from files you point to, but the lead reads the plans and decides. Workers read `perf-mode/worker.md` first, and never run `EXPLAIN ANALYZE` on writes or change anything in the database.

## Reply format

The window and snapshot times, the top statements (share of database time, calls, mean, flags), which transaction each belongs to, what the plans showed, the proposed change and the metric that should move, and what is unproven. Statement text with literals masked.

## Related playbooks

`analyse-a-test-run` (the analysis that points here).

## Done when

- The ranking comes from a snapshot pair that covers the run.
- Each recommended change has a plan, a mechanism, and a metric to move.
- Nothing sensitive is in the report.
