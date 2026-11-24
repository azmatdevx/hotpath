# Puppeteer: journey capture

Not tested here. Puppeteer has no built-in HAR recorder. Two usual routes:

- Record with `puppeteer-har` (a third-party package) around the same flow module shape as the Playwright script. Check its output opens in a HAR viewer and has `timings.wait` and `content.size` before trusting the analyzer on it.
- Collect `Network.*` events through a CDP session yourself and write the HAR. This is more work and easy to get subtly wrong, so prefer the package unless you need control.

Keep what matters the same as with Playwright:
- a fresh profile per cold run (`puppeteer.launch` with a new `userDataDir`), a priming pass on the same `userDataDir` for warm
- a `verify` check that throws unless the end state is reached, with a run record written beside the HAR
- HARs written outside version control

Run `node` against a known page first, open the HAR in a viewer, and run `har-analysis` on it before relying on it.
