# Gatling script review

Verify details against the Gatling version and language (Scala, Java, or Kotlin) in use.

## What to look for

- **Checks.** Each important request has a content check (`substring`, `jsonPath`, `css`) beyond `status`.
- **No assertions on the simulation.** Without `.assertions(...)` in `setUp`, the run cannot fail in CI (see `ci-performance-gates`).
- **Think time.** `pause` missing or constant.
- **Feeder strategy.** `.queue` ends the run for new users when data runs out, while `.circular` silently reuses data. Check the choice matches the data plan.
- **Failure handling.** Flows that continue after a failed step, such as login, and produce misleading downstream errors. Consider `exitBlockOnFail` or `exitHereIfFailed`.
- **Injection profile.** Open model (`rampUsersPerSec`, `constantUsersPerSec`) versus closed model (`constantConcurrentUsers`) matches the workload design, and the profile and duration match the plan.
- **Hard-coded base URL and credentials.** Prefer `sys.env` or system properties.
- **Embedded resources.** `inferHtmlResources` set deliberately.
- **Connection settings.** `shareConnections`, `maxConnectionsPerHost`, and timeouts set to match real clients.
- **Leftover logging.** Verbose or `TRACE` logging in `logback.xml` left on from debugging.
- **Blocking code in lambdas.** Blocking calls or heavy computation inside session functions slow the engine.
- **Request naming.** Dynamic values in request names fragment the report. Use stable names and `group` for steps.
- **Warm-up requests.** Gatling can send a warm-up request to the target by default. Be aware of it when measuring and when pointing at sensitive environments.
