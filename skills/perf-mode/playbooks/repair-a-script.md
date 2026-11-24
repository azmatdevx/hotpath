# Playbook: repair a script

You own getting a load test script passing again after the application changed, with the smallest change the evidence justifies, without turning a real application failure into a pass. Reproduce, classify, recapture, update, prove, deliver.

Use when: a script fails validation or in the pipeline (new 401s or 403s, empty extractions, content assertion failures, unexpected redirects, "works for one user, fails for two"), and the test case still describes the journey.

## Inputs

- The failing script, the validation or pipeline output (the first failure, not only the last), and the test case.
- The target environment and build, and the user's permission to drive it (see the hard rule). Reproduction uses one user, then a few.
- Two test accounts, and the old captures if they still exist.

## Steps

1. **Reproduce at one user.** Run the script with a single user and record the first failing request and its response. Do not scale to find out more.
2. **Classify.** Decide with `script-correlation` and `script-validation`: a new or changed dynamic value, exhausted or colliding test data, a changed endpoint or contract, a changed auth flow, an environment problem, or a real defect (the application now returns errors for a correct request). If you cannot tell, stop.
3. **Recapture.** Capture the journey twice with the current build (`journey-capture`, bodies recorded, one account each). Keep the HARs out of version control.
4. **Compare.** Run `har_correlate.py` on the new pair, and compare the transaction list of the new capture against the script's transactions: requests added, removed, or reordered, and values that changed role.
5. **Update the script minimally.** Change only what the comparison shows: an extraction rule, a request, a parameter. Keep transaction names stable so results stay comparable over time, and say so if you must rename one.
6. **Prove it.** Run `script-validation`: one user, then a few, with the content assertions that were shown able to fail (make the broken copy of the script with your file-edit tool, not with `sed`, which an allowlist may reject). Confirm the change fixed the original failure, not another one.
7. **Deliver.** Run the `open-a-pr` playbook with the before and after evidence and a note of what changed in the application.

## Verification

A pass is the original failure gone, a single-user and a small concurrent run passing with content assertions, transaction names unchanged (or the rename justified), and the change explained by what differs between the old and the new capture. Not a pass: a script that works because an assertion was loosened, a request removed to avoid a failing call, or a fix tested only against one user.

## Stop conditions

- The classification is a real defect: report it as a finding with the evidence; do not repair the script around it.
- The test case is out of date: tell its owner; do not paper over it.
- The environment is down, at a login page, or being deployed to: fix that, not the script.
- Two repair attempts on one failure did not work: stop and hand it to a person.

## Delegation

You do the repair yourself. A person reviews the PR. Workers can capture an account's journey. Read `perf-mode/worker.md` first.

## Reply format

The failing request and its classification, what differs between the old and new capture (names only, no values), the change, the validation evidence, and the PR.

## Related playbooks

`script-from-test-case`, `open-a-pr`.

## Done when

- The failure is classified with evidence.
- The repaired script passes at one user and a few, with assertions that can fail.
- A pull request describes what changed in the application and in the script.
