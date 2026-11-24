# Playbook: sweep an epic

You own a user-experience performance sweep across a set of journeys, run in a browser one user at a time instead of by engineers walking each journey and reading DevTools, and handed over as bug drafts. Plan, delegate, roll up, draft. Every draft traces to evidence in at least three runs of a journey that was verified to complete.

Use when: you have manual test cases (markdown with steps and an expected result), such as the stories of an epic, and want a frontend performance review of the whole set, for example before a release.

## Inputs

- The folder of test case `.md` files, and which are in scope.
- The base URL and build of the environment, and the user's permission to drive it (see the hard rule). Single-user browsing is not load, but it still needs a named, permitted target that is not being deployed to.
- The cache states to capture (cold, warm, or both), the number of runs (at least 3), and where captures and drafts go (outside version control).
- The thresholds your team uses, or an agreement that the analyzer defaults apply.

## Steps

1. **Confirm the set.** List the test cases in scope, give each a short id, and confirm the list with the user before starting.
2. **Write down the shared conditions** once, in `sweep-conditions.md` in the output folder: URL, build, cache states, runs, thresholds, folders. Check, and record the result of, each of these: the app answers a plain GET, the captures folder is outside version control, and nothing else is deploying to or driving the environment. If a check cannot be run, write that instead of skipping it.
3. **Start one worker per journey for authoring.** Each kickoff begins with "Read `<skills-dir>/sweep-mode/worker.md` before anything else", gives absolute paths, and names the `sweep-one-journey` playbook. Authoring may run in parallel.
4. **Schedule captures yourself, one journey at a time.** Tell each worker when its turn comes.
5. **Collect the returns.** A journey with no return, or whose runs did not verify, is missing, not clean. Check each worker's run records yourself.
6. **Roll up.** Run `sweep-rollup` with `--json` over the journey files, including the web-vitals rows.
7. **Draft the bugs.** Run `perf-bug-writing`: generate one draft per request or page, fill in Impact and Proposed severity written for the engineer who will log the bug (no mention of workers, agents, or reviewers), and pass `--check`. Pass the actual threshold values to `--thresholds`.
8. **Review the drafts.** Start a reviewer on the `review-drafts` playbook. Make one revision pass on the text you wrote (never the evidence, never a number), run `--check` again, review once more, and add the latest notes to each draft under "Agent review", unchanged. If it still says CHANGE, hand over with its notes; do not loop. Report what you changed and what you left.
9. **Hand over.** The output is a `bugs/` folder of drafts and an `INDEX.md`. Engineers verify each draft against the app with DevTools, log it themselves, and record the ticket id in the file.

## Verification

A pass is: every journey captured and analysed or reported missing, every run behind a finding verified to have reached its end state, every draft backed by at least three runs, `--check` passing, and the run records read by you. Not a pass: a journey that never ran counted as clean, a HAR from a repaired or improvised run, a finding from one run, or a draft that cites something the evidence does not show.

## Stop conditions

- The environment is being deployed to or load tested, or you cannot confirm it is not: stop and say so.
- Captures fail everywhere at once: the environment is likely down; stop and report.
- A step failed and nobody can tell locator drift from a real defect: stop on that journey and report.
- A journey needs a login or step that cannot be automated: report it as missing with the reason.

## Delegation

You own the conditions, the roll-up, the drafts, and the report. Workers do one journey each. Flow authoring runs in parallel; captures never run in parallel against one environment. A reviewer checks drafts read-only. You do not file anything, and neither does any agent: engineers verify and log each draft.

## Reply format

Journeys covered and missing, cache state and build, thresholds used, repairs made, runs recorded as drifted, drafts written and where, what you changed after review and what you left, and what the sweep cannot say.

## Related playbooks

`sweep-one-journey` (the worker's job), `repair-a-flow`, `review-drafts`.

## Done when

- Every journey is captured and analysed or reported missing.
- Every draft traces to evidence in at least three runs, and nothing sensitive is in the draft text.
- Nothing was filed; the engineers have the drafts folder.
- Trust-ladder record: keep a note per sweep of drafts confirmed, drafts rejected with the reason, and problems the engineers found that the sweep missed. Widen what agents do only when several sweeps support it, as a separate decision.
