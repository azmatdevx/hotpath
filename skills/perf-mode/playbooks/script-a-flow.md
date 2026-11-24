# Playbook: script a flow

You own a load test script for one user journey that has been proven to work. Plan, build, validate, review. Every claim that the script works traces to a run with content assertions.

Use when: a journey needs a load test script in any tool (JMeter, k6, Locust, Gatling, and so on), or an existing script is failing on replay.

## Inputs

- The journey, named step by step (for example "login, search, add to cart, check out").
- The tool and its version.
- The target environment, and the user's permission to run against it (see the hard rule in `perf-mode`).
- Test data for the journey, or how to create it.

## Steps

1. **Define the flow and the target.** Name the journey, the tool, and the environment. Confirm permission to test that environment.
2. **Capture the flow twice.** Record or run it two times, as different users if possible, and save the traffic (HAR or tool recording). Capture requests as well as responses. Keep the files out of version control.
3. **Author the script.** Run `script-authoring`: group requests into named transactions, add think time and pacing that match real use, and strip static noise real users would not generate.
4. **Correlate.** Run `script-correlation`: diff the two captures, extract each dynamic value from the response that produces it, and substitute it into later requests.
5. **Parameterize.** Run `script-parameterization`: supply per-user and per-iteration data and avoid collisions and cache-friendly repetition.
6. **Validate.** Run `script-validation`: single user first, then a few concurrent users. Assert on response content, not only status, and show the assertions can fail.
7. **Review.** Run `script-review` (or `browser-script-review` for a browser script) and fix every blocker and major finding.
8. **Gate on principles.** Check `principle-validate-before-scale` and `principle-prove-the-work-happened`. If either fails, go back to step 4, 5 or 6.
9. **Hand off.** Record the command to run the script, the assumptions, and the known gaps (client-side computed values, third-party calls, data limits).

## Verification

A pass is a single-user run and a small concurrent run, each with content assertions that were shown able to fail, against the named environment. Not a pass: a green run with status-only checks, a run against a different environment than the one named, or a replay that "works" because a captured token is hard-coded.

## Stop conditions

- Errors at one user: fix the script before running more users.
- A value you cannot correlate (computed in the browser): stop, list it, and say what is needed (the algorithm, or a call to the endpoint the page uses).
- Test data that runs out or collides: fix the data before scaling.
- The environment or permission is not what step 1 said.

## Delegation

The lead owns correlation decisions and the final review. A worker can do capture clean-up or extra journeys, one journey each, but runs never share a target at the same time. Workers read `perf-mode/worker.md` first.

## Reply format

What the script covers, the command to run it, the validation evidence (the runs and the assertions, including the one that was shown to fail), the assumptions, and the known gaps.

## Related playbooks

`new-load-test` (this is its step 5), `sweep-mode` (the same flow run once for a user-experience check, instead of load).

## Done when

- The script passes a single-user run and a multi-user concurrent run.
- Every response that matters has a content assertion that was shown to fail.
- No dynamic value is hard-coded, and no real secret is committed.
- The handoff note lists how to run it and what it does not cover.
