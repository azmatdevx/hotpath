# Playbook: design a load test

You own the plan for a load test that answers a stated question, together with the scripts and the pipeline configuration that will run it. Plan, build, wire up, hand over. Your pipeline runs the load; you do not. Every threshold in the plan traces to a stated target.

Use when: a release gate, capacity plan, SLA check, or regression question needs a load test, and the test will run from your CI pipeline (for example a GitHub Actions workflow).

## Inputs

- The question the result will inform, in one sentence.
- The SLAs or targets, and the test types needed (load, stress, soak, spike, breakpoint).
- The target environment, how it differs from production, and who approves load against it (see the hard rule).
- Production traffic data for the workload model, if it exists.
- The tool and its version, the repository and pipeline where the test runs, and the load generator capacity the pipeline provides.

## Steps

1. **State the question.** What decision will the result inform? One sentence.
2. **Define objectives and criteria.** Run `load-test-design`: NFRs and SLAs, pass/fail thresholds, and the test types.
3. **Model the workload.** Apply `principle-model-real-users`: transaction mix, peak rate, concurrency, think time, pacing, and open versus closed model, from production data where available.
4. **Prepare environment and data.** Record how the environment differs from production. Prepare data large and varied enough to avoid cache distortion, and say how it is reset between runs.
5. **Build the scripts.** Run the `script-from-test-case` playbook for each journey in the mix.
6. **Wire the pipeline.** Run `ci-performance-gates`: the workflow that runs the test, its thresholds as pass/fail, how artifacts are kept (raw results, not only the summary), and the approvals the environment needs. Deliver the change with the `open-a-pr` playbook. Do not start the pipeline's load run yourself.
7. **Pre-run checks.** Run `load-run-checklist` against the plan, so the first pipeline run has the environment, data, monitoring, and stop conditions in place. For a distributed run, follow `distributed-load-generation`.
8. **Hand over.** Give the owner the plan, the thresholds and where they came from, the pipeline change, and what to look at when the first run completes (`analyse-a-test-run`).

## Verification

A pass is a plan whose question, thresholds, workload model, and environment differences are written down, scripts that passed validation, and a pipeline change that a reviewer can run. Not a pass: thresholds with no stated source, a workload model not tied to real traffic or labelled as an assumption, a script that was never validated, or a pipeline that keeps only a summary.

## Stop conditions

- The environment owner has not approved load against it for this test: stop; the pipeline must not be pointed at it.
- The thresholds or the question are missing: ask; do not invent SLAs.
- Scripts fail validation: fix them before wiring the pipeline.
- The generators in the pipeline cannot provide the load the plan needs: say so, and say what would.

## Delegation

The lead owns the plan, the thresholds, and the pipeline change. Workers can build one journey script each. Workers read `perf-mode/worker.md` first, and never start load.

## Reply format

The question, the plan in brief (workload, thresholds with sources, test types), the scripts and their validation, the pipeline change and PR, the environment differences, and what the plan cannot tell you.

## Related playbooks

`script-from-test-case` (step 5), `open-a-pr` (step 6), `analyse-a-test-run` (after the pipeline runs).

## Done when

- The plan answers the original question, with thresholds that trace to targets.
- Every script passed validation, and the pipeline change is a PR for review.
- The first run can be analysed from kept raw results.
