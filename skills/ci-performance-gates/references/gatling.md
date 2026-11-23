# Gatling: CI pass/fail

Verify names and syntax against the Gatling version and build plugin in use.

- Define assertions in `setUp(...)`. The run fails (non-zero exit) when an assertion fails:
  ```scala
  setUp(scn.inject(rampUsers(50).during(60)))
    .protocols(httpProtocol)
    .assertions(
      global.failedRequests.percent.lt(1),
      details("checkout").responseTime.percentile(95).lt(2000)
    )
  ```
- Run through the Maven or Gradle plugin, or the bundle's command line, so the exit code reaches CI.
- Publish the HTML report directory as a build artifact, and keep `simulation.log` so the report can be regenerated.
- Compare against a stored baseline with a script that reads the report's statistics JSON, since assertions are absolute.
- Keep the simulation's injection profile small enough for the stage's time budget.
