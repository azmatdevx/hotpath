---
name: principle-validate-before-scale
description: Use before scaling a load test up. A script must pass a single-user run and a small concurrent run before any large load is applied.
---

# validate-before-scale

Scale a script only after it is proven correct at small scale.

- Run one user and check content assertions, correlation, and data handling.
- Run a handful of concurrent users and confirm they do not share tokens or collide on data.
- Remove debug listeners and verbose logging before the large run.
- Ramp up in steps and watch for errors early. Stop the run when errors appear, because load applied to a broken script produces meaningless numbers and may harm shared environments.
