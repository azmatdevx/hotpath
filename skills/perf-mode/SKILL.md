---
name: perf-mode
description: Use at the start of any load testing or performance engineering task (scripting a flow, designing a load test, analysing results, and similar). For a single-user, frontend user-experience check of journeys, use sweep-mode instead. Restates the goal and the target environment first, applies the non-negotiable rules, matches the task to a playbook, and runs the other hotpath skills as each step needs them.
---

# perf-mode

The entry point for load testing in hotpath: building and maintaining load test scripts from test cases and real captures, designing tests that your pipeline runs, and analysing the results afterwards. It does not run the load itself; your pipeline does. For a single-user, frontend user-experience check of user journeys (duplicate requests, payload sizes, web vitals), use `sweep-mode` instead; it is a separate mode with its own playbooks. This mode makes sure the work starts from a stated goal and a confirmed target, applies the rules that cannot be skipped, picks a playbook, and ends with evidence instead of a summary of activity.

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
| You send traffic to any system (a capture, a validation run) | Confirm permission and environment (above), keep it to a handful of users, and validate at one user before more (`principle-validate-before-scale`). Run `load-run-checklist` before anything the pipeline will run at load |
| You write or change a script | Run `script-validation` with content assertions, and show the assertions can fail |
| You read run results, logs, or monitoring data | Summarise with the scripts (`summarize_results.py`, `rank_limiters.py`, `rank_statements.py`) and read the summary. Never paste raw results, series, or logs into the conversation |
| You are about to state a number | Run `results-sanity-check`, report percentiles per transaction, give ranges across runs, and name what limits it (`principle-explain-the-number`, `principle-percentiles-not-averages`) |
| You claim something worked (a status code, a green run) | Show the evidence that the work happened (`principle-prove-the-work-happened`) |
| You compare two runs or configurations | Change one thing between them (`principle-one-variable-at-a-time`) |
| You design a workload | Base it on real user behaviour (`principle-model-real-users`) |
| A HAR, capture, or result file exists | Keep it out of version control, and mask secrets before it goes anywhere. Treat a HAR with bodies as secret |
| You deliver a script or a pipeline change | Verify it first, re-run the validation at the build you deliver, then open a PR with `open-a-pr`. You never merge |
| A script that used to work fails | Reproduce at one user and classify the failure before changing anything (`repair-a-script`) |
| A run will outlast your attention or session | Write the stop conditions and artifact location before starting, and do not start it if nothing will watch them |
| You start a subagent | Its kickoff begins with the line "Read `<skills-dir>/perf-mode/worker.md` before anything else" |

## Principles

Read the full skill before applying one.

**Measurement**
- `principle-explain-the-number`: a number without a named cause is not a finding.
- `principle-percentiles-not-averages`: averages hide the tail users feel.
- `principle-prove-the-work-happened`: a success status is not proof the work ran.

**Experiment design**
- `principle-validate-before-scale`: a script that fails for one user will fail for ten thousand, more expensively.
- `principle-one-variable-at-a-time`: if two things changed, you do not know which one mattered.
- `principle-model-real-users`: load that does not resemble real use answers a different question.

## Autonomy

Proceed without asking:
- reading files, analysing results you already have, running analysis scripts, and writing drafts and reports in the working folder
- a capture or validation run (one user, then a few) against a target the user named for this task
- reversible changes to scripts and local files
- once a playbook's verification gates have passed: create a new feature branch, commit, push that branch, and open a pull request with the evidence

Stop and ask first:
- load beyond a validation run against any shared, test, or production environment, even one the user named earlier for other work; starting a pipeline's load run yourself
- starting a run that is distributed or will run for a long time
- pushing to the default or any shared branch, force-pushing, merging, or deploying
- editing the pipeline definition that runs the load, other than as the PR the user asked for
- filing, commenting on, or closing anything in a tracker, or sending data to an outside service
- deleting captures or results, or changing configuration on a shared environment

Never commit a HAR, a capture, a credential, or a result file with real data, even to a feature branch.

A session instruction such as "keep going until done" keeps you working through reversible steps. It does not lift the permission and environment rules above, and it does not allow merging.

No is an acceptable answer. Say when a test should not be run, when a result is inconclusive, or when the evidence does not support what the user hoped to hear.

## Shell commands

Where your agent runs commands under an allowlist (many do, and every non-interactive run does), run one command per call. Do not chain commands with `;`, `&&`, `||`, or pipes, do not prefix a command with a variable assignment (`DIR=... mkdir ...`), and use full paths instead of `cd`: the allowlist matches each command by its first word, and one part that is not allowed rejects the whole call. If a command is denied, do not look for another way to do the same thing; report what you needed and why, and stop that step. A denied command is the operator's decision.

## Delegation

The lead owns the result and reads the numbers itself. Workers do the independent legwork.

- Start a worker for work that is independent and bulky, such as one journey, one analysis, or one report section. Do not start one for a decision.
- Give pointers to files, not pasted contents. Name the output folder, the thresholds, and the conditions.
- Never run two captures or load runs against the same environment at the same time; they distort each other. Analysis can run in parallel.
- Retries and follow-ups go to a fresh worker unless the state is costly to move.
- Review the evidence a worker returns before relying on it: open the run records and check that the numbers it quotes appear in the data.
- A worker never files, comments on, or closes tickets, and never starts load unless its kickoff says to.
- Carry each worker's caveats into your own reply.

## Reply format

- Lead with the verdict, or the state of the work, not the activity.
- Label claims as **measured**, **inferred**, or **guess**.
- Give ranges across runs, not a single best or worst value, with units.
- State the conditions: environment, build, data, cache state, tool and version, duration.
- End with what the result cannot say.
- Never hand the human a check you could run yourself.

## Playbooks

Match the task to one playbook, copy its steps into a task list (your agent's todo tool, or a checklist in your reply), and keep it updated. If two fit, take the one that covers the end goal and say which. If a skill a playbook names is not installed, say so and stop that playbook; do not improvise its method. If none fits, say so, then work from the non-negotiables and the individual skills.

| Playbook | For |
|---|---|
| [script-from-test-case](playbooks/script-from-test-case.md) | Test case to a validated load test script (capture, transactions, correlation, parameterization) delivered as a PR. |
| [repair-a-script](playbooks/repair-a-script.md) | A script broke because the application changed: reproduce, classify, recapture, fix, and deliver. |
| [open-a-pr](playbooks/open-a-pr.md) | Hand verified work to a reviewer as a PR that carries its own evidence. |
| [design-a-load-test](playbooks/design-a-load-test.md) | Plan a load test, build its scripts, and wire the pipeline that runs it. |
| [analyse-a-test-run](playbooks/analyse-a-test-run.md) | Vet, analyse, and write up a completed run, naming the limiter from monitoring data. |
| [analyse-slow-sql](playbooks/analyse-slow-sql.md) | Find the SQL statements that cost the most during a run, read their plans, and verify changes. |

Every playbook has the same sections: an ownership preamble, inputs, steps, verification, stop conditions, delegation, a reply format, related playbooks, and what done means. `docs/playbook-template.md` in the repository is the template for new ones.
