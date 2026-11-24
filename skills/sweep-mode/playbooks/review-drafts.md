# Playbook: review drafts

You own a read-only check of bug drafts against their evidence, returned as notes for the engineer. You edit nothing and file nothing. Every number you pass was matched to the data.

Use when: bug drafts from a sweep exist and need an independent check before engineers see them.

## Inputs

- The drafts folder, the rollup JSON, the journey JSON files, and the path to the skills (`<skills-dir>`), all absolute.
- If you cannot read any of these, say which and stop for that check.

## Steps

Read `<skills-dir>/perf-bug-writing/SKILL.md` for the rubric and `<skills-dir>/har-analysis/SKILL.md` for what each finding means. For each `BUG-*.md`, check and report:

1. **Numbers match the evidence.** Every figure in Seen and Evidence appears in the rollup or journey JSON, with the same ranges.
2. **Severity fits the rubric** given the Impact text. Say if it looks too high or too low and why, quoting the rubric row.
3. **Intended behaviour.** For polling, repeated calls, and redirects, say whether the evidence rules out an intended cause. If not, the draft should say it is unconfirmed.
4. **Cause as fact.** Flag any cause stated as fact that the evidence does not show.
5. **Sensitive data.** Flag tokens, session ids, personal data, or captures attached or pasted.
6. **Duplicates.** Flag two drafts that probably share one cause, and say which.
7. **Claims about load.** Flag any claim about behaviour under load; the captures are single-user.
8. **Internal wording.** Flag any mention of agents, workers, reviewers, or "I judged" in text an engineer will read.
9. **Thresholds.** Flag a draft that does not state the threshold values it relies on.

Classify each issue as BLOCKING (a number that does not match the evidence, an unsupported claim, sensitive data, a severity that contradicts the rubric row it cites, a missing threshold the claim relies on) or NIT (wording or preference that does not change what the engineer would conclude).

## Verification

A pass is one block per draft, each issue classed, with `OK` only after all nine checks. Not a pass: a verdict from memory, or an `OK` for a draft where a file could not be read.

## Stop conditions

- A file you need (the rubric, the rollup, a journey JSON) cannot be read: report `CANNOT CHECK`, name the file and the path you tried, and do not search the filesystem for it or give a verdict from memory.

## Delegation

You work alone and read-only. The orchestrator decides what to change. Read `sweep-mode/worker.md` first.

## Reply format

One block per draft:
```
BUG-NN: OK | CHANGE | CANNOT CHECK
- BLOCKING: <issue, with the line or phrase it concerns>
- NIT: <issue>
```
`CHANGE` only when at least one issue is BLOCKING. A draft with only NITs is `OK` with the nits listed.

## Related playbooks

`sweep-epic` (step 8).

## Done when

- Every draft has a block, every issue is classed, and nothing was edited.
