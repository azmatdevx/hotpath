# hotpath

Skills, instructions, and workflows for performance engineering with AI coding agents.

**Principle: measure first, change one thing, measure again.**

hotpath covers the work of a performance test engineer: scripting and validating load tests, correlation, test design, frontend performance, SQL plan analysis, and results analysis. The skills are tool-agnostic. The method lives in each skill, and tool-specific syntax lives in its `references/` folder.

## Status

Early. The skills are drafts. Tool syntax in `references/` was written without running it, so verify it against the versions you use before relying on it. Issues and pull requests that correct or extend it are welcome.

## Quick start

1. Install the skills for your agent (see [Install](#install)).
2. Start a task with `perf-mode` and describe the goal and how you will know it is done:

```
perf-mode script the checkout flow for k6: record it twice, correlate the CSRF token and cart ID, and validate with 5 concurrent users.
```

`perf-mode` picks a playbook, copies its steps into a task list, runs the other skills as each step needs them, and ends with evidence.

## What is inside

### Entry point and playbooks

| Skill | For |
|---|---|
| `perf-mode` | The router. Matches a task to a playbook and runs the other skills. |
| `perf-mode/playbooks/script-a-flow` | Turn a user journey into a working, validated script. |
| `perf-mode/playbooks/new-load-test` | Plan, build, run, and report a load test end to end. |
| `perf-mode/playbooks/results-to-report` | Vet, analyse, and write up completed run results. |

### Load test scripting (tool-agnostic, with per-tool references for JMeter, k6, Locust, Gatling)

| Skill | For |
|---|---|
| `script-authoring` | Writing a script from a capture or a spec. |
| `script-correlation` | Extracting and substituting dynamic values. |
| `script-parameterization` | Per-user and per-iteration test data. |
| `script-validation` | Proving a script is correct before any load. |
| `script-review` | Reviewing a JMeter, k6, Locust, or Gatling script by severity. |
| `distributed-load-generation` | Scaling load across generators. |

### Design, execution, and analysis

| Skill | For |
|---|---|
| `load-test-design` | Objectives, SLAs, workload model, test types. |
| `load-run-checklist` | Before, during, and after a run. |
| `results-sanity-check` | Nine questions to vet a result before reporting it. |
| `results-analysis` | Percentiles, curves, errors, and finding the limiter. |
| `test-report` | Reporting a result to stakeholders. |
| `capacity-planning` | Sizing from load test evidence, with headroom and redundancy. |
| `ci-performance-gates` | Automated performance checks in CI/CD. |
| `observability-setup` | Metrics, traces, and logs ready before the run. |

### Frontend, database, and runtime

| Skill | For |
|---|---|
| `browser-script-authoring` | Browser-based flows (Playwright, k6 browser, Puppeteer). |
| `browser-script-review` | Reviewing browser scripts for flakiness and measurement integrity. |
| `web-vitals-audit` | LCP, INP, CLS, and waterfall analysis. |
| `sql-plan-analysis` | Slow queries via execution plans (Postgres, Oracle, SQL Server, MySQL). |
| `jvm-gc-analysis` | Latency, CPU, and memory problems on JVM services. |

### Foundations and principles

| Skill | For |
|---|---|
| `profile-first` | No optimization without a baseline and a profile. |
| `benchmark-harness` | Repeatable benchmarks with noise control. |
| `principle-explain-the-number` | Every number needs a named limiter and evidence. |
| `principle-prove-the-work-happened` | A success status is not proof the work ran. |
| `principle-percentiles-not-averages` | Report the distribution, per transaction. |
| `principle-validate-before-scale` | Prove the script at small scale first. |
| `principle-one-variable-at-a-time` | Change one thing between runs. |
| `principle-model-real-users` | Base the workload on real usage. |

## Layout

```
skills/<name>/SKILL.md          the skill (method, steps, pitfalls, done-when)
skills/<name>/references/       per-tool syntax and gotchas
skills/perf-mode/playbooks/     multi-step playbooks that chain skills
instructions/                   CLAUDE.md / AGENTS.md templates (planned)
workflows/                      workflow notes (planned)
examples/                       case studies with real numbers (template included); demo-shop is a local target to practice on
scripts/validate-skills.py      checks frontmatter, names, TODOs, and committed captures (run in CI)
```

## Works across agents

Skills are plain markdown with minimal frontmatter (`name`, `description`) and never reference agent-specific tools. They only assume the agent can read files, edit files, and run shell commands.

## Install

Copy or symlink skill folders into the location your agent reads skills from. Check your agent's current docs, since these paths change:

| Agent | Typical location |
|---|---|
| Claude Code | `~/.claude/skills/` or `.claude/skills/` |
| Codex | `.agents/skills/` or `~/.codex/skills/` |
| GitHub Copilot | `.github/skills/` |

```sh
for s in skills/*/; do ln -s "$PWD/$s" ~/.claude/skills/"$(basename "$s")"; done
```

If an agent has no skills support, paste the skill body into its instructions file (`AGENTS.md`, `CLAUDE.md`, or `.github/copilot-instructions.md`).

## Safety

Only run load against systems you own or have explicit permission to test, and never against production without explicit approval. Keep tokens, credentials, HAR files with real sessions, and customer data out of the repo.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Keep each skill narrow, with one job. Put the method in `SKILL.md` and tool syntax in `references/`, back claims with evidence, and run `python3 scripts/validate-skills.py` before opening a pull request.

## License

MIT
