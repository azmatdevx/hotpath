# Amazon CloudWatch

Not run against a real account; check the namespaces and dimensions for your services.

Export with `aws cloudwatch get-metric-data` (a read-only role, credentials from the environment) and convert the `Timestamps` and `Values` arrays to `time,value`. Standard metrics have 1 or 5 minute resolution: enable detailed monitoring or high-resolution custom metrics before the run if you need finer, and say so in the findings when you could not.

Metrics (use the `Maximum` statistic, and `p95` through `ExtendedStatistics` where noted):
- Load balancer: `AWS/ApplicationELB` `TargetResponseTime` (p95), `RequestCount`, `HTTPCode_Target_5XX_Count`, `ActiveConnectionCount`, `TargetConnectionErrorCount`
- EC2: `AWS/EC2` `CPUUtilization`, `CPUCreditBalance` for burstable types, `NetworkIn`, `NetworkOut`
- ECS and containers: `AWS/ECS` `CPUUtilization`, `MemoryUtilization`; Container Insights `CpuUtilized`, `MemoryUtilized`
- RDS: `AWS/RDS` `CPUUtilization`, `DatabaseConnections`, `ReadLatency`, `WriteLatency`, `DiskQueueDepth`, `FreeableMemory`; Performance Insights for top SQL and wait events
- Lambda: `AWS/Lambda` `Duration` (p95), `ConcurrentExecutions`, `Throttles`

Logs (CloudWatch Logs Insights) are for samples and errors, not for series; keep their output small with `stats` and `limit`.
