# Playbook: script from a test case

You own a load test script for one user journey, built from its test case and a real capture, proven to work, and delivered as a pull request. Capture, build, verify, deliver. Every claim that the script works traces to a validation run with content assertions that were shown able to fail, and nothing is committed that you have not verified.

Use when: a journey needs a load test script in any tool (JMeter, k6, Locust, Gatling, and so on) and its test case exists as a markdown file (or the user supplies HAR files), or an existing script must be rebuilt from a fresh capture.

## Inputs

- The test case `.md` file (steps and expected result), or two HARs of the journey recorded as different users.
- The tool and its version, and the repository and branch conventions of the load test project (where scripts live, naming, how the pipeline picks them up).
- The target environment for the capture and the validation, and the user's permission to drive it (see the hard rule). Validation sends a handful of users, not load.
- Two test accounts (and where their credentials are supplied, never in the repository), and data for the journey.

## Steps

1. **Confirm the inputs.** Restate goal, target, permission, tool (hard rule). Check the test case reads as a journey with an expected result, and that two accounts exist.
2. **Capture the journey twice.** If a test case exists, run `flow-from-test-case` to turn it into a flow, then `journey-capture` twice, once per account, recording response bodies. Keep the HARs out of version control: they hold real tokens. Without a test case, use the two HARs the user supplies.
3. **Group into transactions.** Name each user step from the test case (`01_open_home`, `02_login`, and so on), and drop static noise and third-party calls unless the test needs them (`script-authoring`). Use `<skills-dir>/script-authoring/scripts/har_transactions.py` for the request list per step.
4. **Author the script.** Run `script-authoring` with the tool's reference: transactions, think time and pacing from real use, headers, and a structure that is easy to read and change.
5. **Correlate.** Run `script-correlation`: `har_correlate.py` on the two HARs lists the dynamic values and where each comes from; extract each at its source, substitute it where it is used, and fail loudly if an extraction is empty.
6. **Parameterize.** Run `script-parameterization`: per-user and per-iteration data, collisions avoided, and the credentials read from the environment or a data file that is not committed.
7. **Validate.** Run `script-validation`: one user, then a few concurrent users, with content assertions that were shown able to fail. Run it against the build you captured from. To show an assertion can fail without breaking the real target, you may point a copy of the script at a local stub that returns the wrong answer; say that it was a stub, and stop it afterwards. Stop every process you started.
8. **Check for drift.** Re-run step 7 right before delivery. If the application changed since the capture and the script now fails, stop and run `repair-a-script` instead of patching blind.
9. **Review.** Run `script-review` and fix every blocker and major finding.
10. **Gate on principles.** Check `principle-validate-before-scale` and `principle-prove-the-work-happened`. If either fails, go back to step 5, 6 or 7.
11. **Deliver.** Run the `open-a-pr` playbook with the verification evidence.

## Verification

A pass is a script that, against the named environment and build, passes a single-user run and a small concurrent run, with content assertions that were shown to fail, no hard-coded dynamic value, no secret in the diff, and the validation re-run at the time of delivery. Not a pass: a green run with status-only checks, a script validated against an older build than the one captured, a replay that works only because a captured token is hard-coded, or a diff that includes a HAR.

## Stop conditions

- Errors at one user: fix the script before running more users.
- A value you cannot correlate (computed in the browser): stop, list it, and say what is needed (the algorithm, or a call to the endpoint the page uses).
- Test data that runs out or collides: fix the data before more users.
- The two captures do not follow the same sequence of requests: recapture; do not guess.
- A step that cannot be automated (MFA, CAPTCHA): report the journey as missing with the reason.
- The environment or permission is not what step 1 said.

## Delegation

The lead owns correlation decisions, validation, and the PR. A worker can capture one account's journey or build another journey's script, one journey each, but captures and validation runs never share a target at the same time. Workers read `perf-mode/worker.md` first.

## Reply format

What the script covers, the branch and PR, the validation evidence (the runs, the assertions, and the one shown to fail), the correlations and parameters it uses (names only, no values), the assumptions, and what it does not cover.

## Related playbooks

`repair-a-script` (drift), `open-a-pr` (step 11), `design-a-load-test` (the plan this script serves), `sweep-mode` (the same journey run once for a user-experience check).

## Done when

- The script passes a single-user run and a multi-user concurrent run, re-run at delivery.
- Every response that matters has a content assertion that was shown to fail.
- No dynamic value is hard-coded, and no secret or HAR is in the diff.
- A pull request exists with the evidence, and it has not been merged by you.
