---
name: profile-first
description: Use before proposing or making any performance optimization. Requires a baseline measurement and a profile before changing code.
---

# Profile first

Do not propose an optimization until you have:

1. A reproducible benchmark or workload, and a baseline number (with variance).
2. A profile showing where time or memory actually goes.

Then:

- Change one thing at a time.
- Re-measure under the same conditions and report baseline vs. result.
- If the number didn't move beyond noise, revert the change.
