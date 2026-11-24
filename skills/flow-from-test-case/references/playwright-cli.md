# Writing and repairing a flow with `playwright-cli`

`playwright-cli` is Microsoft's browser command line for coding agents (`npm install -g @playwright/cli@latest`, Node 20 or newer). The agent drives a real browser one command at a time and reads the page as text. Tested here with the `@playwright/cli` package against the local demo app; not tested against SSO, MFA, or large apps.

Use it to **author and repair** flows. Do not use it for the measured capture: it has no HAR recording command (tracing and a `requests` list exist, but not a HAR), so `journey-capture` stays on the scripted Playwright run.

## Commands used
```
playwright-cli open <url>          open a headless browser on the page (add --headed to watch)
playwright-cli snapshot            write the page as text with element refs (e1, e2, ...) to .playwright-cli/
playwright-cli find "<text>"       search the snapshot, with context
playwright-cli click e4            act on a ref
playwright-cli fill e5 "<text>"    type into a field
playwright-cli eval "el => el.id" e4   read an attribute that the snapshot does not show
playwright-cli requests            list the requests since load (no timings or sizes)
playwright-cli close
```
Add `-s=<name>` to keep separate browser sessions, and `open --persistent` or `--profile=<dir>` to keep a login.

## Authoring: walk the test case once, let the helper write the flow
After every action the CLI prints the Playwright code it ran. For a ref it chooses a role-and-name locator:

```
playwright-cli click e4
  -> await page.getByRole('button', { name: 'Refresh orders' }).click();
```
The page behind that example gives its button a new random id on every load (`eval "el => el.id"` returned `btn-ce27fce1`), and the printed locator does not depend on it.

`<skill-dir>/scripts/cli_to_flow.py` records that code as you go and builds the flow module from it. Use the test case's own wording for each step; the build checks it against the test case.

```
H=<skill-dir>/scripts/cli_to_flow.py   # <skill-dir>: the flow-from-test-case folder
python3 $H record walk.jsonl --step "Open the base URL" -- playwright-cli open http://localhost:3918/start
playwright-cli find "3 orders"                       # look first: prove the page is in the expected state
python3 $H record walk.jsonl --step "Wait for the orders count to appear" --wait-text "3 orders"
playwright-cli snapshot                              # get the ref of the target
python3 $H record walk.jsonl --step 'Click "Refresh orders"' -- playwright-cli click e4
python3 $H record walk.jsonl --step "Wait for the refresh to finish" --wait-text "3 orders (refreshed)"
python3 $H build walk.jsonl --id tc-02 --test-case journeys/02-refresh-orders.md \
          --expect-text "3 orders (refreshed)" --out flows/02-refresh-orders.js
```
- `record` runs the CLI command, shows its output, and keeps the printed code. It refuses commands that only look at the page (`snapshot`, `find`, `eval`, `requests`). `--wait-text` and `--wait-ms` record steps that wait.
- `build` writes the flow: the base URL is replaced by `base`, element actions go through `find` with the printed locator first, and `verify` waits for `--expect-text`.
- **Warnings** (exit code 1, the file is still written) mean a person or agent must review: an unstable locator (CSS, an id, `nth`, `first`, a role with no name), code it cannot translate, a typed value for a field that looks like a secret (replaced with `process.env.SWEEP_SECRET`), a recorded step that is not in the test case, or a test case step never recorded. Fix the walk or the flow, then build again.
- Read the generated file once. The helper cannot tell whether the wait text really proves the step finished.

Then run the flow with `journey-capture`, and prove `verify` can fail, as `flow-from-test-case` requires. Run `python3 <skill-dir>/scripts/selftest.py` to check the converter itself.

## Repairing: use the failure bundle first, the CLI second
The failure bundle already holds an accessibility snapshot taken at the failure. Often that is enough to find the element by meaning. If it is not, reproduce the state with the CLI: open the URL, replay the earlier steps, `snapshot`, and look at what the step needed. Then follow `flow-repair`.

## Notes
- `playwright-cli` writes its snapshots and logs into `.playwright-cli/` in the directory you run it from. If that is a repository, keep the folder out of your commit (and out of the diff you hand over) and delete it when you are done.
- Snapshots and logs go to `.playwright-cli/` in the working directory. They can hold page text, so this repo ignores that folder; do not commit or share it.
- The CLI's browser is separate from the capture script's browser. A step that works in the CLI still has to be proven in a capture run.
- Values in a snapshot (field contents, personal data) can end up in your notes. Do not paste them into bugs.
