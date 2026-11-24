# Reference agents for Claude Code

Three small agents that run the `sweep-mode` playbooks. They are examples to adapt, not part of the skills: the skills hold the method and work in any agent, and these files only say who runs which step and with which permissions.

| Agent | Role | Tools |
|---|---|---|
| `sweep-orchestrator` | Plans the epic, schedules captures one at a time, rolls up, drafts bugs, gets them reviewed | Agent, Read, Write, Edit, Bash, Glob, Grep |
| `sweep-worker` | One journey: flow, capture, repair, analysis | Read, Write, Edit, Bash, Glob, Grep |
| `draft-reviewer` | Read-only check of the drafts against their evidence | Read, Glob, Grep |

## Use
1. Put the hotpath checkout somewhere the agents can read, and copy these three `.md` files into your project's `.claude/agents/`.
2. Merge `settings.example.json` into your project settings, and adjust it (see below).
3. Start the orchestrator as the main session, because sub-agents cannot start other sub-agents:
   ```
   claude --agent sweep-orchestrator
   ```
   Tell it HOTPATH, the test case folder, the base URL and build, and where captures and drafts should go.

## What stays private
Put these in your own repo, not in a copy of this one: base URLs and environments, test accounts and login setup, your thresholds and severity scale, tracker conventions, and every test case, HAR, failure bundle, and bug draft.

## Enforcing "agents do not file bugs"
A tool allowlist cannot stop a worker that has `Bash` from running `gh issue create` or `curl`, so the agents' prompts say not to, and `settings.example.json` denies the obvious commands. Add deny rules for whatever your tracker's CLI or API client is (for example a Jira CLI), and do not give these agents a tracker connector. Check it works: ask a worker to run a denied command in a throwaway project and confirm it is refused.

## Permission rules and chained commands
An allowlist such as `Bash(python3:*)` matches each part of a command. If an agent chains commands (`mkdir x; python3 y | tail; cd z && git ...`), one part that is not allowed rejects the whole call, and in a non-interactive session the agent cannot ask. The agent files tell the agents to run one command per call, and the example settings allow the commands the skills use. When you add a command to a skill's steps, add it to the allowlist as well.

## Status
Run three times end to end on the demo app (the orchestrator, workers, and the reviewer, headless, with the permissions passed on the command line): about $0.94, $1.17 and $2.07, with 39, 52 and 58 orchestrator turns (the third run covered three journeys through `sweep-mode`). Every run verified all its captures, produced drafts that passed `--check`, and filed nothing. See `examples/sweep-demo/README.md` for what they found and what was fixed in between.

The reviewer's BLOCKING/NIT split and the absolute-path rule, added after the second run, worked in the third. Not tested: real test cases, SSO or MFA, an epic-sized set of journeys, interactive sessions. Codex and Copilot define agents differently; map the same three roles and the same rules onto their format and test the result.
