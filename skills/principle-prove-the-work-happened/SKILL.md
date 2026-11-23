---
name: principle-prove-the-work-happened
description: Use when a load test or benchmark reports success. Confirm the intended work ran, not just that requests returned a success status.
---

# prove-the-work-happened

A success status is not evidence that the work happened.

- Assert on response content that depends on the work: a known element, an ID, a count, a changed value.
- Check that writes landed, that rows exist, and that the response was not a cached page, a login redirect, or an empty result.
- Check that the timed region contains the work: lazy results, unawaited calls, and discarded outputs produce numbers for work that never ran.
- Count errors and assertion failures next to every latency figure.
