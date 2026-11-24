# Playbook: sweep one journey

You own one journey from its test case to analysed findings. Author, capture, measure, analyse. Every finding appears in all of at least three verified runs, and you report what you could not check.

Use when: a worker is handed one journey by an orchestrator, or someone wants a quick front-end check of one user flow.

## Inputs

- The test case file (steps and expected result), and the base URL and build of the permitted environment.
- The cache states, number of runs (at least 3), thresholds, and an output folder outside version control, all as absolute paths.
- Whether it is your turn to capture, if other journeys are being captured too.

## Steps

1. **Turn the test case into a flow.** Run `flow-from-test-case`: walk the test case with `playwright-cli` if available and build the flow with `cli_to_flow.py`, resolve every warning, list the steps that cannot be automated, and prove `verify` can fail.
2. **Wait for your turn** to capture, if the orchestrator schedules captures.
3. **Capture.** Run `journey-capture`: at least the runs you were given, for each cache state, with web vitals recorded. If a step fails, follow `repair-a-flow`, then capture again from scratch.
4. **Analyse the traffic.** Run `har-analysis` with `compare_runs.py --json` per cache state. Judge each consistent finding as real, expected, or unproven, with the reason.
5. **Analyse the vitals.** Run `web-vitals-audit` on the run records: `<skills-dir>/web-vitals-audit/scripts/vitals_summary.py --json`. Keep the ranges across runs, and say which findings come from lab conditions without throttling.
6. **Return** the summary the worker rules ask for, with paths instead of contents.

## Verification

A pass is a journey whose runs all verified, whose findings each appear in every run, and whose vitals are reported as ranges across the same runs. Not a pass: a run that stopped early, a finding from one run, a vitals number from a single run, or a result from a repaired or improvised run.

## Stop conditions

- A step cannot be automated: stop that journey and report it with the reason.
- You cannot tell drift from a real defect: stop and report; do not change the flow until it passes.
- The environment answers with errors or a maintenance page: stop and report.

## Delegation

You do this journey yourself. You do not capture before your turn, start other journeys, or file anything. Read `sweep-mode/worker.md` first.

## Reply format

The journey id and test case, conditions used, the journey JSON paths (traffic and vitals), steps that could not be automated, runs that did not verify, repairs made, runs recorded as drifted, and each consistent finding with real, expected, or unproven and the reason. Label claims measured, inferred, or guess.

## Related playbooks

`sweep-epic` (the orchestrator), `repair-a-flow`.

## Done when

- The journey is captured and analysed, or reported missing with the reason.
- Every reported finding appears in every run, with ranges.
- No HAR contents, tokens, or page text are in the reply.
