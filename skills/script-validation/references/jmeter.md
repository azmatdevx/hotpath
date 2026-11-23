# JMeter: validation commands and elements

Verify the commands and element names against the JMeter version in use.

## Single-user pass
- Set the Thread Group to 1 thread, 1 loop. Add a **View Results Tree** and a **Debug Sampler** to inspect requests, responses, and variable values. Run in the GUI for this step only.

## Assertions
- **Response Assertion** (text in body or field of the response), **JSON Assertion** (path and expected value), **XPath2 Assertion**, **Duration Assertion** (response time limit).
- Add assertions at the sampler level for step-specific checks. A Response Assertion on a parent controller applies to every child.
- When extracting values, set a default such as `TOKEN_NOT_FOUND` and assert the variable does not hold it.

## Timing
- Think time: **Uniform Random Timer** or **Gaussian Random Timer**. Pacing or rate: **Constant Throughput Timer** or **Precise Throughput Timer**.
- Avoid a **Constant Timer** with a fixed sleep for every step unless the model calls for it.

## Data
- **CSV Data Set Config**: choose the sharing mode deliberately, set recycle and stop-on-EOF behaviour, and confirm the file path resolves on the load generator.

## Concurrent pass and load run
- Remove or disable **View Results Tree**, **Debug Sampler**, and other listeners before real runs.
- Run headless: `jmeter -n -t plan.jmx -l results.jtl`
- Generate the report with `-e -o <empty-output-dir>`.
- Pass parameters with `-Jname=value` and read them with `${__P(name,default)}`.
