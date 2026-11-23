---
name: principle-explain-the-number
description: Use when a performance number is about to be reported or acted on. Every number needs a named limiter and evidence, not just a value.
---

# explain-the-number

A number you cannot explain is a hypothesis.

- Name what limits the result (CPU, DB wait, pool size, GC, downstream service, the load generator) and show the evidence.
- If a change did not move the number, find the limiter before declaring the change useless.
- If two runs disagree, explain the gap before choosing one.
- State the number with its unit, percentile, run count, and range.
