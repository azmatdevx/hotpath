# hotpath

Skills, instructions, and workflows for performance engineering with AI coding agents.

**Principle: measure first, change one thing, measure again.**

hotpath covers the work of a performance test engineer, in two modes:

- **`sweep-mode`: user-experience checks of single user journeys in a browser.** It takes the user steps from your test cases, runs them through the app with Playwright, captures HARs and web vitals, finds duplicate requests, huge or uncompressed payloads, uncacheable assets, slow calls and poor vitals, and prepares bug drafts for engineers to verify and log. No load is generated.
- **`perf-mode`: load testing.** Scripting and validating load tests, correlation, test design, and analysing results.

The skills are tool-agnostic. The method lives in each skill, and tool-specific syntax lives in its `references/` folder.

## Status

Early. The skills are drafts. The `sweep-mode` skills and scripts were run end to end on a local demo app (Playwright 1.49, Chromium) and are covered by self-tests. The `perf-mode` skills are drafts: the k6 syntax was run against k6 v1.0.0, and the syntax for every other tool (JMeter, Locust, Gatling, Puppeteer, the SQL and JVM references) was written without running it, so verify it against the versions you use before relying on it. Issues and pull requests that correct or extend it are welcome.

For an example of the skills applied to a real run, with numbers and limits, see the [demo-shop case study](examples/demo-shop-case-study/README.md). It used a synthetic target on one shared laptop, so treat it as a worked example of the method, not as benchmark data.

## Quick start

1. Install the skills for your agent (see [Install](#install)). The first release is the `sweep-mode` pack.
2. Start a task with a mode and describe the goal and how you will know it is done:

```
sweep-mode check the journeys in ./test-cases against https://staging.example (build 1.4.2, I own it): 3 cold runs each, drafts into ./bugs.
```

```
perf-mode script the checkout flow for k6: record it twice, correlate the CSRF token and cart ID, and validate with 5 concurrent users.
```

Each mode first restates the goal, the target, the permission, and the tool, then picks a playbook, copies its steps into a task list, runs the other skills as each step needs them, and ends with evidence.

## What is inside

### Modes and playbooks

| Skill | For |
|---|---|
| `sweep-mode` | Journey sweeps: single-user, frontend checks driven by test cases. Hard rule (restate goal and target first), non-negotiables, autonomy, delegation, and reply rules. |
| `sweep-mode/playbooks/sweep-epic` | Sweep every test case of an epic with an orchestrator and one worker per journey. |
| `sweep-mode/playbooks/sweep-one-journey` | One journey: test case to flow, capture, vitals, analysis. |
| `sweep-mode/playbooks/repair-a-flow` | Repair a flow that failed because the page changed, then recapture. |
| `sweep-mode/playbooks/review-drafts` | Read-only review of bug drafts against their evidence. |
| `perf-mode` | Load testing: the same hard rule, plus rules for load, scripts, and numbers. |
| `perf-mode/playbooks/script-from-test-case` | Test case to a validated load test script, delivered as a PR. |
| `perf-mode/playbooks/repair-a-script` | Fix a script after the application changed. |
| `perf-mode/playbooks/open-a-pr` | Hand verified work to a reviewer as a PR with evidence. |
| `perf-mode/playbooks/design-a-load-test` | Plan a load test, build its scripts, and wire the pipeline that runs it. |
| `perf-mode/playbooks/analyse-a-test-run` | Vet, analyse, and write up a completed run. |

### Journey sweep (sweep-mode)

| Skill | For |
|---|---|
| `flow-from-test-case` | Turn a markdown test case into a verifiable browser flow (with a `playwright-cli` walk-through converter). |
| `journey-capture` | Run a flow in a browser: HARs and web vitals, cold and warm, repeated, verified to have completed. |
| `flow-repair` | Repair a flow after the page changed, without turning a real defect into a pass. |
| `har-analysis` | Slow APIs, duplicate calls, large or uncacheable assets, N+1 patterns, across runs. |
| `web-vitals-audit` | LCP, INP, CLS, TBT and waterfall analysis, with a vitals summary across runs. |
| `sweep-rollup` | Merge findings across journeys into one de-duplicated list. |
| `perf-bug-writing` | Turn findings into markdown bug drafts for engineers to verify and log. |
| `browser-script-authoring`, `browser-script-review` | Browser flows in Playwright, k6 browser, or Puppeteer. |

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

### Database and runtime

| Skill | For |
|---|---|
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
skills/<mode>/playbooks/        multi-step playbooks that chain skills (perf-mode, sweep-mode)
instructions/                   CLAUDE.md / AGENTS.md templates (planned)
docs/playbook-template.md       the structure every playbook follows
packs/                          lists of skills that install together (sweep-mode is the first release)
examples/                       case studies with real numbers (template included); demo-shop is a local target to practice on, with a worked case study in demo-shop-case-study
scripts/validate-skills.py      checks frontmatter, names, TODOs, script paths, and committed captures (run in CI)
scripts/test-install.py         runs the skills from an installed copy in another directory (run in CI)
```

## Works across agents

Skills are plain markdown with minimal frontmatter (`name`, `description`) and never reference agent-specific tools. They only assume the agent can read files, edit files, and run shell commands.

## Install

Nothing is required to start. The skills are folders of markdown (a few with Python or Node scripts), so there are three ways to use them:

1. **No install.** Clone the repo, open your agent in it, and tell it to follow `skills/sweep-mode/SKILL.md` (or `skills/perf-mode/SKILL.md`). This works in any agent. Nothing is discovered automatically, so you point the agent at the skill.
2. **Copy or symlink into your agent's skills folder**, so the agent lists the skills and picks them by their descriptions. This is the route to use for everyday work.
3. **Plugin or marketplace.** Not provided yet. Option 2 covers Claude Code, Cursor, Copilot and Codex.

Where each agent looks (check your agent's current docs, since these paths change and I have only tested Claude Code):

| Agent | Location |
|---|---|
| Claude Code | `~/.claude/skills/` or `<project>/.claude/skills/` |
| GitHub Copilot | `<project>/.github/skills/` (also `.claude/skills/`; `~/.copilot/skills/` for personal skills) |
| Cursor | `<project>/.cursor/skills/` (it also reads `.agents/skills/`, `.claude/skills/` and `.codex/skills/`, per third-party guides) |
| Codex | `<project>/.agents/skills/` or `~/.agents/skills/` (some lists give `.codex/skills/`) |

Several agents read `.agents/skills/` or `.claude/skills/`, so one copy can often serve more than one. **First release: the `sweep-mode` pack.** `packs/sweep-mode.txt` lists the skills a journey sweep needs, and the validator checks the pack is self-contained. Link just those:

```sh
mkdir -p ~/.claude/skills
while read s; do ln -s "$PWD/skills/$s" ~/.claude/skills/"$s"; done < packs/sweep-mode.txt
```

To install everything instead, link every folder under `skills/` (the loop above, over `skills/*/`). The `perf-mode` skills are drafts, and a playbook that names a skill you have not installed should stop and say so.

Keep the skill folders side by side. Skills name each other and their scripts relative to the folder they were loaded from, so the scripts work wherever you install them. `scripts/test-install.py` checks this from a copy in another directory. The browser capture needs the `playwright` package in the project you run it from (`npm i playwright && npx playwright install chromium`).

If an agent has no skills support, paste the skill body into its instructions file (`AGENTS.md`, `CLAUDE.md`, or `.github/copilot-instructions.md`), or use option 1.

The reference agents in `examples/agents/claude-code/` are for Claude Code only. Other agents define agents differently; see that folder's README.

## Safety

Only run load against systems you own or have explicit permission to test, and never against production without explicit approval. Keep tokens, credentials, HAR files with real sessions, and customer data out of the repo.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Keep each skill narrow, with one job. Put the method in `SKILL.md` and tool syntax in `references/`, back claims with evidence, and run `python3 scripts/validate-skills.py` before opening a pull request.

## License

MIT
