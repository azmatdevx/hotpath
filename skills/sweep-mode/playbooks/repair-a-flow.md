# Playbook: repair a flow

You own getting a failing flow passing again by changing how it finds things, without turning a real application failure into a pass, and without trusting any measurement taken during the repair. Classify, repair, prove, record, recapture.

Use when: a capture run failed at a step and wrote a failure bundle, because the page changed (dynamic ids, renamed labels, a new dialog).

## Inputs

- The failed run's record and failure bundle, the test case step that failed, and the flow file.
- The environment and conditions of the capture.

## Steps

1. **Say what the step meant** in one sentence from the test case.
2. **Classify the failure** with `flow-repair`: locator drift, wording or structure change, timing, real defect, or environment. If you cannot tell, stop.
3. **Repair the smallest thing** that keeps the intent: a role-and-name or label locator first, never a generated id or position. Do not loosen `verify` or remove a step.
4. **Prove it.** Run the flow once and check the repaired step acted on the intended element (the next step's expected result and `verify` are the evidence). At most two attempts per step.
5. **Record it** in `repairs.md` next to the flow: date, flow, step, old and new locator, cause class, evidence.
6. **Recapture from scratch.** Delete the HARs from the failed attempt and the repair run, and capture the full set again with `journey-capture`.

## Verification

A pass is a flow that verifies in every run of a fresh full capture, with the repair recorded. Not a pass: a repaired step that happens to click something else, a loosened end check, or any HAR carried over from before the repair.

## Stop conditions

- The bundle shows a real defect (missing or inert target, an error page): report it as a finding; do not repair.
- The test case itself is out of date: tell its owner; do not paper over it.
- The environment is down or at a login page: fix that, not the flow.
- Two repair attempts on one step failed: stop and hand it to a person.

## Delegation

You do the repair yourself. A person reviews `repairs.md`. Read `sweep-mode/worker.md` first.

## Reply format

The step and its intent, the cause class and evidence, the change, the proof, and the recapture result.

## Related playbooks

`sweep-one-journey`, `sweep-epic`.

## Done when

- The failure is classified with evidence.
- The repaired flow verified in a fresh full capture.
- `repairs.md` has the entry, and no old HAR was kept.
