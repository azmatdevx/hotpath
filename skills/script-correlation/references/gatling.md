# Gatling: correlation syntax

Extract with `check(...)` on a request and save to the session with `saveAs`. Reference the saved value with the Gatling Expression Language in later requests. In current Gatling versions the syntax is `#{name}`; older versions use `${name}`, so confirm against the version in use.

```scala
val flow = scenario("Flow")
  .exec(http("login")
    .post("/api/login")
    .body(StringBody("""{"user":"u","pass":"p"}""")).asJson
    .check(status.is(200))
    .check(jsonPath("$.data.token").saveAs("token")))
  .exec(http("form")
    .get("/form")
    .check(css("input[name=csrf]", "value").saveAs("csrf"))
    .check(regex("""nonce="([^"]+)"""").optional.saveAs("nonce")))
  .exec(http("submit")
    .post("/submit")
    .header("Authorization", "Bearer #{token}")
    .formParam("csrf", "#{csrf}")
    .check(substring("Order confirmed")))
```

## Tips
- A `check` that finds nothing fails the request, which makes missing extraction visible. Use `.optional` only when absence is expected.
- Pick the occurrence deliberately with `.find(n)`, `.findAll`, or `.findRandom`.
- Session values are per virtual user, so there is no cross-user sharing.
- Cookies are handled per virtual user by default.
- Prefer `jsonPath` and `css` over `regex`.
- Add a content check (`substring`, `jsonPath(...).is(...)`) on the response that depends on the correlated value to prove it worked.
