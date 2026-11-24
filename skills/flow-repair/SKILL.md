---
name: flow-repair
description: Use when a captured browser flow failed at a step because the page changed (dynamic ids, renamed labels, moved elements, a new dialog) and needs repairing from the user step's intent. Reads the failure bundle, finds the right element by meaning, tells locator drift apart from a real defect or an outdated test case, fixes the flow minimally, and recaptures from scratch.
---

# Flow repair

Goal: get a failing flow passing again by changing how it finds things, without ever turning a real application failure into a pass, and without trusting any measurement taken while the flow was being fixed.

Repair happens between captures, never during one. A run in which something was improvised mid-run has extra latency and may have acted on the wrong element, so its HAR is discarded.

## Inputs
- The failed run's record and failure bundle from `journey-capture` (step, error, locators tried, URL, title, accessibility snapshot of the page at the failure).
- The test case file, specifically the user step that failed. Its wording is the intent to preserve.
- The flow file.

The bundle can contain text from the page. Keep it with the captures, outside version control.

If the bundle's snapshot is not enough to tell what changed, reproduce the state with `playwright-cli` (see `flow-from-test-case/references/playwright-cli.md`): open the page, replay the earlier steps, and snapshot.

## Steps

### 1. Say what the step meant
Write the failed step's intent in one sentence from the test case ("click the Refresh orders button"). The repair must satisfy that intent, not just make the error go away.

### 2. Classify the failure
Use the bundle (URL, title, accessibility snapshot) and decide which of these it is:

| Cause | Signs in the bundle | Action |
|---|---|---|
| **Locator drift** | The target is in the snapshot under a different handle (generated id, new class, new position) but the same role and name | Repair the locator (step 4) |
| **Wording or structure change** | The target exists with a different label, or a new step sits in front of it (a dialog, a consent banner, an extra page) | Repair if the change is cosmetic. If the user-visible steps changed, the test case is outdated: tell its owner and do not paper over it |
| **Timing** | The target appears if you wait; the step gave up too early | Wait for the condition (an element, a response, a URL), not a fixed sleep |
| **Real defect** | The target is missing or inert where it should work, or an error page or message is showing | Do not repair. This is a functional failure: report it, with the bundle as evidence |
| **Environment** | The page is a login, a 5xx, or a maintenance page | Fix the environment or session and recapture; the flow is not at fault |

If you cannot tell, say so and stop. A wrong repair is worse than a failed run.

### 3. Check you are on the right page
If the URL or title differs from what the step expects, an earlier step went wrong. Repairing the failing step will not help. Look at the previous step's result instead.

### 4. Make the smallest change that keeps the intent
Prefer, in order: role and accessible name, label, visible text, a test id the team controls. Never use a generated id, a generated class, or a position. Put the stable locator first. Keep a second candidate only if it is also stable. Make sure the locator matches exactly one visible element; `find` fails on ambiguity on purpose.

Do not loosen the end-state check (`verify`) or remove a step to make a run pass.

### 5. Prove the repair
- Run the flow once. It must verify.
- Confirm the repaired step acted on the element you meant. The next step's expected result and the `verify` content check are the evidence; a click that landed elsewhere should break one of them.
- If you changed `verify`, show that it still fails when the expectation is wrong (see `flow-from-test-case`).

Give each step at most two repair attempts, then stop and hand it to a person.

### 6. Write the repair down
Append to `repairs.md` next to the flow: date, flow, step, old and new locator, cause class from step 2, and the evidence (bundle file name, what the snapshot showed). A person reviews these; repairs are changes to the test, and they should not pile up unseen.

### 7. Recapture from scratch
Discard every HAR from the failed attempt and from the repair run. Capture the full set again (at least 3 runs per cache state) with `journey-capture`. A capture where a fallback locator was used still records `drifted`; treat that as a sign the primary locator needs the same repair.

## Pitfalls to avoid
- Repairing during a measured run, or analysing a HAR from a run that was repaired.
- Fixing a real defect by changing the flow until it passes.
- Choosing the first element that looks similar. Check that it is the one the step meant.
- Using generated ids, generated classes, or positions as the new locator.
- Loosening `verify` or deleting the failing step.
- Changing the flow when the test case itself is out of date.
- Repair attempts without a record.

## Done when
- The failure is classified, with the evidence.
- The repaired flow verified, and the intent of the step is preserved.
- `repairs.md` has the entry.
- The full capture was redone, with no HAR carried over from before the repair.
