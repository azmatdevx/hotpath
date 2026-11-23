# Lighthouse: web vitals audit

Verify flags against the Lighthouse version in use.

## Running
- CLI: `npx lighthouse <url> --output=json --output-path=report.json`
- Form factor: `--form-factor=mobile` (default) or `--preset=desktop`.
- Throttling: the default simulates a slower network and CPU. Record whatever you use and keep it the same.
- Lighthouse CI (`lhci autorun`) can run each URL several times (`--collect.numberOfRuns=5`) and assert on results, which suits regression checks.

## Notes
- Lighthouse is a lab tool. Results vary between runs, so use several runs and report the median.
- It reports LCP, CLS, TBT, FCP, and Speed Index. It does not measure INP in a default navigation run, because INP needs real interactions. Use TBT as a proxy, and use a user-flow (timespan) run or field data for INP.
- Use the report's opportunities and diagnostics as leads, then confirm in a trace or waterfall. The estimated savings are guides, not guarantees.
- Run on a quiet machine. Extensions, other tabs, and CPU contention change results.
