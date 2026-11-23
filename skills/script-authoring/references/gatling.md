# Gatling: authoring structure

Verify DSL names against the Gatling version and language (Scala, Java, or Kotlin) in use. The sketch below is Scala.

## Suggested structure
```scala
class CheckoutSimulation extends Simulation {
  val httpProtocol = http
    .baseUrl(sys.env.getOrElse("BASE_URL", "https://target"))
    .acceptHeader("application/json")

  val users = csv("users.csv").circular

  val scn = scenario("Checkout")
    .feed(users)
    .group("01_login") { exec(http("login").post("/login").formParam("u", "#{user}")) }
    .pause(1, 3)
    .group("02_search") { exec(http("search").get("/search").queryParam("q", "#{term}")) }

  setUp(scn.inject(rampUsers(50).during(60))).protocols(httpProtocol)
}
```

## Notes
- Use `group("name")` for steps, so reports show per-step timings.
- Keep the injection profile in `setUp(...)`, separate from the scenario.
- Read configuration with `sys.env` or system properties. Do not hard-code hosts.
- Use `.pause(min, max)` for think time.
- Share common chains (login) as `val` chains or methods and compose them in scenarios.
- The Recorder or HAR conversion can produce a starting simulation. Clean it, drop static and third-party requests, and then correlate. `inferHtmlResources` controls whether embedded resources are fetched, so set it deliberately.
