---
name: script-validation
description: Use before any load run to prove a load test script is correct, in any tool (JMeter, k6, Locust, Gatling, etc.). Covers a single-user pass, content assertions, correlation and data checks, think time and pacing, server-side confirmation, debug-overhead removal, and a small concurrent run.
---

# Script validation

Goal: prove the script does what a real user does, correctly, before any load is applied. Load applied to a broken script produces meaningless numbers and can harm shared environments.

This skill is tool-agnostic. Per-tool commands are in `references/` (`jmeter.md`, `k6.md`, `locust.md`, `gatling.md`). Read the file for the tool in use after reading this one.

## When to use

- A script was just written, recorded, or changed.
- A script that passed before now fails, or passes with suspicious numbers.
- Before handing a script to someone else, or scaling it up.

## Steps

### 1. Run one user, one iteration
Run a single virtual user for a single iteration with full request and response logging. Read the logs. Do not trust the summary alone.

### 2. Check every response for content
For each step in the flow, confirm the response is the right one:
- status code matches what the real client sees (including expected redirects)
- the body contains something that proves the step worked (a username after login, an order number after checkout, a known element or field)
- the body does not contain error markers (error page text, a login form, an empty result)

Add these as assertions or checks in the script, so a wrong response fails the request.

Then prove the assertions can fail. Break something on purpose (send a wrong token or a stale CSRF value, or point at a stub that returns status 200 with an empty result) and confirm the script reports failures and, in a headless run, exits with a failing status. An assertion that has never failed is untested.

### 3. Check correlation and data
- Every dynamic value is extracted from a response, and none is hard-coded (see `script-correlation`).
- Extraction fails visibly when the value is missing.
- Test data is valid, belongs to the intended user, and is not exhausted or locked.
- Run two iterations in a row for the same user to catch values that work only once.

### 4. Check timing behaviour
- Think time and pacing are present and match the workload model. Without them, a closed model sends unrealistic request rates.
- Transaction names are stable and meaningful, so results can be grouped.
- No fixed sleeps hide waiting that should be an explicit wait or a polled condition.

### 5. Confirm on the server side
Where possible, verify the system under test saw what the script thinks it sent:
- request counts in the access log or APM match the script's count
- writes landed (rows created, orders placed, files stored)
- no unexpected errors or warnings in application logs during the run

### 6. Remove debug overhead
Before any load run:
- disable verbose request and response logging and GUI listeners
- run in the tool's headless or non-GUI mode
- keep only the result output needed for analysis

### 7. Run a small concurrent test
Run a handful of users (for example 5 to 10) for a few iterations:
- no errors, and assertions pass for all users
- users do not share tokens, sessions, or data that should be unique
- no data collisions (two users editing the same record, duplicate keys)
- generator resource use is low, so the generator is not the limiter

### 8. Record the result
Write down the exact command, the tool version, the data used, and what the single-user and concurrent runs showed. This is the handoff for the real run.

## Pitfalls to avoid
- Treating status 200 as success without a content check.
- Validating with the GUI or debug logging on, then running the load test the same way.
- Skipping the second iteration, which hides single-use values.
- Validating with one user only, which hides shared state and collisions.
- Letting a failed assertion pass silently because the tool's default is to continue.
- Trusting an error rate built only on status codes: a degraded system can return 200 with empty or fake results.
- Using production accounts or real customer data for validation.

## Done when
- A single-user run passes with content assertions on every important step.
- Each assertion was shown to fail when the response is wrong.
- A small concurrent run passes with no errors, shared state, or collisions.
- Server-side evidence confirms the requests and the work happened.
- Debug overhead is off, and the run command is recorded.
