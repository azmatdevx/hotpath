# hotpath

Open-source skills, instructions, and workflows for performance engineering with AI coding agents.

Principle: **measure first, change one thing, measure again.**

## Layout

- `skills/` — one narrow skill per job (each has a `SKILL.md`)
- `instructions/` — `CLAUDE.md` / `AGENTS.md` templates per stack
- `workflows/` — multi-step playbooks that chain skills
- `examples/` — real before/after case studies with numbers

## Works across agents

Skills are plain markdown with minimal frontmatter (`name`, `description`) and never reference agent-specific tools. They only assume the agent can read files, edit files, and run shell commands.

## Install

Copy or symlink a skill folder into the location your agent reads skills from. Check your agent's current docs, since these paths change:

| Agent | Typical location |
|---|---|
| Claude Code | `~/.claude/skills/` or `.claude/skills/` |
| Codex | `.agents/skills/` or `~/.codex/skills/` |
| GitHub Copilot | `.github/skills/` |

```sh
ln -s "$PWD/skills/benchmark-harness" ~/.claude/skills/benchmark-harness
```

If an agent has no skills support, paste the skill body into its instructions file (`AGENTS.md`, `CLAUDE.md`, or `.github/copilot-instructions.md`).

## License

MIT
