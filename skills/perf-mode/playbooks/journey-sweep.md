# Playbook: journey-sweep

You own a performance review of a set of user journeys, run in a browser instead of by hand, and handed to engineers as bug drafts. Plan, capture, analyse, draft. Every draft traces to evidence in at least three runs of a journey that was verified to complete.

Use when: you have manual test cases (markdown with steps and an expected result) and want a performance review of the whole set, such as a periodic sweep before a release.

## Inputs

- The test case files, and which are in scope.
- The base URL and build of the environment, and the user's permission to drive it (see the hard rule in `perf-mode`). Single-user browsing is not load, but it still needs a named, permitted target.
- The cache states to capture (cold, warm, or both), the number of runs (at least 3), and where captures and drafts go (outside version control).
- The thresholds your team uses, or an agreement that the analyzer defaults apply.

## Steps

1. **Check the inputs.** Confirm the test cases are readable, the environment is the intended one and steady (no deployment or load test), and where HARs will be stored. Note the build.
2. **Turn each test case into a flow.** Run `flow-from-test-case` for each. Report the steps that cannot be automated and decide with the owner whether to capture those manually or skip. Prove each `verify` can fail.
3. **Capture.** Run `journey-capture` for each flow: at least 3 runs, cold (and warm where caching matters), one journey at a time. Do not analyse a run that did not verify. If a step fails because the page changed, run `flow-repair` between captures, then capture again from scratch.
4. **Analyse each journey.** Run `har-analysis` with `compare_runs.py` on each journey's runs. Judge every consistent finding as real, expected, or unproven, with the reason.
5. **Roll up.** Run `sweep-rollup` across the journeys. Account for any that are missing.
6. **Draft the bugs.** Run `perf-bug-writing`: it generates one markdown draft per request, you fill in impact and proposed severity, and `--check` must pass. De-duplicate against the tracker. Do not file anything.
7. **Report.** Give the journeys covered and missing, the cache state and build, the thresholds used, the drafts written and where they are, and what the sweep cannot say.

Apply `principle-prove-the-work-happened` at steps 2 and 3, and `principle-explain-the-number` at step 4. See `workflows/journey-sweep-epic.md` for running this across a whole epic with several agents.

## Verification

A pass is: every journey captured and analysed (or reported missing), every run behind a finding verified to have reached its end state, every draft backed by at least three runs, and `--check` passing. Not a pass: a journey that never ran counted as clean, a HAR from a repaired or improvised run, a finding from one run, or a draft that cites something the evidence does not show.

## Stop conditions

- The environment is being deployed to, or a load test is running: stop, wait, and say so.
- A step failed and you cannot tell locator drift from a real defect: stop and report; do not change the flow until it passes.
- The login or setup cannot be automated: report the journey as missing, with the reason.
- Captures start failing everywhere at once: the environment is likely down; stop and report.

## Delegation

The lead (the orchestrator) owns the conditions, the roll-up, and the drafts. One worker per journey does the flow, capture, repair, and analysis. Flow authoring can run in parallel; captures never run in parallel against one environment. Workers read `perf-mode/worker.md` first. A reviewer can check the drafts against the evidence, read-only. The lead checks each worker's run records itself before using its result. Nothing is filed by an agent; engineers verify and log each draft.

## Reply format

Journeys covered and missing, cache state and build, thresholds used, repairs made, runs recorded as drifted, drafts written and where, and what the sweep cannot say (behaviour under load, rendering time, other browsers, anything not judged against the evidence).

## Related playbooks

`script-a-flow` (the same journeys, for load testing), `new-load-test`.

## Done when

- Every journey is captured and analysed or reported missing.
- Every draft traces to evidence in at least three runs, and nothing sensitive is in the draft text.
- Nothing was filed; the engineers have the drafts folder.
