---
name: principle-one-variable-at-a-time
description: Use when comparing performance before and after a change. Change one thing, keep every other condition identical, and re-measure.
---

# one-variable-at-a-time

If two things changed, you cannot say which one mattered.

- Fix the workload, data, environment, and build, then change exactly one variable.
- Re-run under identical conditions and compare medians with their spread.
- Alternate runs (A, B, A, B) so drift and warmup do not favour one side.
- If the difference is within run-to-run noise, report no measurable change and revert the change.
