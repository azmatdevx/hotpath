---
name: sweep-mode
description: Use for a user-experience performance check of user journeys in a browser, one user at a time. Takes the user steps from test cases, runs them through the app with Playwright, captures HARs and web vitals, finds duplicate requests, huge or uncompressed payloads, uncacheable assets, slow calls and poor vitals, and prepares bug drafts for engineers to verify. Not for load testing or protocol-level scripting.
---

# sweep-mode

The entry point for a journey sweep: a single-user, frontend check of how the app feels to use, driven by the user steps in your test cases. It is about user experience, not high-volume protocol testing; for load testing use the perf-mode skill, if it is installed.

This skill is agent-neutral. It assumes only that you can read files, edit files, and run shell commands. Bundled skills live at `<skills-dir>/<name>/SKILL.md` (the folder the skills were installed in); scripts named by a skill are in that skill's own `scripts/` folder, so use the path the skill was loaded from, not the current directory.

<!-- hard-rule:start -->
## Start here (hard rule)

Before any command or tool call that contacts the target (a reachability check counts), and even when the request already gives these details, write them back in a message of your own first, in this order:

1. **Goal.** The decision the result will inform, and the smallest result that answers it.
2. **Target.** The exact environment and URL (or the data source, if you are only analysing existing results), and whether it is shared or production.
3. **Permission.** Who owns it, and that the user has said this task may test it. If you do not know, ask. Do not assume.
4. **Tool and version**, and the conditions that matter (build, data set, cache state, duration).

Then wait for a correction or a go-ahead only if something in 1 to 4 is unknown or looks wrong. If all four are clear, say so and proceed.

No load, capture, script run, or measurement goes to a target until 2 and 3 are stated. A user's earlier instruction for a different task does not cover this one. Production is never a target unless the user names it for this task.
<!-- hard-rule:end -->

## Non-negotiables

Each trigger is a required action, not a suggestion. Each reply names the principles that shaped its decisions and the choice each one changed. Cite a principle only if you read its `SKILL.md` in this session.

| Trigger | Required action |
|---|---|
| A test case becomes a flow | Run `flow-from-test-case`, keep the test case's wording as the step names, and show `verify` can fail |
| You take a capture | Run `journey-capture`: at least 3 runs, cold or warm stated, every run verified to reach its end state |
| A run did not verify, or was repaired or improvised | Do not analyse it. Recapture from scratch |
| A step fails | Run `flow-repair` between captures. Never change a flow until a real defect passes |
| You state a finding | Use `har-analysis` and `compare_runs.py`: it must appear in every run, with ranges, labelled as a single-user lab measurement |
| You state a vitals result | Use `web-vitals-audit`: lab numbers, ranges across runs, conditions recorded |
| You claim a journey ran | Show the run record that says it verified (`principle-prove-the-work-happened`) |
| You state a number | Name what limits it, or say the evidence is missing (`principle-explain-the-number`) |
| A HAR, failure bundle, or capture exists | Keep it out of version control, and out of replies and bug text |
| You write a bug | Produce drafts with `perf-bug-writing`. You never file, comment on, or close a ticket |
| You start a subagent | Its kickoff begins with the line "Read `<skills-dir>/sweep-mode/worker.md` before anything else" |
| Two journeys need capturing | Capture them one at a time against an environment; analysis can run in parallel |

## Principles

Read the full skill before applying one.

- `principle-prove-the-work-happened`: a success status is not proof the work ran.
- `principle-explain-the-number`: a number without a named cause is not a finding.

## Autonomy

Proceed without asking:
- reading test cases and captures, running the analysis scripts, and writing drafts and reports in the working folder
- single-user captures (3 or more runs) against the environment the user named for this task
- repairing a flow, within `flow-repair`'s rules, and recapturing

Stop and ask first:
- a target that is not the one named, or that is being deployed to or load tested
- filing, commenting on, or closing anything in a tracker, or sending data to an outside service
- deleting captures, or committing or pushing anything
- a journey with a step you cannot automate (login, MFA, CAPTCHA): say what is needed, and report the journey as missing until it is covered

A session instruction such as "keep going until done" keeps you working through reversible steps. It does not lift the target and permission rules.

No is an acceptable answer. Say when a finding is not supported, when a draft is not ready, or when the evidence does not show what the user expected.

## Shell commands

Where your agent runs commands under an allowlist (many do, and every non-interactive run does), run one command per call. Do not chain commands with `;`, `&&`, `||`, or pipes, do not prefix a command with a variable assignment (`DIR=... mkdir ...`), and use full paths instead of `cd`: the allowlist matches each command by its first word, and one part that is not allowed rejects the whole call. If a command is denied, do not look for another way to do the same thing; report what you needed and why, and stop that step. A denied command is the operator's decision.

## Delegation

The lead (orchestrator) owns the conditions, the roll-up, and the drafts, and reads the evidence itself. One worker handles one journey.

- Flow authoring can run in parallel. Captures never run in parallel against one environment; they load each other and distort the timings.
- Give pointers to files and absolute paths, not pasted contents. Name the output folder, the thresholds, and the conditions.
- Retries and follow-ups go to a fresh worker unless the state is costly to move.
- Check each worker's run records yourself before using its result. A journey with no return, or whose runs did not verify, is missing, not clean.
- A worker never files, comments on, or closes tickets.
- Carry each worker's caveats into your own reply.

## Reply format

- Lead with the state of the sweep: journeys covered and missing.
- Label claims as **measured**, **inferred**, or **guess**.
- Give ranges across runs, with units, and the conditions: environment, build, cache state, tool and version.
- Name the drafts written and where they are, and the repairs made.
- End with what the sweep cannot say (behaviour under load, other browsers, anything not judged against the evidence).
- Never hand the human a check you could run yourself.

## Playbooks

Match the task to one playbook, copy its steps into a task list, and keep it updated. If a skill a playbook names is not installed, say so and stop that playbook; do not improvise its method. If none fits, say so, then work from the non-negotiables and the individual skills.

| Playbook | For |
|---|---|
| [sweep-epic](playbooks/sweep-epic.md) | Run a sweep over every test case in an epic with an orchestrator and one worker per journey. |
| [sweep-one-journey](playbooks/sweep-one-journey.md) | One journey from its test case to analysed findings: flow, capture, vitals, analysis. |
| [repair-a-flow](playbooks/repair-a-flow.md) | Repair a flow that failed because the page changed, and recapture from scratch. |
| [review-drafts](playbooks/review-drafts.md) | Read-only review of bug drafts against their evidence. |

Every playbook has the same sections: an ownership preamble, inputs, steps, verification, stop conditions, delegation, a reply format, related playbooks, and what done means. `docs/playbook-template.md` in the repository is the template for new ones.
