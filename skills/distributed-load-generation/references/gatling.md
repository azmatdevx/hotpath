# Gatling: distributed setup

Verify options against the Gatling edition and version in use.

- **Open-source Gatling has no built-in distribution.** Run the same simulation on several machines, then gather each machine's `simulation.log` into one folder and generate a combined report with the reports-only option of the launcher (for example `gatling.sh -ro <folder>`).
- **Injection arithmetic.** Each instance injects its own users, so divide the target load by the number of instances.
- **Enterprise or hosted editions** coordinate distributed runs and merge results for you.
- Split feeder files per instance so instances do not reuse rows.
- Use the same Gatling version, Java version, and simulation on every machine, and synchronise clocks so merged logs line up.
- Keep verbose logging off in distributed runs.
