---
name: script-parameterization
description: Use when a load test script needs per-user or per-iteration test data (credentials, search terms, IDs, payload values), in any tool. Covers data sources, assignment strategies, sizing, collision and cache-distortion avoidance, single-use data, and data setup and cleanup.
---

# Script parameterization

Goal: each virtual user sends realistic, valid, non-colliding data, so the system under test behaves as it would under real traffic.

This skill is tool-agnostic. Per-tool syntax is in `references/` (`jmeter.md`, `k6.md`, `locust.md`, `gatling.md`). Read the file for the tool in use after reading this one.

## When to use

- Every user logs in with the same credentials, or every request uses the same ID.
- Results look too good, which suggests cache hits from repeated data.
- Users collide on shared records, or the test runs out of data.

## Steps

### 1. List what must vary
Go through the recorded flow and mark values that real users vary: credentials, search terms, product or record IDs, quantities, addresses, dates, and unique fields (emails, order references). Leave constant what is truly constant.

### 2. Choose the source
- **Data file** (CSV or JSON): simple, repeatable.
- **Database query or API export**: real, valid records.
- **Generated at runtime**: unique values (UUIDs, counters combined with a user number), and dates relative to now.
- **Created by a setup step**: accounts or records made through the application before the run.

### 3. Choose an assignment strategy
Pick per field, and write the choice down:
- **Unique per user**: each virtual user gets its own row (logins, carts).
- **Sequential or queue**: each row used once, in order (single-use items).
- **Random**: models independent choices (search terms, products).
- **Circular**: reuse rows in a loop when reuse is harmless.
- **Weighted or skewed**: popular items chosen more often, as in real traffic.

### 4. Size the data
- Single-use data needs at least users × iterations rows (or arrival rate × duration). Add margin.
- For reusable data, size the pool so repeated access does not create unrealistic cache hit rates. If every user reads the same ten products, you measure the cache.
- Match production distribution and volume where it matters for indexes and caches.

### 5. Avoid collisions
- Two users must not edit the same record, use the same unique key, or hold the same lock, unless that is the scenario.
- Generate unique values with a user or thread identifier plus a counter or UUID.
- In distributed runs, split data across generators so two generators do not use the same rows.

### 6. Handle consumed data
Orders, coupons, one-time tokens, and password changes use up or change data. Plan one of:
- generate fresh data for each run
- reset the data before each run (restore a snapshot, or run a cleanup script)
- design the flow to be repeatable (create then delete)

### 7. Prepare and verify data before the run
- Confirm every row exists and is valid in the target environment: accounts can log in, IDs exist, accounts are not locked.
- Run a small validation (see `script-validation`) using the actual data file.
- Check data for sensitive information. Use synthetic or anonymised data, never real customer data.

### 8. Store data safely
Keep data files out of version control if they hold credentials. Load secrets from environment variables or a secret store. Document the data format and how to regenerate it.

## Pitfalls to avoid
- One account for all users, causing lock contention and session conflicts.
- Running out of single-use rows mid-test and having the tool wrap or stop silently.
- Repeating a small data set so the cache makes everything fast.
- Duplicate unique values causing validation errors that look like server faults.
- Using production customer data.
- Forgetting that the data file path must exist on every load generator.

## Done when
- Every field that must vary has a source and an assignment strategy.
- The data volume covers users × iterations (or arrival rate × duration) with margin.
- A concurrent validation run shows no collisions or invalid data.
- Single-use data has a reset or generation plan, and no real customer data is used.
