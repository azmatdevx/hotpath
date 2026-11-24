# Workflow: journey-sweep across an epic

Use this to run the `journey-sweep` playbook over a whole set of test cases (one epic, many stories) with an orchestrating agent. The orchestrator plans and merges; one worker per journey does the capture and analysis.

This file is agent-neutral. "Worker" means a sub-agent, a separate session, or the same agent working through the list one journey at a time. If your agent has no sub-agents, run the workers yourself in sequence; nothing else changes.

## Orchestrator

1. **Collect the journeys.** List the test case files in scope, one per story. Give each a short id (for example the story key or the file name). Confirm the list with the owner before starting.
2. **Set the shared conditions** once and write them down: base URL, build, cache states to capture, thresholds, output directory outside version control, and the number of runs (at least 3).
3. **Check the environment is steady.** No deployment, no load test, and no one else driving it. Captures that overlap distort each other.
4. **Prepare flows in parallel, capture in sequence.** Flows can be written by several workers at once (`flow-from-test-case`). Captures must not run in parallel against the same environment, so the orchestrator schedules them one at a time. Analysis (`har-analysis`) can run in parallel again.
5. **Give each worker one journey** and these instructions: run `flow-from-test-case`, then `journey-capture`, then `har-analysis` for its journey only, and return the path of the journey's JSON file, the list of unautomatable steps, and any run that did not verify. A worker does not file bugs.
6. **Collect the results.** Check every journey returned either a JSON file or a reason it is missing. A journey with no return is missing, not clean.
7. **Roll up** with `sweep-rollup` (with `--json`), then run `perf-bug-writing` to generate the drafts, fill in impact and proposed severity, and pass `--check`.
8. **Hand to people, nothing is filed.** The output is a `bugs/` folder of markdown drafts and an `INDEX.md`. Engineers verify each draft against the app with DevTools, log it in the tracker themselves, and record the ticket id in the file. The agent does not file, comment on, or close tickets. This is deliberate: trust in the sweep is built by comparing its drafts with what the engineers confirm and reject, and autonomy is widened only as that record supports it.
9. **Report** using the last step of the `journey-sweep` playbook.

## Worker instructions (copy into the worker's prompt)

```
Journey: <id>, test case file: <path>
Environment: <base URL>, build <build>, cache states: <cold|warm>, runs: <n>, thresholds: <values>
Output directory: <path outside version control>

Follow skills flow-from-test-case, journey-capture, and har-analysis for this journey only.
Do not capture in parallel with other workers; wait for the orchestrator's go-ahead before step 2.
Return: the journey JSON path, unautomatable steps with reasons, runs that did not verify, repairs made (from repairs.md), runs recorded as drifted, and
for each consistent finding whether you judge it real, expected, or unproven, with the reason.
If a step fails, use skill flow-repair between captures and capture again from scratch; do not repair during a run.
Do not file bugs. Do not paste HAR contents into your reply.
```

## Climbing the trust ladder
Keep a short record per sweep: drafts produced, drafts confirmed, drafts rejected with the reason, and problems the engineers found that the sweep missed. Reasons for rejection usually point at a threshold, a classification rule, or a flow that needs changing. Do not move to a more autonomous step (for example filing drafts as tickets) until several sweeps show few rejections and no misses that matter, and when you do, make it a separate, explicit decision.

## What this does not replace
Repairs are changes to the test, so the reviewer also reads each worker's repair log and checks that a real defect was not repaired into a pass. A person still decides which findings matter for the product, signs off the severities, and covers the steps that cannot be automated. Single-user timings show relative problems, not capacity; use the load testing skills for that.
