# JMeter script review

A `.jmx` file is XML, so many problems can be found with a search. Verify element and property names against the JMeter version in use, and open the plan in the GUI to confirm.

## What to look for (and how)

| Concern | Look for |
|---|---|
| Listeners left on | `<ResultCollector ... enabled="true"` (View Results Tree, tables, graphs). Disable for load runs. |
| Old scripting | `BeanShell` elements. Prefer JSR223 with Groovy. |
| Uncached scripts | JSR223 elements without "Cache compiled script" enabled (a cache key set). |
| Hard-coded hosts | `HTTPSampler.domain` filled in per sampler instead of **HTTP Request Defaults** or `${__P(...)}`. |
| Hard-coded cookies | A `Cookie` header in an **HTTP Header Manager**, or no **HTTP Cookie Manager** at all. |
| No assertions | No `ResponseAssertion`, `JSONPathAssertion`, or similar on important samplers. |
| Silent extractors | Extractors with an empty default value, so a missing value is not visible. Give a marker default and assert on it. |
| No think time | No timers anywhere, or a single **Constant Timer** on every step. |
| Infinite loops | `LoopController.loops` set to forever with no duration or scheduler. |
| Missing timeouts | Connect and response timeouts left unset (infinite wait). |
| Embedded resources | "Retrieve all embedded resources" enabled unintentionally. |
| Parallel downloads | Unintended concurrent resource download settings. |
| Data sharing | **CSV Data Set Config** sharing mode, recycle, and stop-thread settings that do not match the data plan. |
| Transactions | Missing **Transaction Controller**, or one without "Generate parent sample" so results report per request. |
| Dead code | `enabled="false"` elements left in the plan. |
| Secrets | Passwords, tokens, or keys in samplers, headers, or user variables. |

## Quick searches

```sh
grep -c 'ResultCollector' plan.jmx
grep -n 'enabled="true"' plan.jmx | grep -i 'ResultCollector'
grep -n 'BeanShell' plan.jmx
grep -n 'enabled="false"' plan.jmx
grep -n 'HTTPSampler.domain' plan.jmx
grep -in 'password\|token\|secret\|apikey' plan.jmx
```

## Also check
- Results output settings (saved fields, response data). Saving response bodies bloats files and slows the generator.
- That the plan runs headless with properties (`-J`) for host, users, ramp, and duration.
- Plugin dependencies are listed, since a missing plugin breaks the plan on another machine.
