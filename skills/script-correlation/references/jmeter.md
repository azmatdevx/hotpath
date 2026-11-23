# JMeter: correlation syntax

Add extractors as **post-processors** on the sampler that returns the value. Reference the result as `${varName}` in later samplers.

| Source | Element |
|---|---|
| JSON body | JSON Extractor, path such as `$.data.token` |
| HTML attribute / hidden field | CSS Selector Extractor, e.g. selector `input[name=csrf]`, attribute `value` |
| Header / arbitrary text | Boundary Extractor, or Regular Expression Extractor |
| XML | XPath2 Extractor |

## Tips
- Set a **Default Value** such as `TOKEN_NOT_FOUND`, then add a Response/JSON Assertion that fails when the variable holds it. This makes missing extraction visible.
- Set **Match No.** deliberately: `1` first match, `-1` all matches (creates `var_1`, `var_2`, ...), `0` random.
- Use the extractor's **scope** (main sample vs sub-samples) when the value is in a redirect or embedded resource.
- Put cookie handling in an **HTTP Cookie Manager** at the Thread Group level so each virtual user keeps its own cookies. Do not hard-code `Cookie` headers.
- Set `cookies.policy`/header handling only when the application needs it; do not copy the recorded `Cookie` header.
- Use a **Debug Sampler** plus **View Results Tree** in a single-user run to inspect variable values. Remove them (and disable heavy listeners) before the load run.
- Counter-check with a second thread: variables are per-thread, so confirm threads do not share values.
