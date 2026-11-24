# hotpath

Skills, instructions, and workflows for performance engineering with AI coding agents.

**Principle: measure first, change one thing, measure again.**

hotpath covers the work of a performance test engineer: scripting and validating load tests, correlation, test design, frontend performance, SQL plan analysis, and results analysis. The skills are tool-agnostic. The method lives in each skill, and tool-specific syntax lives in its `references/` folder.

## Status

Early. The skills are drafts. The k6 scripting syntax in `references/` was run against k6 v1.0.0. The syntax for every other tool (JMeter, Locust, Gatling, Playwright, Puppeteer, the SQL and JVM references) was written without running it, so verify it against the versions you use before relying on it. Issues and pull requests that correct or extend it are welcome.

For an example of the skills applied to a real run, with numbers and limits, see the [demo-shop case study](examples/demo-shop-case-study/README.md). It used a synthetic target on one shared laptop, so treat it as a worked example of the method, not as benchmark data.

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
| `perf-mode` | The router. Restates the goal and target first (hard rule), applies the non-negotiables, autonomy, delegation, and reply rules, then matches a task to a playbook. |
| `perf-mode/playbooks/script-a-flow` | Turn a user journey into a working, validated script. |
| `perf-mode/playbooks/new-load-test` | Plan, build, run, and report a load test end to end. |
| `perf-mode/playbooks/results-to-report` | Vet, analyse, and write up completed run results. |
| `perf-mode/playbooks/journey-sweep` | Run manual test cases as browser flows, capture HARs, find performance problems, and write the bugs. |

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
| `har-analysis` | Find slow APIs, duplicate calls, large or uncacheable assets, and N+1 patterns in a HAR, with a stdlib analyzer script. |
| `perf-bug-writing` | Turn confirmed findings into reproducible, de-duplicated bug reports with a severity rubric. |
| `flow-from-test-case` | Turn a markdown test case into a named, verifiable browser flow (with a `playwright-cli` walk-through converter), and list the steps that cannot be automated. |
| `journey-capture` | Run a flow in a browser and record HARs (cold and warm, repeated, verified to have completed). |
| `flow-repair` | Repair a flow that failed because the page changed, from the step's intent, without turning a real defect into a pass. |
| `sweep-rollup` | Merge findings across journeys into one de-duplicated list of problems. |
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
workflows/                      running skills at scale (journey-sweep across an epic)
examples/                       case studies with real numbers (template included); demo-shop is a local target to practice on, with a worked case study in demo-shop-case-study
scripts/validate-skills.py      checks frontmatter, names, TODOs, script paths, and committed captures (run in CI)
scripts/test-install.py         runs the skills from an installed copy in another directory (run in CI)
```

## Works across agents

Skills are plain markdown with minimal frontmatter (`name`, `description`) and never reference agent-specific tools. They only assume the agent can read files, edit files, and run shell commands.

## Install

Nothing is required to start. The skills are folders of markdown (a few with Python or Node scripts), so there are three ways to use them:

1. **No install.** Clone the repo, open your agent in it, and tell it to follow `skills/perf-mode/SKILL.md`. This works in any agent. Nothing is discovered automatically, so you point the agent at the skill.
2. **Copy or symlink into your agent's skills folder**, so the agent lists the skills and picks them by their descriptions. This is the route to use for everyday work.
3. **Plugin or marketplace.** Not provided yet. Option 2 covers Claude Code, Cursor, Copilot and Codex.

Where each agent looks (check your agent's current docs, since these paths change and I have only tested Claude Code):

| Agent | Location |
|---|---|
| Claude Code | `~/.claude/skills/` or `<project>/.claude/skills/` |
| GitHub Copilot | `<project>/.github/skills/` (also `.claude/skills/`; `~/.copilot/skills/` for personal skills) |
| Cursor | `<project>/.cursor/skills/` (it also reads `.agents/skills/`, `.claude/skills/` and `.codex/skills/`, per third-party guides) |
| Codex | `<project>/.agents/skills/` or `~/.agents/skills/` (some lists give `.codex/skills/`) |

Several agents read `.agents/skills/` or `.claude/skills/`, so one copy can often serve more than one. Link every skill folder into the location you chose, for example:

```sh
mkdir -p ~/.claude/skills
for s in skills/*/; do ln -s "$PWD/$s" ~/.claude/skills/"$(basename "$s")"; done
```

Keep the skill folders side by side. Skills name each other and their scripts relative to the folder they were loaded from, so the scripts work wherever you install them. `scripts/test-install.py` checks this from a copy in another directory. The browser capture needs the `playwright` package in the project you run it from (`npm i playwright && npx playwright install chromium`).

If an agent has no skills support, paste the skill body into its instructions file (`AGENTS.md`, `CLAUDE.md`, or `.github/copilot-instructions.md`), or use option 1.

The reference agents in `examples/agents/claude-code/` are for Claude Code only. Other agents define agents differently; see that folder's README.

## Safety

Only run load against systems you own or have explicit permission to test, and never against production without explicit approval. Keep tokens, credentials, HAR files with real sessions, and customer data out of the repo.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Keep each skill narrow, with one job. Put the method in `SKILL.md` and tool syntax in `references/`, back claims with evidence, and run `python3 scripts/validate-skills.py` before opening a pull request.

## License

MIT
