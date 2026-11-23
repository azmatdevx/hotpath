---
name: jvm-gc-analysis
description: Use when a Java or JVM-based service shows latency spikes, high CPU, or memory growth under load. Covers enabling GC logs, reading pause time, allocation rate, promotion, and live-set trends, correlating pauses with latency, taking thread dumps and profiles, and tuning one change at a time.
---

# JVM and GC analysis

Goal: decide from evidence whether garbage collection, allocation, or heap sizing is limiting a JVM service, and fix the right thing.

Run this after load test results point at a JVM tier (see `results-analysis`). Do not tune the JVM first and measure afterwards (see `principle-explain-the-number`).

## When to use

- Latency has periodic spikes that line up with nothing in the application.
- CPU is high with little useful work, or heap use climbs through a test.
- Throughput stops rising while the JVM shows pauses or long GC cycles.

## Steps

### 1. Confirm the JVM is involved
Check that the slow tier is a JVM service and that the time is spent in the JVM, not waiting on a database or downstream call. Look at GC pause metrics and CPU per thread category if available.

### 2. Enable GC logging
Collect GC logs for the test window. On modern JDKs use unified logging, for example `-Xlog:gc*:file=gc.log:time,uptime,level,tags`. Older JDKs use flags such as `-XX:+PrintGCDetails -XX:+PrintGCDateStamps -Xloggc:gc.log`. Verify flags against the JDK version. Record the heap size, collector, and all JVM flags with the run.

### 3. Read the logs
Look at, over the steady-state window:
- **Pause time:** the maximum, p99, and total share of time paused.
- **Frequency:** how often young and mixed or full collections happen.
- **Allocation rate:** how fast the application allocates.
- **Promotion rate:** how fast objects move to the old generation.
- **Live set:** heap occupancy after a full or mixed collection. A live set that rises over time suggests a leak or unbounded cache.
- **Full GCs or concurrent mode failures:** these are a warning sign.
- **Humongous allocations** (G1) and metaspace growth.

### 4. Correlate with latency
Line up pause times with latency spikes and throughput dips on a shared time axis (see `observability-setup`). A pause that does not match a spike is not the cause of that spike.

### 5. Gather deeper evidence when needed
- **Thread dumps:** take several, spaced seconds apart (for example with `jcmd <pid> Thread.print`), to see blocked or busy threads.
- **CPU and allocation profile:** use a profiler or Java Flight Recorder (for example `jcmd <pid> JFR.start duration=60s filename=rec.jfr`) to find hot methods and top allocators.
- **Heap histogram:** `jcmd <pid> GC.class_histogram` shows which classes dominate the heap. Take a heap dump only when you must, because it pauses the JVM, is large, and may contain sensitive data.
- Analysis tools (GC log viewers, JDK Mission Control) are fine. Be careful about uploading logs or dumps to third-party websites, since they can expose internal details.

### 6. Fix in order of cost
1. **Reduce allocation or retention** in the application (the profile shows where). This often beats any flag.
2. **Size the heap** to the live set with headroom, and set it explicitly, including in containers (container-aware settings such as `-XX:MaxRAMPercentage`).
3. **Choose the collector** for the goal: throughput, or low pause (for example ZGC or Shenandoah on suitable JDKs). Verify support in your JDK.
4. **Tune pause targets or regions** only after the above, and one setting at a time.

### 7. Change one thing and re-measure
Apply one change, repeat the same load test, and compare pause time, throughput, and latency percentiles (see `principle-one-variable-at-a-time`). Confirm under the same conditions and for long enough to include old-generation behaviour.

### 8. Record the finding
Note the evidence (log excerpts, pause stats, profile findings), the change, and the before and after numbers.

## Pitfalls to avoid
- Copying JVM flags from the internet without measuring.
- Tuning for a short run that never reaches old-generation collections.
- Treating high GC time as the cause when the application is simply allocating too much.
- Setting the heap larger without checking the container or host memory limit.
- Taking a heap dump on a busy production instance without approval.
- Changing the collector and the heap size together.

## Done when
- GC logs, heap settings, and flags are recorded for the run.
- Pause time, allocation rate, promotion, and live set are read, and pauses are correlated with latency.
- The limiter is stated with evidence, and one change was tested with before and after numbers.
