---
name: flow-from-test-case
description: Use when a manual test case written in markdown (preconditions, numbered steps, expected result) must become a repeatable browser flow that a capture tool can run, for example before recording HARs of a user journey. Maps each step to a named, verifiable action and an end-state check, and lists what cannot be automated.
---

# Flow from test case

Goal: turn a written test case into a flow that reaches the same end state a person would, so that a capture of it can be trusted.

This skill is tool-agnostic. It reuses `browser-script-authoring` for selectors, waits, and state, and `browser-script-review` for the review. The flow shape that `journey-capture` runs is in its `references/`. An agent can write the flow by walking the test case in the real app with `playwright-cli`; see `references/playwright-cli.md`.

`<skill-dir>` below is the folder that contains this SKILL.md (the scripts live in its `scripts/` folder), and `<skills-dir>` is its parent, where the sibling skills sit. Use the real path your agent loaded this skill from; do not assume the current directory is the hotpath checkout.

## Steps

### 1. Read the test case as a list of actions
Read the whole file first: title, preconditions, steps, expected result. Write down, for each numbered step, the one action it asks for. Keep the test case's own wording; it becomes the step name, so a finding can be traced back to the step that caused it.

Test cases vary in format. If steps are not numbered or an expected result is missing, say so and use what the file does give.

### 2. List what cannot be automated
Mark and report these instead of guessing:

- CAPTCHA, MFA codes, email or SMS links, hardware tokens
- file uploads or downloads from the local machine
- steps that depend on a person judging the screen ("the layout looks right")
- data that must exist first and no instruction says how to create it
- anything that needs a third-party page you cannot drive

A journey with an unautomatable step is either captured manually for that part or skipped and reported. Do not invent a way around it.

### 3. Handle preconditions
- **Login:** do the login once, outside the measured steps, and reuse the saved session so the capture is of the journey and not of the login. If login is part of the journey, keep it as steps.
- **Data:** use the data the test case names. If it needs data created, create it through a setup step that is not measured, and say where it came from.
- **Environment:** take the base URL from the command line, never from the flow file.

### 4. Write each step
If you can drive the app, walk the test case once with `playwright-cli` and let `<skill-dir>/scripts/cli_to_flow.py` write the flow from what you did (see `references/playwright-cli.md`), so each locator comes from the real page, not from a guess. Review every warning it gives before you use the flow.

For every action:

- Find elements by role and accessible name, label, visible text, or a test id, never by position or by an id or class that is generated. Many apps generate ids on every load, and a flow built on them fails on the next run.
- Use the `find` helper from `journey-capture` for targets that need an action. Give it the target's name from the test case and one or two stable candidates; it requires exactly one visible match and records which candidate matched.
- Wait for a condition (an element, a response, a URL), never a fixed sleep. A fixed wait is allowed only where the test case asks for settling time, and then it is its own named step.
- Do the action, then wait for the visible result that proves it happened before the next step.

### 5. Write the end-state check
Turn the expected result into a check that throws when it does not hold, and put it in the flow as `verify`. It must test content (a number, a name, a confirmation), not that the page loaded. A capture whose journey did not complete is not a capture of that journey.

### 6. Prove it can fail
Run the flow once with the expectation deliberately wrong (for example the wrong order count) and confirm `verify` fails. If it still passes, the check proves nothing; fix it.

### 7. Expect drift later
The page will change after this flow is written. When a run fails at a step, use `flow-repair`; do not fix it by hand inside a measured run.

### 8. Review
Run `browser-script-review` over the flow. Then run it three times and confirm every run verifies. A flow that passes only sometimes is flaky; fix the waits before capturing.

## Pitfalls to avoid
- Recording the login or setup in the measured HAR.
- Replacing an unautomatable step with a guess.
- Fixed sleeps standing in for waits.
- An end check that only confirms the page loaded.
- Step names that no longer match the test case, so findings cannot be traced.
- Putting credentials or tokens in the flow file.
- Generated ids or classes as locators, which break on the next page load.

## Done when
- Every automatable step is a named action using the test case's wording.
- Unautomatable steps are listed with the reason.
- `verify` checks content, and has been shown to fail when the expectation is wrong.
- The flow verified in three consecutive runs.
