# JMeter: CI pass/fail

Verify names and options against the JMeter version and plugins in use.

- Run headless: `jmeter -n -t plan.jmx -l results.jtl -e -o report/`, and publish `report/` and the results file as build artifacts.
- JMeter does not fail the build on slow responses by itself. Assertions mark individual samples as failed, which raises the error rate, but the process still exits successfully.
- Options for a pass/fail gate:
  - **Taurus (`bzt`)** wraps a JMeter plan and supports pass/fail criteria on percentiles, error rate, and throughput, and returns a non-zero exit code on failure.
  - **A build plugin** (Maven or Gradle) that runs the plan and checks results.
  - **A small script** that parses the results file, computes percentiles over the steady-state window, compares them with thresholds, and exits non-zero.
- Keep the results output lean in CI (avoid saving response bodies) to limit file size.
