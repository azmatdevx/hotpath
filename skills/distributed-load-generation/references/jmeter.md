# JMeter: distributed setup

Verify options against the JMeter version in use.

- **Controller and remote engines.** Start `jmeter-server` on each engine and run the plan from the controller with `-R host1,host2` (or `-r` for the configured list), headless: `jmeter -n -t plan.jmx -R host1,host2 -l results.jtl`.
- **User arithmetic.** Each engine runs the full plan, so total users = configured threads × number of engines. Reduce the thread count accordingly.
- **Data files** must exist on every engine at the path the plan uses. Split them so engines do not reuse rows.
- **Versions.** Use the same JMeter, Java version, and plugins on all machines.
- **Networking.** Remote engines communicate over RMI. Open the required ports, set the engine hostname and ports in properties, and handle the RMI SSL keystore (generate one for the cluster, or follow the documented option to disable it only on a trusted network).
- **Controller load.** Result samples flow back to the controller. If it becomes a bottleneck, use a lighter sample sender mode in properties, keep saved fields small, or run independent non-distributed instances and merge their results files afterwards.
- Keep GUI listeners off.
