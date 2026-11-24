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

## Authoring: walk the test case once, keep the code it prints
After every action the CLI prints the Playwright code it ran. For a ref it chooses a role-and-name locator:

```
playwright-cli click e4
  -> await page.getByRole('button', { name: 'Refresh orders' }).click();
```
The page behind that example gives its button a new random id on every load (`eval "el => el.id"` returned `btn-ce27fce1`), and the printed locator does not depend on it.

For each test case step:
1. Do the step with the CLI, taking a `snapshot` first so the target is a real element, not a guess.
2. Copy the printed code into the flow step, as the first candidate of a `find([...])` call.
3. Read the printed code critically. Keep it only if it is a role and accessible name, label, text, or test id. If it printed a CSS selector, an `nth`, or a generated id, find a stabler handle in the snapshot and use that.
4. After the last step, take a snapshot and read the visible result that proves the journey ended (a count, a name, a confirmation). That becomes `verify`.

Then run the flow with `journey-capture` once, and prove `verify` can fail, as `flow-from-test-case` requires.

## Repairing: use the failure bundle first, the CLI second
The failure bundle already holds an accessibility snapshot taken at the failure. Often that is enough to find the element by meaning. If it is not, reproduce the state with the CLI: open the URL, replay the earlier steps, `snapshot`, and look at what the step needed. Then follow `flow-repair`.

## Notes
- Snapshots and logs go to `.playwright-cli/` in the working directory. They can hold page text, so this repo ignores that folder; do not commit or share it.
- The CLI's browser is separate from the capture script's browser. A step that works in the CLI still has to be proven in a capture run.
- Values in a snapshot (field contents, personal data) can end up in your notes. Do not paste them into bugs.
