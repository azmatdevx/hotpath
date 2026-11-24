# Playbook: <name>

<One line that states what you own, in the form "You own <outcome>. Plan, run, verify.". Then one line on the evidence standard, for example "Every number traces to raw data.">

Use when: <the situation that selects this playbook>.

## Inputs

What you need before step 1. Ask for any that is missing; do not guess. Always include the target, its permission, and the conditions (see the hard rule in `perf-mode`).

## Steps

1. **<Short verb phrase>.** What to do, which skill to run (`skill-name`), and the output of the step.
2. ...

## Verification

What counts as a pass at the end, and which steps verify it. Say what is NOT a pass (an inconclusive or wrong-target result, a status code with no content check).

## Stop conditions

When to stop and say so instead of continuing (early errors, a failed sanity check, an environment that is not what the plan says, an abort threshold).

## Delegation

What the lead keeps, what can go to workers, and what must stay sequential. Workers read `perf-mode/worker.md` first.

## Reply format

The fixed shape of the final reply, for example: verdict, headline number with range, conditions, caveats.

## Related playbooks

Other playbooks to run next or instead.

## Done when

- The checkable conditions that mean the work is finished.
