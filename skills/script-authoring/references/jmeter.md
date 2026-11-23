# JMeter: authoring structure

Verify element names against the JMeter version in use.

## Suggested plan structure
- **Test Plan**: User Defined Variables for defaults. Read run settings with `${__P(name,default)}` so they can be set with `-Jname=value`.
- **HTTP Request Defaults**: protocol, host, port, and base path once.
- **HTTP Header Manager**: common headers.
- **HTTP Cookie Manager**: at the Thread Group level so each virtual user has its own cookies.
- **HTTP Cache Manager**: when modelling browser caching.
- **Thread Group**: one per journey, or use a plugin thread group when you need arrival-rate or stepped profiles.
- **Transaction Controller** per user step, with **Generate parent sample** checked so results report one row per step.
- **HTTP Request** samplers inside each transaction, then extractors and assertions.

## Recording
- Use the **HTTP(S) Test Script Recorder** with include and exclude patterns to drop static assets and third-party hosts, and a prefix for transaction names. Clean the recorded plan before correlating.

## Scripting and reuse
- Use **JSR223** elements with Groovy and enable "Cache compiled script if available". Avoid BeanShell for new work.
- Use **Module Controller**, **Include Controller**, or **Test Fragments** for shared steps like login.
- Keep think time in timers (for example **Uniform Random Timer**), not in scripts.

## Maintenance
- Keep the `.jmx` in version control and keep diffs small. Do not save listener output into the plan.
- Use a `setUp Thread Group` for one-time preparation and a `tearDown Thread Group` for cleanup.
