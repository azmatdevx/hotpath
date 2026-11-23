---
name: script-authoring
description: Use when writing a load test script from scratch or from a recording, in any tool (JMeter, k6, Locust, Gatling, etc.). Covers journey definition, cleaning a capture, transaction naming, session handling, think time and pacing, assertions, externalised configuration, and maintainable structure.
---

# Script authoring

Goal: a script that behaves like real users, is easy to read and change, and is ready for correlation, parameterization, and validation.

This skill is tool-agnostic. Per-tool structure and syntax are in `references/` (`jmeter.md`, `k6.md`, `locust.md`, `gatling.md`). Read the file for the tool in use after reading this one.

## When to use

- A new journey needs a load test script.
- A recording or HAR file must be turned into a maintainable script.
- An existing script is brittle, hard to read, or hard to change.

## Steps

### 1. Define the journey
Write the flow as numbered user steps with the expected outcome of each (for example "1. open home page, 2. log in, 3. search, 4. add to cart, 5. check out, confirmation shown"). Decide the level of simulation:
- **Protocol level** (HTTP requests): high scale, cheaper, needs correlation.
- **Browser level**: realistic client behaviour and timings, expensive, lower scale (see `browser-script-authoring`).
Say which and why.

### 2. Start from a capture or a spec
Prefer a clean source: an API specification, or a capture recorded twice (see `script-correlation`). Record only the target journey, with a clean browser state, and with no unrelated tabs or extensions.

### 3. Clean the capture
Keep what a real client sends to the system under test. Remove:
- third-party analytics, ads, and tracking calls, unless the test must include them
- browser-internal and extension traffic
- static assets, unless you are testing the CDN or caching, or modelling a browser (decide deliberately)
- duplicate requests from the recorder
Do not delete requests that the application needs for state (CSRF fetches, config calls, auth redirects).

### 4. Group into transactions
Wrap each meaningful user step in a named transaction so results report at the step the user cares about, not per request. Use stable names that match the journey ("01_login", "02_search"). Keep names free of dynamic values so results aggregate.

### 5. Handle session and headers
- Let the tool manage cookies per virtual user. Do not hard-code recorded cookies or session headers.
- Set common headers (base URL, user agent, content type) once, not per request.
- Keep authentication as its own step so it can be reused and measured.

### 6. Add realistic timing
Add think time between user steps and pacing between iterations, based on observed behaviour (see `principle-model-real-users`). Use variation, not one constant. Do not add think time inside a transaction's own measured duration unless it is part of what the user waits for.

### 7. Prepare for correlation and data
Leave obvious placeholders for dynamic values and test data, then use `script-correlation` and `script-parameterization`. Do not hard-code environment-specific values (hosts, ports, user names) in request bodies.

### 8. Add assertions
Assert on response content for every step that matters (see `script-validation`), not only on status codes.

### 9. Externalise configuration
Keep these outside the script logic, as parameters or environment variables: base URL, user count, ramp and duration, think time scale, data file paths, and credentials source. Never commit secrets.

### 10. Structure for maintenance
- Put shared logic (login, common checks) in reusable modules or functions.
- Keep one journey per script or scenario, and compose them in the workload definition.
- Keep the workload (how many users, how long) separate from the journey logic.
- Use version control and small, reviewable changes. Add a short header comment with the journey, the tool version, and how to run it.

## Pitfalls to avoid
- Recording a long, unfocused session and leaving all of it in.
- Leaving recorded cookies, tokens, or hosts hard-coded.
- Naming transactions after URLs with IDs, which fragments the results.
- No think time, or the same think time everywhere.
- Mixing journey logic with workload settings.
- Committing recordings that contain real credentials or customer data.

## Done when
- The journey is written down and the script follows it step by step.
- Requests are grouped into stable, meaningful transactions.
- Configuration is externalised and no secrets are committed.
- Dynamic values and data are ready for correlation and parameterization.
- The script is structured so a teammate can read and change it.
