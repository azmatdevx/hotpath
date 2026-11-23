---
name: script-review
description: Use when reviewing a load test script (a JMeter .jmx, k6, Locust, or Gatling script) before it is run or merged. Checks correctness, realism, data, measurement integrity, safety, and maintainability, and reports findings by severity with a verdict.
---

# Script review

Goal: catch problems that would invalidate results, distort numbers, or harm the target, before any load is run.

This skill is tool-agnostic. Per-tool things to look for are in `references/` (`jmeter.md`, `k6.md`, `locust.md`, `gatling.md`). Read the file for the tool in use after reading this one. For browser-based scripts use `browser-script-review`.

## When to use

- A teammate or an agent wrote or changed a load test script.
- A script is about to be used for a release decision.
- Results look wrong and the script is the suspect.

## Steps

### 1. Get context
Find out the journey being simulated, the workload (users or arrival rate, duration, think time), the tool and version, the target environment, and the intended question (see `load-test-design`). A script cannot be judged without knowing what it should do.

### 2. Review by category
Work through each category and note findings with their location.

**Correctness**
- Every step asserts response content, not only status codes (see `script-validation`).
- Dynamic values are extracted from responses, not hard-coded, and a missing value fails loudly (see `script-correlation`).
- Error handling does not silently swallow failures or let a broken flow count as success.
- Redirects and multi-request steps behave as the real client does.

**Realism**
- Think time and pacing exist, vary, and match the model (see `principle-model-real-users`).
- Cookies and sessions are per virtual user.
- The transaction mix and flow order match the design.
- Caching and static resource behaviour are deliberate, not accidental.

**Data**
- Data varies per user where it should, and has enough volume (see `script-parameterization`).
- No collisions between users, and single-use data cannot be silently exhausted or wrapped.
- No secrets, tokens, or customer data in the script or its data files.

**Measurement integrity**
- Transactions are named stably, without dynamic values.
- No debug listeners, verbose logging, or heavy per-request code on the hot path of a load run.
- Timeouts are set, so a hung request does not stall a user forever.
- Ramp-up, duration, and loop settings match the plan, and nothing runs infinitely by accident.
- The script does not do expensive work (large parsing, heavy logging) that makes the generator the limiter.

**Safety**
- The target host comes from configuration, and the script cannot hit production by default.
- Request rate and iteration limits are bounded.
- Destructive operations (deletes, payments, emails, notifications) are avoided or pointed at safe test endpoints.

**Maintainability**
- Configuration is externalised, and shared logic is reused.
- Structure is readable, names are meaningful, and dead or disabled code is removed.
- The file is in version control with a short note on how to run it.

### 3. Run it when you can
Static review misses behaviour. Run the single-user and small concurrent checks from `script-validation`, and compare what the script does with what the review expects.

### 4. Report findings
For each finding give: location (file and line or element name), severity, why it affects results, and a suggested fix. Use these severities:
- **Blocker:** invalidates results or can harm the target.
- **Major:** distorts the numbers materially.
- **Minor:** weakens realism or maintainability.
- **Nit:** style.
Group by severity, most serious first. Praise what is done well in a line, since it shows what to keep.

### 5. Give a verdict
One of: **approve**, **approve with changes** (list the required ones), or **request changes** (blockers present). Say what you could not check, such as behaviour you did not run.

## Report template

```
Verdict: <approve | approve with changes | request changes>
Context: <journey, tool and version, workload, target>

Blockers
- <location>: <finding>. Why: <effect on results>. Fix: <change>.
Major
- ...
Minor / Nits
- ...
Not checked: <what you did not run or verify>
```

## Pitfalls to avoid
- Reviewing style while missing a status-only check.
- Assuming the script works because it ran.
- Ignoring the workload settings and only reading the journey.
- Reporting every finding at the same weight.
- Rewriting the script in review instead of describing the fix.

## Done when
- Each category was reviewed, and findings have location, severity, effect, and fix.
- The verdict follows from the findings, and unchecked areas are stated.
