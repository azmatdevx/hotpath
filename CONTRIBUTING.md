# Contributing

Thanks for helping. A few rules keep the skills useful.

## Skill rules

- **One skill, one job.** If a skill needs "and" in its description twice, split it.
- **Method in `SKILL.md`, syntax in `references/`.** Keep the main file tool-agnostic. Put JMeter, k6, Locust, Gatling, Playwright, and other tool specifics in `references/<tool>.md`.
- **Frontmatter has two fields:** `name` (must match the folder, lowercase and hyphenated) and `description` (when to use it, under 1024 characters).
- **Structure:** when to use, steps, pitfalls, and a "done when" section.
- **No agent-specific tools.** Assume only that the agent can read files, edit files, and run shell commands.
- **Say what you verified.** Mark syntax you have not run, and name the tool version when you have.

## Safety

- Never commit HAR files, result files, tokens, credentials, or customer data. `.gitignore` covers common cases, and CI rejects `.har` and `.jtl` files.
- Examples must use public demo apps or synthetic data.

## Before opening a pull request

```sh
python3 scripts/validate-skills.py
```

This checks frontmatter, names, leftover `TODO` markers, and committed capture files.

## Case studies

Add one under `examples/<name>/` using `examples/_template/`. Real before and after numbers, with the environment and run count, are the most valuable contribution.

A playbook follows `skills/perf-mode/playbooks/_template.md`: an ownership preamble, inputs, steps, verification, stop conditions, delegation, a reply format, related playbooks, and done-when. Add it to the table in `skills/perf-mode/SKILL.md`. The validator checks the sections and that every skill a playbook names exists.

Write script paths in a skill relative to the skill folder: `<skill-dir>/scripts/x.py` for its own scripts and `<skills-dir>/<other-skill>/scripts/x.py` for a sibling's. Do not write `skills/<name>/...`; that only works from a checkout. `scripts/validate-skills.py` rejects repo-relative paths and checks that the referenced files exist, and `python3 scripts/test-install.py` runs the scripts from an installed copy.
