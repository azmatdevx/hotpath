---
name: benchmark-harness
description: Use when building, fixing, or running a benchmark to measure performance. Produces a repeatable benchmark with warmup, repetitions, variance reporting, and noise control, and a baseline-vs-result comparison. Use before and after any optimization.
---

# Benchmark harness

Goal: a number you can trust, produced the same way every time, so a before/after comparison means something.

This skill is agent-neutral. It assumes only that you can read files, edit files, and run shell commands.

## When to use

- No benchmark exists for the code being optimized.
- An existing benchmark gives noisy or contradictory numbers.
- You are about to claim "X is faster" and need evidence.

Do not use for one-off timing in a REPL. Those numbers are not evidence.

## Steps

### 1. Define the workload
- State what is measured in one sentence (e.g. "p50 latency of `GET /search?q=foo` with a warm cache").
- Pick one primary metric: wall time, throughput, p50/p95/p99 latency, allocations, or peak memory.
- Use realistic input sizes and data shapes. Record the seed or fixture so the input is identical across runs.

### 2. Pick the right harness
Prefer the ecosystem's standard tool over hand-rolled loops:

| Stack | Tool |
|---|---|
| Any CLI or command | `hyperfine` |
| Python | `pytest-benchmark`, `pyperf` |
| Go | `go test -bench` + `benchstat` |
| Rust | `criterion` |
| JVM | JMH |
| JS/TS | `tinybench`, `mitata`, or Node's `perf_hooks` |
| HTTP services | `wrk`, `k6`, `oha` |
| Web pages | Lighthouse CI, WebPageTest |

If you must hand-roll a loop, keep the measured section minimal and prevent the compiler or runtime from eliminating the work (consume the result).

### 3. Control noise
- **Warmup:** discard initial iterations (JIT, caches, lazy init).
- **Repetitions:** run enough iterations that run-to-run variation is visible. At least 10 samples for a quick check, more for small effects.
- **Isolation:** close other heavy processes; on laptops, plug in power and avoid thermal throttling; pin CPU or use a quiet machine when possible.
- **Same conditions:** same machine, same build mode (release/optimized), same input, same time of day if the environment is shared.
- **Separate setup from measurement:** do not time data loading, compilation, or process startup unless that is what you are measuring.

### 4. Record a baseline
Before changing any code, run the benchmark and save:
- the raw samples (or summary: median, min, max, standard deviation or MAD)
- the exact command
- the commit hash, machine, OS, runtime/compiler version, and build flags

Save it to a file in the repo or a scratch location. Do not keep it only in chat history.

### 5. Compare after a change
- Re-run with the same command and conditions.
- Report **median** (not mean alone) and the spread for both runs.
- Use a statistical comparison when the tool offers one (`benchstat`, `hyperfine` multi-command comparison, `criterion` change report).
- Treat the difference as real only if it clearly exceeds run-to-run noise. If it does not, say "no measurable change."

### 6. Report
Use this template:

```
Workload:   <one sentence>
Command:    <exact command>
Environment:<machine, OS, runtime, build mode, commit>
Baseline:   <median> (spread <x>) over <n> runs
After:      <median> (spread <x>) over <n> runs
Change:     <delta, percent> — <real | within noise>
```

## Pitfalls to avoid
- Benchmarking a debug build.
- Timing a single run.
- Comparing numbers taken on different machines or under different load.
- Dead-code elimination: the benchmarked result is never used, so the work is skipped.
- Microbenchmarks that do not reflect real usage; confirm the hot path with a profile first (see `profile-first`).
- Reporting the best run instead of the median.
- Changing the benchmark and the code in the same step.

## Done when
- The benchmark runs with one documented command.
- A baseline is saved with its environment.
- Any claimed improvement is reported with before/after medians and spread, and is distinguishable from noise.
