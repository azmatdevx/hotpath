---
name: perf-mode
description: Use at the start of any performance testing or performance engineering task (scripting a flow, designing a load test, analysing results, and similar). Matches the request to a playbook, follows its steps, and calls the other hotpath skills and principles as each step needs them.
---

# perf-mode

The entry point for hotpath. Describe the goal and how you will know it is done. This skill picks a playbook and runs the other skills for you.

This skill is agent-neutral. It assumes only that you can read files, edit files, and run shell commands.

## How it works

1. **Match the task to a playbook** in the table below. If two fit, pick the one that covers the end goal and say which you chose.
2. **Copy the playbook's steps into a task list.** Use your agent's todo or plan tool if it has one. Otherwise keep a checklist in your reply and update it as each step finishes.
3. **Run each step.** When a step names another skill, run it with your agent's skill mechanism. If there is none, read `skills/<name>/SKILL.md` and follow it. For a tool-specific step, also read the matching file in that skill's `references/`.
4. **Apply the principles** (`principle-*`) throughout, especially `principle-prove-the-work-happened`, `principle-validate-before-scale`, and `principle-explain-the-number`.
5. **End with evidence.** Give a verdict backed by what you observed, not a summary of what you did.

If no playbook fits, say so, then work from the principles and the individual skills.

## Playbooks

| Playbook | For |
|---|---|
| [script-a-flow](playbooks/script-a-flow.md) | Turn a user journey into a working, validated load test script in any tool. |
| [new-load-test](playbooks/new-load-test.md) | Plan, build, run, and report a load test end to end. |
| [results-to-report](playbooks/results-to-report.md) | Take completed run results, vet them, analyse them, and write them up. |
| [journey-sweep](playbooks/journey-sweep.md) | Run a set of manual test cases as browser flows, capture HARs, find performance problems, and write the bugs. |

## Ground rules

- **Confirm the target and permission first.** Only run load against systems the user owns or has explicit permission to test. Never run load against production unless the user says so for this task.
- **Ask for the tool and environment** if they are not clear (JMeter, k6, Locust, Gatling, Playwright, and so on), rather than assuming one.
- **Keep secrets out of the repo.** Do not commit tokens, credentials, HAR files with real sessions, or client data.
- **Stop when the evidence says stop.** If errors appear at low load, fix the script before scaling.
