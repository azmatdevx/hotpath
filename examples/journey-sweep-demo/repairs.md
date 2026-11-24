# Repairs

One entry per repair, as `flow-repair` asks. A person reviews these.

## tc-02-refresh-orders, step "Click \"Refresh orders\""
- **Failure:** the flow found the button with `#btn-1a2b3c4d`, the id seen when the flow was first written. The page generates a new id on every load, so the click timed out in 3 of 3 cold runs (`tc-02-brittle-cold-run{1,2,3}`), each writing a failure bundle.
- **Cause class:** locator drift. The bundle's snapshot showed `button "Refresh orders"` on the expected page (URL `/`, title `Shop`, orders count showing), so the element was present under a different handle.
- **Change:** replaced the id with `getByRole('button', { name: 'Refresh orders' })` as the first `find` candidate, and `getByText('Refresh orders', { exact: true })` as the second.
- **Proof:** the repaired flow verified in 3 of 3 cold and 3 of 3 warm runs, none using the fallback. The step after the click waits for "3 orders (refreshed)" and `verify` checks that text, so a click on the wrong element would have failed one of them.
- **Recapture:** the HARs of the failed attempt were discarded; the 6 runs above were captured fresh, and `compare_runs.py` refused the failed run's HAR.
- **Done by:** an agent following `flow-repair`, in a test of the skill, not on a production flow. Review it as you would any repair.
