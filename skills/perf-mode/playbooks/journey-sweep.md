# Playbook: journey-sweep

Goal: find performance problems across a set of user journeys by running them in a browser and analysing the traffic, and log them, instead of having people walk each journey by hand and read DevTools.

Use when: you have manual test cases (markdown with steps and an expected result) and want a performance review of the whole set, such as a periodic sweep before a release.

Inputs: the test case files, the base URL of the environment, the thresholds your team uses (or say that defaults are used), and where to store captures.

## Steps

1. **Check the inputs.** Confirm the test cases are readable, the environment is the intended one and steady (no deployment or load test), and where HARs will be stored. Note the build.
2. **Turn each test case into a flow.** Run `flow-from-test-case` for each. Report the steps that cannot be automated and decide with the owner whether to capture those manually or skip. Prove each `verify` can fail.
3. **Capture.** Run `journey-capture` for each flow: at least 3 runs, cold (and warm where caching matters), one journey at a time. Do not analyse a run that did not verify. If a step fails because the page changed, run `flow-repair` between captures, then capture again from scratch; never analyse a run that was repaired or improvised.
4. **Analyse each journey.** Run `har-analysis` with `compare_runs.py` on each journey's runs. Judge every consistent finding as real, expected, or unproven, with the reason.
5. **Roll up.** Run `sweep-rollup` across the journeys. Account for any that are missing.
6. **Write the bugs.** Run `perf-bug-writing` on each ranked problem, de-duplicating against the tracker. A person reviews and files them.
7. **Report.** Give the journeys covered and missing, the cache state and build, the thresholds used, the bugs written, and what the sweep cannot say (behaviour under load, rendering time, other browsers).

Apply `principle-prove-the-work-happened` at steps 2 and 3, and `principle-explain-the-number` at step 4. See `workflows/journey-sweep-epic.md` for running this across a whole epic with several agents.

Done when: every journey is captured and analysed or reported missing, every bug traces to evidence in at least three runs, and nothing sensitive is in the bug text.
