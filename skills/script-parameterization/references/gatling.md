# Gatling: parameterization

Verify names against the Gatling version and language in use. The sketch below is Scala.

## Feeders
```scala
val users   = csv("users.csv").queue          // each row once; fails when exhausted
val terms   = csv("terms.csv").random         // random pick
val reuse   = csv("products.csv").circular    // loop when reuse is harmless
val unique  = Iterator.continually(Map("email" -> s"user-${java.util.UUID.randomUUID}@example.test"))

val scn = scenario("Checkout")
  .feed(users)
  .feed(terms)
  .exec(http("search").get("/search").queryParam("q", "#{term}"))
```

## Notes
- Strategies: `.queue` (in order, once), `.circular` (loop), `.random`, `.shuffle`. Choose deliberately. `.queue` ends the run for new users when rows run out, which surfaces exhaustion.
- Use `.batch` for very large files, so they are not fully loaded into memory.
- Reference feeder fields in requests with `#{name}` (older versions use `${name}`).
- For database-driven data, use a JDBC feeder or build data before the simulation runs.
- Custom feeders can be any `Iterator[Map[String, Any]]`, which is useful for unique generated values.
- In distributed runs, each Gatling instance has its own feeder state, so split files per instance to avoid reuse.
