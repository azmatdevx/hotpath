# perf-skills

Open-source skills, instructions, and workflows for performance engineering with AI coding agents.

Principle: **measure first, change one thing, measure again.**

## Layout

- `skills/` — one narrow skill per job (each has a `SKILL.md`)
- `instructions/` — `CLAUDE.md` / `AGENTS.md` templates per stack
- `workflows/` — multi-step playbooks that chain skills
- `examples/` — real before/after case studies with numbers

## Install

Copy or symlink a skill into your agent's skills directory, e.g.:

```sh
ln -s "$PWD/skills/profile-first" ~/.claude/skills/profile-first
```

## License

MIT
