# Playbook: new load test

Goal: a planned, executed, vetted, and reported load test that answers a stated question about the system.

## Steps

1. **State the question.** What decision will the result inform (release gate, capacity plan, SLA check, regression)? Record it in one sentence.
2. **Define objectives and criteria.** Run `load-test-design`: NFRs and SLAs, pass/fail thresholds, and the test types needed (load, stress, soak, spike, breakpoint).
3. **Model the workload.** Apply `principle-model-real-users`: transaction mix, peak rate, concurrency, think time, pacing, and open versus closed model, derived from production data where available.
4. **Prepare environment and data.** Record how the environment differs from production. Prepare test data large and varied enough to avoid cache distortion.
5. **Build the scripts.** Run the `script-a-flow` playbook for each journey in the mix.
6. **Pre-run checks.** Run `load-run-checklist`: environment parity, generator sizing, monitoring in place, ramp-up plan, and stop conditions.
7. **Run in steps.** Smoke test, then a ramp, then the target load. Stop and fix on early errors. Change one variable between runs (`principle-one-variable-at-a-time`).
8. **Vet the results.** Run `results-sanity-check`. Do not report anything that fails it without marking it inconclusive.
9. **Analyse and report.** Run the `results-to-report` playbook from its analysis step onward.

## Done when

- The original question is answered with a verdict (pass, fail, no measurable difference, or inconclusive).
- Every number in the report passed `results-sanity-check` or is marked with the failed check.
- The run can be repeated from the recorded command, data, and environment notes.
