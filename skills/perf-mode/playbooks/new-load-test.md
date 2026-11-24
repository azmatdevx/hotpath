# Playbook: new load test

You own a load test that answers a stated question, from plan to report. Plan, run, vet, report. Every number in the report passed the sanity check or is marked with the check it failed.

Use when: a release gate, capacity plan, SLA check, or regression question needs a load test.

## Inputs

- The question the result will inform, in one sentence.
- The SLAs or targets, and the test types needed (load, stress, soak, spike, breakpoint).
- The target environment, how it differs from production, and the user's permission to load it for this test (see the hard rule in `perf-mode`).
- Production traffic data for the workload model, if it exists.
- The tool and its version, and the load generator capacity available.

## Steps

1. **State the question.** What decision will the result inform? One sentence.
2. **Define objectives and criteria.** Run `load-test-design`: NFRs and SLAs, pass/fail thresholds, and the test types.
3. **Model the workload.** Apply `principle-model-real-users`: transaction mix, peak rate, concurrency, think time, pacing, and open versus closed model, from production data where available.
4. **Prepare environment and data.** Record how the environment differs from production. Prepare data large and varied enough to avoid cache distortion.
5. **Build the scripts.** Run the `script-a-flow` playbook for each journey in the mix.
6. **Pre-run checks.** Run `load-run-checklist`: environment parity, generator sizing, monitoring, ramp plan, stop conditions, and approvals.
7. **Run in steps.** Smoke test, then a ramp, then the target load. Change one variable between runs (`principle-one-variable-at-a-time`). For a distributed run, follow `distributed-load-generation`.
8. **Vet the results.** Run `results-sanity-check`. Do not report anything that fails it without marking it inconclusive.
9. **Analyse and report.** Run the `results-to-report` playbook from its analysis step onward.

## Verification

A pass is a verdict (pass, fail, no measurable difference, or inconclusive) on the original question, with every reported number vetted. Not a pass: a result from a run with generator saturation, dropped iterations, or a drifting steady state that was not checked; a comparison where more than one thing changed; a number with no named limiter and no statement that the evidence is missing.

## Stop conditions

- Errors at low load: stop, fix the script, do not scale.
- The environment is not in the state the plan says, or something else is running in the window.
- An abort threshold from the plan is crossed (error rate, response time, a resource ceiling): stop the run, record why, and ask before continuing.
- The load generators approach saturation: the run no longer measures the system.
- Permission or the target changes during the run.

## Delegation

The lead owns the plan, the run, and the verdict. Workers can build one journey script each and run analysis. Load runs and captures never run in parallel against the same environment. Workers read `perf-mode/worker.md` first, and never start load unless the kickoff says to.

## Reply format

The verdict first, then the headline number against the SLA with its range across runs, the conditions (environment, build, data, tool, duration, load level), the limiter with evidence, the checks that failed or were not run, and what the test cannot say.

## Related playbooks

`script-a-flow` (step 5), `results-to-report` (step 9).

## Done when

- The original question is answered with a verdict.
- Every number in the report passed `results-sanity-check` or is marked with the failed check.
- The run can be repeated from the recorded command, data, and environment notes.
